#!/usr/bin/python3

""" Primary Backup Logic"""
import json
import sys
import time
import datetime
import logging
import argparse
import subprocess

from datetime import date
from settings import settings
from googleapiclient import discovery
from kubernetes_client import k8s_control
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from json.decoder import JSONDecodeError as JsonError

SNAPSHOT_DATESTRING_LEN = 10
DEFAULT_LOG_UPDATE_TIME = 10

logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s')
backup_logger = logging.getLogger("backup")
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

def list_disks(compute, project, zone):
	""" Lists all persistent disks used by project """
	backup_logger.debug("Finding all disks for specified project")
	all_disks = []
	try:
		result = compute.disks().list(project=project, zone=zone).execute()
		all_disks.extend(result['items'])

		while 'nextPageToken' in result:
			result = compute.disks().list(project=project, zone=zone, \
				pageToken=result['nextPageToken']).execute()
			all_disks.extend(result['items'])
	except HttpError:
		backup_logger.error("Error with HTTP request made to list_disks")
		sys.exit(1)

	return all_disks


def list_snapshots(compute, project):
	""" Lists all snapshots created for this project """
	backup_logger.debug("Finding all snapshots for specified project")
	all_snapshots = []
	try:
		result = compute.snapshots().list(project=project).execute()
		all_snapshots.extend(result['items'])

		while 'nextPageToken' in result:
			result = compute.snapshots().list(project=project, \
				pageToken=result['nextPageToken']).execute()
			all_snapshots.extend(result['items'])
	except HttpError:
		backup_logger.error("Error with HTTP request made to list_snapshots")
		sys.exit(1)

	return all_snapshots


def filter_disks_by_name(disks, names):
	""" Takes in NAMES, a predefined list of disks to snapshot, and filters 
	disks to only returns those that are in NAMES """
	backup_logger.debug("Filtering disks to match the given list of PV names")
	filtered_disks = []
	for disk in disks:
		try:
			if disk['name'] in names:
				filtered_disks.append(disk)
		except KeyError:
			backup_logger.error("Improperly formatted disks -- is your information correct?")
			sys.exit(1)
	return filtered_disks


def filter_snapshots_by_time(snapshots, retention_period):
	""" Takes in RETENTION_PERIOD, a number of days, and filters
	disks to return only those that are older than the retention_period
	and should be deleted """
	backup_logger.debug("Filtering snapshots that are older than %d days", retention_period)
	try:
		old_snapshots = list(filter(lambda snapshot: \
			__days_between_now_and_last_backup(snapshot['creationTimestamp'][:SNAPSHOT_DATESTRING_LEN]) > \
				retention_period, snapshots))
	except (TypeError, KeyError):
		backup_logger.error("Attempted to filter invalid snapshots")
		sys.exit(1)
	return old_snapshots


def filter_snapshots_by_id(snapshots, snapshot_ids):
	""" Takes in SNAPSHOT_IDS, a list of IDs corresponding to disks 
	of which snapshots have been made, and filters SNAPSHOTS until
	only those with corresponding IDs remain """
	try:
		snapshots_by_ids = list(filter(lambda snapshot: \
			snapshot['sourceDiskId'] in snapshot_ids, snapshots))
	except Exception:
		backup_logger.error("Failed to filter snapshots by snapshot_ids")
		sys.exit(1)
	return snapshots_by_ids


def create_snapshot_of_disk(compute, disk_name, project, zone, body):
	""" Creates a snapshot of the provided disk """
	backup_logger.debug("Creating snapshot for disk %s", disk_name)
	try:
		result = compute.disks().createSnapshot(disk=disk_name, project=project, zone=zone, body=body).execute()
	except HttpError:
		backup_logger.error("Error with HTTP Request made to create disk snapshot")
		sys.exit(1)
	return result


def create_disk_from_snapshot(compute, new_disk_name, snapshot_url, project, zone):
	""" Creates a new disk with NEW_DISK_NAME from the supplied SNAPSHOT_URL """
	request_body = {
		"kind" : "compute#disk",
		"name" : new_disk_name,
		"sourceSnapshot" : snapshot_url
	}
	try:
		backup_logger.debug("Creating new disk with name %s from snapshot url %s", new_disk_name, snapshot_url)
		result = compute.disks().insert(project=project, zone=zone, body=request_body).execute()
	except HttpError:
		backup_logger.error("Error with HTTP Request made to create disk from snapshot")
		sys.exit(1)
	return result


def delete_snapshot(compute, project, snapshot_name):
	""" Deletes a snapshot given its name """
	backup_logger.debug("Deleting snapshot %s", snapshot_name)
	try:
		result = compute.snapshots().delete(project=project, snapshot=snapshot_name).execute()
	except HttpError:
		backup_logger.error("Error with HTTP Request made to delete snapshot")
		sys.exit(1)
	return result


def replace_pv_with_snapshot_disk(pv_name, disk_name):
	""" Takes in PV_NAME and replaces the underlying GCE Persistent disk
	with the specified snapshot disk name"""
	backup_logger.debug("Replacing pv: %s disk with new disk %s" % (pv_name, disk_name))
	cmd = ['kubectl', 'patch', 'pv', pv_name, '-p', \
		'{"spec":{"gcePersistentDisk":{"pdName":"%s"}}}"' % disk_name]
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	output, err = p.communicate()
	if err:
		backup_logger.error("Could not patch PV %s with new GCE disk %s" % (pv_name, disk_name))
		sys.exit(1)
	return output, err


def __days_between_now_and_last_backup(date_string):
	""" Takes in DATE_STRING, formed like %Y-%M-%D such
	as 2017-03-04 and returns how many days there are between
	the current date, and that represented by DATE_STRING """
	today = datetime.datetime.now()
	d1 = date(today.year, today.month, today.day)
	snapshot_year, snapshot_month, snapshot_day = \
				[int(num) for num in date_string.split('-')]
	d2 = date(snapshot_year, snapshot_month, snapshot_day)
	delta = d1 - d2
	return delta.days


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"-c", "--cluster", help="Specify the cluster for which this script is to run on", required=True)
	parser.add_argument(
		"-b", "--backup", help="Specify a namespace to backup within the designated cluster")
	parser.add_argument(
		"-n" "--create-disk", help="Automatically creates disks from recently created snapshots", action="store_true")
	parser.add_argument(
		"-d", "--delete", help="Specify the lifespan of a snapshot (in days) before eligible for deletion")
	parser.add_argument(
		"-r", "--replace", help="Specify the persistent volume name and the new GCE PD disk to insert", nargs=2)
	parser.add_argument(
		"-v" "--verbose", help="Show verbose output (debug)", action="store_true")
	parser.add_argument(
		"-t", "--test", help="Runs script in test mode; no real actions will be taken on your cluster", action="store_true")
	args = parser.parse_args()
	backup_logger.setLevel(logging.INFO)

	# Instantiate objects, credentials, and clients
	if args.verbose:
		backup_logger.setLevel(logging.DEBUG)
	else:
		backup_logger.setLevel(logging.INFO)

	options = settings()
	k8s = k8s_control(args.cluster)
	credentials = GoogleCredentials.get_application_default()
	compute = discovery.build('compute', 'v1', credentials=credentials)

	# Filter and retrieve necessary items from Google Cloud
	all_disks = list_disks(compute, options.project_id, options.project_zone)
	all_snapshots = list_snapshots(compute, options.project_id)

	# If specified, create snapshots of all eligible disks
	if args.backup:
		filtered_disks = filter_disks_by_name(all_disks, k8s.get_filtered_disk_names(args.backup))
		backup_logger.info("Filtered %d disks out of %d total that are eligible for snapshotting",
							len(filtered_disks), len(all_disks))

		snapshot_ids = []
		completed_snapshots = 0
		start_time = time.time()
		previous_log_time = time.time()

		for disk in filtered_disks:
			request_body = {
				"kind" : "compute#snapshot",
				"name" : disk['name'],
				"id"   : disk['id']
			}
			curr_iteration_time = time.time()
			if curr_iteration_time - previous_log_time > DEFAULT_LOG_UPDATE_TIME:
				previous_log_time = curr_iteration_time
				backup_logger.info("%f seconds elapsed with %d out of %d disks successfully snapshotted", \
						curr_iteration_time - start_time, completed_snapshots, len(filtered_disks))

			if not args.test:
				result = create_snapshot_of_disk(compute, disk['name'], options.project_id, options.project_zone, request_body)
				completed_snapshots += 1
				snapshot_ids.append(result['targetId'])

		if args.create_disk:
			backup_logger.info("Refreshing list of snapshots to create new disks")
			all_snapshots = list_snapshots(compute, options.project_id)
			filtered_snapshots_by_id = filter_snapshots_by_id(all_snapshots, snapshot_ids)
			backup_logger.info("Creating disks from %d new snapshots", len(filtered_snapshots_by_id))
			today = datetime.datetimenow()
			today_as_str = str(date(today.year, today.month, today.day))

			completed_disks = 0
			start_time = time.time()
			previous_log_time = time.time()

			for snapshot in filtered_snapshots_by_id:
				curr_iteration_time = time.time()
				if curr_iteration_time - previous_log_time > DEFAULT_LOG_UPDATE_TIME:
					previous_log_time = curr_iteration_time
					backup_logger.info("%f seconds elapsed with %d out of %d disks created from snapshots", \
							curr_iteration_time - start_time, completed_disks, len(filtered_snapshots_by_id))
				new_disk_name = snapshot['sourceDisk'].split('/')[-1] + '-' + \
					today_as_str + '-snapshot'

				if not args.test:
					create_disk_from_snapshot(compute, new_disk_name, snapshot['selfLink'], options.project_id, options.project_zone)
					completed_disks += 1

	# Delete all snapshots older than the specified number of days
	if args.delete:
		snapshots_to_delete = filter_snapshots_by_time(all_snapshots, int(args.delete))
		backup_logger.info("Filtered %d snapshots out of %d total that are eligible for deletion",
						len(snapshots_to_delete), len(all_snapshots))

		completed_snapshot_deletions = 0
		start_time = time.time()
		previous_log_time = time.time() 

		for snapshot in snapshots_to_delete:
			current_iteration_time = time.time()
			if current_iteration_time - previous_log_time > DEFAULT_LOG_UPDATE_TIME:
				previous_log_time = current_iteration_time
				backup_logger.info("%f seconds elapsed with %d out of %d snapshots successfully deleted", \
						curr_iteration_time - start_time, completed_snapshot_deletions, len(snapshots_to_delete))

			if not args.test:
				delete_snapshot(compute, options.project_id, snapshot['name'])
				completed_snapshot_deletions += 1

	# Replace a pre-existing PV's underlying GCE disk with a new one
	if args.replace:
		pv_name, new_disk_name = args.replace
		backup_logger.info("Replacing %s persistent volume with new disk %s", pv_name, new_disk_name)
		if not args.test:
			replace_pv_with_snapshot_disk(pv_name, new_disk_name)

	backup_logger.info("Autobackup successful with supplied parameters")

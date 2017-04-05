#!/usr/bin/python3

""" Primary Backup Logic"""
import json
import sys
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

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s')
backup_logger = logging.getLogger("backup")
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

def list_disks(compute, project, zone):
    """ Lists all persistent disks used by project """
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


def list_instances(compute, project, zone):
    """ Lists all the instances created for this project """
    all_instances = []
    try:
        result = compute.instances().list(project=project, zone=zone).execute()
        all_instances.extend(result['items'])

        while 'nextPageToken' in result:
            result = compute.instances().list(project=project, \
                zone=zone, pageToken=result['nextPageToken']).execute()
            all_instances.extend(result['items'])
    except HttpError:
        backup_logger.error("Error with HTTP request made to list_instances")
        sys.exit(1)
    return all_instances


def filter_disks_by_name(disks, names):
    """ Takes in NAMES, a predefined list of disks to snapshot, and filters 
    disks to only returns those that are in NAMES """
    filtered_disks = []
    backup_logger.info("Filtering disks to match the given list of PV names")
    for disk in disks:
        try:
            if disk['name'] in names:
                filtered_disks.append(disk)
        except KeyError:
            backup_logger.error("Improperly formatted disks -- is your information correct?")
            sys.exit(1)
    return filtered_disks


def filter_disks_by_namespace(disks, namespace, namespace_dict_key):
    """ Takes in NAMESPACE, a predefined string value, and filters
    disks to only return those belong to NAMESPACE """
    filtered_disks = []
    backup_logger.info("Filtering disks belong to namespace: %s", namespace)
    for disk in disks:
        try:
            disk_namespace = json.loads(disk['description'])[namespace_dict_key]
            if disk_namespace == namespace:
                filtered_disks.append(disk)
        except (JsonError, KeyError):
            continue
    return filtered_disks


def filter_snapshots_by_time(snapshots, retention_period):
    """ Takes in RETENTION_PERIOD, a number of days, and filters
    disks to return only those that are older than the retention_period
    and should be deleted """
    try:
        backup_logger.info("Filtering snapshots that are older than %d days", retention_period)
        old_snapshots = list(filter(lambda snapshot: \
            __days_between_now_and_last_backup(snapshot['creationTimestamp'][:SNAPSHOT_DATESTRING_LEN]) > \
                retention_period, snapshots))
    except (TypeError, KeyError):
        backup_logger.error("Attempted to filter invalid snapshots")
        sys.exit(1)
    return old_snapshots


def create_snapshot_of_disk(compute, disk_name, project, zone, body):
    """ Creates a snapshot of the provided disk """
    backup_logger.info("Creating snapshot for disk %s", disk_name)
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
		result = compute.disks().insert(project=project, zone=zone, body=request_body).execute()
	except HttpError:
		backup_logger.error("Error with HTTP Request made to create disk from snapshot")
		sys.exit(1)
	return result


def delete_disk(compute, project, zone, disk_name):
    """ Deletes the disk specified with DISK_NAME """
    backup_logger.info("Deleting disk %s", disk_name)
    try:
        result = compute.disks().delete(disk=disk_name, project=project, zone=zone).execute()
    except HttpError:
        backup_logger.error("Error with HTTP Request made to delete disk")
        sys.exit(1)
    return result


def delete_snapshot(compute, project, snapshot_name):
    """ Deletes a snapshot given its name """
    backup_logger.info("Deleting snapshot %s", snapshot_name)
    try:
        result = compute.snapshots().delete(project=project, snapshot=snapshot_name).execute()
    except HttpError:
        backup_logger.error("Error with HTTP Request made to delete snapshot")
        sys.exit(1)
    return result


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


def replace_pv_with_snapshot_disk(pv_name, disk_name):
    """ Takes in PV_NAME and replaces the underlying GCE Persistent disk
    with the specified snapshot disk name"""
    cmd = ['kubectl', 'patch', 'pv', pv_name, '-p', \
        '{"spec":{"gcePersistentDisk":{"pdName":"%s"}}}"' % disk_name]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, err = p.communicate()
    if err:
        backup_logger.error("Could not patch PV %s with new GCE disk %s" % (pv_name, disk_name))
        sys.exit(1)
    return output, err


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--cluster", required=True, help="The cluster of nodes for which this script is to run")
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Perform backup of all disks in specified cluster")
    parser.add_argument(
        "-d", "--delete", help="Delete all snapshots older than the specified amount of days")
    parser.add_argument(
        "-r", "--replace", nargs=2, help="Replace the disk underlying a specified Kubernetes PV with a new one")
    args = parser.parse_args()

    # Instantiate objects, credentials, and clients
    options = settings()
    k8s = k8s_control(options, args.cluster)
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    backup_logger.setLevel(logging.INFO)

    # Filter and retrieve necessary items from Google Cloud
    all_disks = list_disks(compute, options.project_id, options.project_zone)
    all_instances = list_instances(compute, options.project_id, options.project_zone)
    all_snapshots = list_snapshots(compute, options.project_id)

    # If specified, create snapshots of all eligible disks
    if args.backup:
        filtered_disks = filter_disks_by_name(all_disks, k8s.filtered_disk_names)
        backup_logger.info("Filtered %d disks out of %d total that are eligible for snapshotting",
                            len(filtered_disks), len(all_disks))
        for disk in filtered_disks:
            request_body = {
                "kind" : "compute#snapshot",
                "name" : disk['name'],
                "id"   : disk['id']
            }
            create_snapshot_of_disk(compute, disk['name'], options.project_id, options.project_zone, request_body)

    # Delete all snapshots older than the specified number of days
    if args.delete:
        snapshots_to_delete = filter_snapshots_by_time(all_snapshots, int(args.delete))
        backup_logger.info("Filtered %d snapshots out of %d total that are eligible for deletion",
                        len(snapshots_to_delete), len(all_snapshots))
        for snapshot in snapshots_to_delete:
            delete_snapshot(compute, options.project_id, snapshot['name'])

    # Replace a pre-existing PV's underlying GCE disk with a new one
    if args.replace:
        pv_name, new_disk_name = args.replace
        replace_pv_with_snapshot_disk(pv_name, new_disk_name)

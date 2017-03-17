#!/usr/bin/python3

""" Primary Backup Logic"""
import json
import sys
import datetime
import logging

from datetime import date
from settings import settings
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from json.decoder import JSONDecodeError as JsonError

SNAPSHOT_DATESTRING_LEN = 10

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s')
backup_logger = logging.getLogger("backup")

def list_disks(compute, project, zone):
    """ Lists all persistent disks used by project """
    all_disks = []
    result = compute.disks().list(project=project, zone=zone).execute()
    all_disks.extend(result['items'])

    while 'nextPageToken' in result:
        result = compute.disks().list(project=project, zone=zone, \
            pageToken=result['nextPageToken']).execute()
        all_disks.extend(result['items'])

    return all_disks


def list_snapshots(compute, project):
    """ Lists all snapshots created for this project """
    all_snapshots = []
    result = compute.snapshots().list(project=project).execute()
    all_snapshots.extend(result['items'])

    while 'nextPageToken' in result:
        result = compute.snapshots().list(project=project, \
            pageToken=result['nextPageToken']).execute()
        all_snapshots.extend(result['items'])

    return all_snapshots


def filter_disks_by_name(disks, name):
    """ Takes in NAME, a predefined prefix to disk names, and filters 
    disks to only returns those that have NAME """
    filtered_disks = []
    backup_logger.info("Filtering disks by prefix name: %s", name)
    for disk in disks:
        try:
            if name in disk['name']:
                filtered_disks.append(disk)
        except KeyError:
            sys.exit("Improperly formatted disks -- is your information correct?")
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
        sys.exit("Attempted to filter invalid snapshots")
    return old_snapshots


def create_snapshot_of_disk(compute, disk_name, project, zone, body):
    """ Creates a snapshot of the provided disk """
    backup_logger.info("Creating snapshot for disk %s", disk_name)
    result = compute.disks().createSnapshot(disk=disk_name, project=project, zone=zone, body=body).execute()
    return result


def delete_snapshot(compute, project, snapshot_name):
    """ Deletes a snapshot given its name """
    backup_logger.info("Deleting snapshot %s", snapshot_name)
    result = compute.snapshots().delete(project=project, snapshot=snapshot_name).execute()
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


if __name__ == "__main__":
    options = settings()
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    backup_logger.setLevel(logging.INFO)

    all_disks = list_disks(compute, options.project_id, options.project_zone)
    filtered_disks = filter_disks_by_name(all_disks, options.name_to_filter)
    backup_logger.info("Filtered %d disks out of %d total that are eligible for snapshotting",
                            len(filtered_disks), len(all_disks))

    all_snapshots = list_snapshots(compute, options.project_id)

    for disk in filtered_disks:
        request_body = {
            "kind" : "compute#snapshot",
            "name" : disk['name'],
            "id"   : disk['id']
        }
        create_snapshot_of_disk(compute, disk['name'], options.project_id, options.project_zone, request_body)

    snapshots_to_delete = filter_snapshots_by_time(all_snapshots, options.retention_period)
    backup_logger.info("Filtered %d snapshots out of %d total that are eligible for deletion",
                        len(snapshots_to_delete, len(all_snapshots)))

    for snapshot in snapshots_to_delete:
        delete_snapshot(compute, options.project_id, snapshot['name'])

import json
import sys
import datetime

from datetime import date
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from json.decoder import JSONDecodeError as JsonError

DEFAULT_PROJECT_ID = '92948014362'
DEFAULT_PROJECT_ZONE = 'us-central1-a'
DEFAULT_NAMESPACE_KEY = 'kubernetes.io/created-for/pvc/namespace'
DEFAULT_NAME_FILTER = 'gke-prod-49ca6b0d-dyna-pvc'


def list_disks(compute, project, zone):
    all_disks = []
    result = compute.disks().list(project=project, zone=zone).execute()
    all_disks.extend(result['items'])

    while 'nextPageToken' in result:
        result = compute.disks().list(project=project, zone=zone, \
            pageToken=result['nextPageToken']).execute()
        all_disks.extend(result['items'])

    return all_disks


def list_snapshots(compute, project):
    all_snapshots = []
    result = compute.snapshots().list(project=project).execute()
    all_snapshots.extend(result['items'])

    while 'nextPageToken' in result:
        result = compute.snapshots().list(project=project, \
            pageToken=result['nextPageToken']).execute()
        all_snapshots.extend(result['items'])

    return all_snapshots


def filter_disks_by_name(disks, name):
    filtered_disks = []
    for disk in disks:
        try:
            if name in disk['name']:
                filtered_disks.append(disk)
        except KeyError:
            sys.exit("Improperly formatted disks -- is your information correct?")
    return filtered_disks


def filter_disks_by_namespace(disks, namespace):
    filtered_disks = []
    for disk in disks:
        try:
            disk_namespace = json.loads(disk['description'])[DEFAULT_NAMESPACE_KEY]
            if disk_namespace == namespace:
                filtered_disks.append(disk)
        except (JsonError, KeyError):
            continue
    return filtered_disks


def filter_snapshots_by_time(snapshots, retention_period=2):
    try:
        old_snapshots = list(filter(lambda snapshot: \
            __days_between_now_and_last_backup(snapshot['creationTimestamp'][:10]) > retention_period, snapshots))
    except (TypeError, KeyError):
        sys.exit("Attempted to filter invalid snapshots")
    return old_snapshots


def create_snapshot_of_disk(compute, disk_name, project, zone, body):
    result = compute.disks().createSnapshot(disk=disk_name, project=project, zone=zone, body=body).execute()
    return result


def delete_snapshot(compute, project, snapshot):
    result = compute.snapshots().delete(project=project, snapshot=snapshot_name).execute()
    return result


def __days_between_now_and_last_backup(date_string):
    today = datetime.datetime.now()
    d1 = date(today.year, today.month, today.day)
    snapshot_year, snapshot_month, snapshot_day = \
                [int(num) for num in date_string.split('-')]
    d2 = date(snapshot_year, snapshot_month, snapshot_day)
    delta = d1 - d2
    return delta.days


if __name__ == "__main__":
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    all_disks = list_disks(compute, DEFAULT_PROJECT_ID, DEFAULT_PROJECT_ZONE)
    filtered_disks = filter_disks_by_name(all_disks, DEFAULT_NAME_FILTER)
    all_snapshots = list_snapshots(compute, DEFAULT_PROJECT_ID)

    for disk in filtered_disks:
        request_body = {
            "kind" : "compute#snapshot",
            "name" : disk['name'],
            "id"   : disk['id']
        }
        create_snapshot_of_disk(compute, disk['name'], DEFAULT_PROJECT_ID, DEFAULT_PROJECT_ZONE, request_body)

    snapshots_to_delete = filter_snapshots_by_time(all_snapshots)
    for snapshot in snapshots_to_delete:
        delete_snapshot(compute, DEFAULT_PROJECT_ID, snapshot)

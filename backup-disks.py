import json
import sys

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from json.decoder import JSONDecodeError as JsonError

DEFAULT_PROJECT_ID = '92948014362'
DEFAULT_PROJECT_ZONE = 'us-central1-a'
DEFAULT_NAMESPACE_KEY = 'kubernetes.io/created-for/pvc/namespace'
DEFAULT_NAME_FILTER = 'gke-prod-49ca6b0d-dyna-pvc'

def list_disks(compute, project, zone):
    result = compute.disks().list(project=project, zone=zone).execute()
    return result['items']


def filter_disks_by_name(disks, name):
    filtered_disks = []
    for disk in disks:
        try:
            if name in disk['name']:
                filtered_disks.append(disk)
        except KeyError:
            sys.exit("Improperly formatted disks -- did you enter the right information?")
    return filtered_disks


def filter_disks_by_namespace(disks, namespace):
    filtered_disks = []
    for disk in disks:
        try:
            disk_namespace = json.loads(disk['description'])[DEFAULT_NAMESPACE_KEY]
            if disk_namespace == namespace:
                filtered_disks.append(disk)
        except JsonError, KeyError:
            continue
    return filtered_disks


def create_snapshot_of_disks(disk_name, project, zone):
    result = compute.disks().createSnapshot(disk=disk_name, project=project, zone=zone).execute()
    return result


if __name__ == "__main__":
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    all_disks = list_disks(compute, DEFAULT_PROJECT_ID, DEFAULT_PROJECT_ZONE)
    filtered_disks = filter_disks_by_name(all_disks, DEFAULT_NAME_FILTER)

    for disk in filtered_disks:
        create_snapshot_of_disks(disk['name'], DEFAULT_PROJECT_ID, DEFAULT_PROJECT_ZONE)



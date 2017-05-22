#!/usr/bin/python

# Requires libsqlite3-mod-impexp for sqlite/json feature.

import os
import socket
import time
import subprocess as sp

import sqlite3

from gcloud import storage

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# gcloud instance where this script is being run
instance = socket.gethostname()

# directory where tarballs are written
tarball_dir = "/var/tmp/archives"

# gce values
project = 'data-8'
zone = 'us-central1-a'
bucket_name = "berkeley-dsep-2017-spring"

# sqlite db path template
sqlite_tmpl = '/home/ryan/jupyterhub-{}.sqlite'

def get_user_from_claim(ns, claim):
	'''Return the user's login given the claim name. We infer the pod name
	   from the claim, then ask the hub for the user name.

       for each namespace,
       kubectl --namespace=<namespace> cp \
		   hub-deployment-...:/srv/jupyterhub/jupyterhub.sqlite \
		   ~/jupyterhub-<namespace>.sqlite
	'''
	conn = sqlite3.connect(sqlite_tmpl.format(ns))
	c = conn.cursor()
	pod_name = claim.replace('claim', 'jupyter', 1)
	sql = 'select name from users where json_extract(state,"$.pod_name")=?'
	c.execute(sql, (pod_name,))
	return c.fetchone()[0]

def tar_file_tmpl(user, namespace):
	return '{}-{}.tar.gz'.format(namespace, user)

def archive_exists(bucket, user, namespace):
	return bucket.get_blob(tar_file_tmpl(user, namespace))

# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/compute/api/create_instance.py
def wait_for_operation(compute, project, zone, operation):
	'''Wait for a gcloud operation to complete and return its result.
       Raise an exception for any error unless it is for when try to create
	   a resource that already exists.'''
	result = {}
	while True:
		result = compute.zoneOperations().get(project=project,
			zone=zone, operation=operation).execute()
		if result['status'] == 'DONE': break
		time.sleep(1)

	if 'error' in result:
		code = result['error']['errors'][0]['code']
		if code not in ['RESOURCE_ALREADY_EXISTS']:
			raise(result['error']['errors'][0]['message'])

	return result

def create_snapshot(service, project, zone, disk, snapshot):
	'''If necessary, create a snapshot of a disk from the snapshot name,
       and return the snapshot ID.'''

	request = service.disks().createSnapshot(project=project, zone=zone,
		disk=pd, body={'name':snapshot})
	response = request.execute()
	result = wait_for_operation(service, project, zone, response['name'])

	# Get the snapshot ID
	request = service.snapshots().get(project=project, snapshot=snapshot)
	response = request.execute()
	snapshot_id = response['id']

	return snapshot_id

def delete_snapshot(service, project, snapshot):
	'''Delete a snapshot.'''
	request = service.snapshots().delete(project=project, snapshot=snapshot)
	response = request.execute()
	result = wait_for_operation(service, project, zone, response['name'])
	
def create_disk(service, project, zone, disk_name, snapshot_id):
	'''If necessary, create an archive disk from the snapshot ID, 
	   and return the link to the disk.'''

	body = {
		'name': disk_name,
		'sourceSnapshotId': snapshot_id,
	}
	request = service.disks().insert(project=project, zone=zone, body=body)
	response = request.execute()
	result = wait_for_operation(service, project, zone, response['name'])

	# Get the disk's url
	request = service.disks().get(project=project, zone=zone, disk=archive_disk)
	response = request.execute()
	disk_link = response['selfLink']

	return disk_link
	
def delete_disk(service, project, zone, disk):
	'''Delete a disk from the disk name.'''
	request = service.disks().delete(project=project, zone=zone, disk=disk)
	response = request.execute()
	result = wait_for_operation(service, project, zone, response['name'])
	
def attach_disk(service, project, zone, instance, disk_link, device_name):
	'''Attach the disk associated with the snapshot.'''

	body = {
		'source': disk_link,
		'deviceName': device_name,
	}
	request = service.instances().attachDisk(project=project, zone=zone,
		instance=instance, body=body)
	response = request.execute()
	result = wait_for_operation(service, project, zone, response['name'])

def detach_disk(service, project, zone, instance, device_name):
	'''Detach the disk associated with the snapshot.'''
	request = service.instances().detachDisk(project=project, zone=zone,
		instance=instance, deviceName=device_name)
	response = request.execute()
	result = wait_for_operation(service, project, zone, response['name'])

def mount_disk(mount_dir, block_device):
	# Mount the disk
	if not os.path.exists(mount_dir):
		cmd = ['sudo', 'mkdir', mount_dir]
		p = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
		p.check_returncode()

	cmd = ['sudo', 'mount', block_device, mount_dir]
	p = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
	p.check_returncode()

def make_archive(ns, user, pd):
	'''Archive user pvc to gcloud archive storage.
	    - namespace: e.g. datahub, stat28, prob140
	    - claim: of the form claim-<user-name>-NNN
	    - pd: google persistend disk, e.g. gke-prod-long-uuid-looking-thing
	'''

	# extract user name from "claim-<user-name>-NNN"
	email = user + '@berkeley.edu'

	# name the things
	ns_user = ns + '-' + user
	archive_name = ns_user
	snapshot = 'snapshot-' + ns_user
	archive_disk = 'archive-disk-' + ns_user
	device_name = archive_disk
	mount_dir = '/mnt/disks/' + archive_disk
	block_device = '/dev/disk/by-id/google-' + archive_disk
	tar_file = tar_file_tmpl(user, ns)
	url = 'https://storage.cloud.google.com/' + bucket_name + '/' + tar_file

	# Create a snapshot of the disk
	snapshot_id = create_snapshot(service, project, zone, pd, snapshot)

	# Create an archive disk from the snapshot
	disk_link = create_disk(service, project, zone, archive_disk, snapshot_id)
	
	# Attach archive disk
	attach_disk(service, project, zone, instance, disk_link, device_name)

	# Mount the disk
	mount_disk(mount_dir, block_device)

	# Create the tar file
	tar_file_path = os.path.join(tarball_dir, tar_file)
	cmd = ['sudo', 'tar', 'czf', tar_file_path, '-C', '/mnt/disks',
		archive_disk]
	p.check_returncode()

	# Upload the tarball to Google archival storage
	blob = bucket.blob(tar_file)
	blob.upload_from_filename(filename=os.path.join(tarball_dir, tar_file))

	# Allow student to access their bucket
	# gsutil acl ch -u ${email}:R gs://${bucket_name}/${tar_file}

	# Unmount disk
	cmd = ['sudo', 'umount', mount_dir]

	# Detach archive disk
	detach_disk(service, project, zone, instance, device_name)

	# Delete archive disk
	delete_disk(service, project, zone, archive_disk)

	# Delete snapshot
	delete_snapshot(service, project, snapshot)

	# Delete tar file
	os.remove(tar_file_path)

# main
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'beta', credentials=credentials)

# http://gcloud-python.readthedocs.io/en/latest/storage-client.html
gs_client = storage.Client()

try:
	bucket = gs_client.get_bucket(bucket_name)
except gcloud.exceptions.Forbidden:
	bucket = gs_client.create_bucket(bucket_name)
except gcloud.exceptions.NotFound:
	bucket = gs_client.create_bucket(bucket_name)

# Create tarball directory
if not os.path.isdir(tarball_dir):
	os.mkdir(tarball_dir)

# Go through piped data
for line in fileinput.input():
	els = line.split()

	namespace = els[0]
	claim = els[1]
	disk = els[2]

	# if claim is not a user's, continue; dsep convention
	if not claim.startswith('claim-'): continue

	try:
		user = get_user_from_claim(namespace, claim)
	except Exception as e:
		print('E: Could not resolve user from claim: {} in {}'.format(
			claim, namespace))
		continue

	# Skip blobs that already exist
	if not archive_exists(bucket, user, namespace):
		make_archive(namespace, user, disk)

# vim:set ts=4 sw=4 noet:

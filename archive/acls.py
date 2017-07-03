#!/usr/bin/env python3

import sys
import pprint

from gcloud import storage
from gcloud.exceptions import NotFound

def validate(bucket, ns, user):
	blob = bucket.blob('{}-{}.tar.gz'.format(ns, user))
	acls = list(blob.acl)
	entity = 'user-' + user + '@berkeley.edu'
	if entity not in list(map(lambda x: x['entity'], acls)):
		print('User not granted access: ' + user)
	else:
		print('Validated: ' + user)
	pprint.pprint(acls)


try:
	ns   = sys.argv[1]
	user = sys.argv[2]
except:
	print("Usage: {} NAMESPACE USER".format(sys.argv[0]))
	sys.exit(1)

bucket_name = 'berkeley-dsep-2017-spring'

gs_client = storage.Client()
bucket = gs_client.get_bucket(bucket_name)

try:
	validate(bucket, ns, user)
except NotFound as e:
	print("Blob not found for " + user)

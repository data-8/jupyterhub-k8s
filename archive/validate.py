#!/usr/bin/env python3

import sqlite3
from gcloud import storage
from gcloud.exceptions import NotFound

sqlite_tmpl = '/home/ryan/jupyterhub-{}.sqlite'
ns = 'stat28'
ns = 'prob140'
ns = 'datahub'
bucket_name = 'berkeley-dsep-2017-spring'

gs_client = storage.Client()
bucket = gs_client.get_bucket(bucket_name)

conn = sqlite3.connect(sqlite_tmpl.format(ns))
c = conn.cursor()

c.execute('select name from users')
users = list(map(lambda x: x[0], c.fetchall()))

for user in users:
	blob = bucket.blob('{}-{}.tar.gz'.format(ns, user))
	try:
		acls = list(blob.acl)
	except NotFound as e:
		print('User has no blob: {}'.format(user))
		continue

	entity = 'user-' + user + '@berkeley.edu'
	if entity not in list(map(lambda x: x['entity'], acls)):
		altuser = user.replace('-', '_')
		if altuser in users:
			print('Skipping doppleganger: {} ({})'.format(
				user, altuser))
			continue
		print('User not granted access: ' + user)
		print(acls)
		#blob.acl.user(user + '@berkeley.edu').grant_read()
		#blob.acl.save()
	else:
		print('Validated: ' + user)


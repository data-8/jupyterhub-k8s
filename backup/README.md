Google Cloud Autobackups
===================================
### General
This script was created to automate the creation of backup snapshots for each existing Google Cloud persistent disk. This script is to be run on a daily basis, and snapshots are kept for a user-specified retention period before they are deleted.

### Expected Behavior
When `backup-disks.py` is run, we expect:

1. The script will acquire necessary credentials and find all the snapshots and disks belong to the cluster
2. The snapshots and disks will be filtered by `NAMESPACE` or `NAME` in order to produce a list of filtered snapshots and disks to be preserved.
3. Snapshots are created for each relevant disk
4. Existing snapshots are filtered by a preset `retention_period` and all snapshots older than `retention_period` are deleted.

### Requirements
Python 3 with the Python Google Cloud Client, `google-api-python-client`
and necessary permissions to access the cluster

### Running This Script
Make sure you read `settings.py` first to look at default values for your cluster. By default, values are specified to the Data8 cluster. You can change your local environment variables to modify how this script runs.

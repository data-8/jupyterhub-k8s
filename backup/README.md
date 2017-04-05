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

### Advanced
Before running, please configure your cluster such that you are assessing the correct nodes and pods. The autobackup script proceeds in the following fashion:
1. Extracting all pods and nodes corresponding to the pre-defined cluster
2. Comparing all persistent volume claims and keeping those belonging to the notebook type (this is to be changed later)
3. Claims that are kept will be filtered for their persistent disk names, which are passed to the Google Cloud API
4. These names are then matched to all available persistent disk structures for the project, and replaced

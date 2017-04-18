Google Cloud Autobackups
===================================
### General
This script was created for Data 8 to automate the creation of backup snapshots for each existing Google Cloud persistent disk that underlies student notebooks. This script is mindful of Kubernetes, and can be run at user expected times to ensure redundancy of data. 

### Expected Behavior
This script was written with the following requirements in mind:

1. Accurately acquire and filter all disks and snapshots by namespace
2. Allow for specified to disks to be snapshotted
3. Allow new disks to be made from snapshots
4. Allow existing Kubernetes PVs to be patched with new disks
5. Allow for snapshots to be retained by a specified number of days, then deleted

All of the behavior and how to use the script is documented below.

### Running This Script
Make sure you read `settings.py` first to look at default values for your cluster. By default, values are specified to the Data8 cluster. You can change your local environment variables to modify how this script runs.

Please be mindful of the command line arguments required to run this script. The definitions are provided for you below:

`-c`, `--cluster` - __REQUIRED__. The name of your cluster, such as `dev` or `prod` should follow this tag

`-b`, `--backup` - Whether or not disk backups should be performed, followed by the namespace to filter on, such as `datahub`

`--create-disk` - Whether or not to automatically create disks from all snapshots made via backup, no subsequent value required.

`-d`, `--delete` - Whether or not snapshots will be deleted, and the number of days their lifespan should be at maximum

`-r`, `--replace` - Whether or not a pre-existing Kubernetes PV should be patched with a newly created GCE disk. Requires __two__ arguments, the name of the Kubernetes PV and the name of the GCE disk

`-t`, `--test` - Whether or not to run this script in a test mode, where logs will be shown but no real action will be taken to your cluster. No subsequent value provided.

`-v`, `--verbose` - Whether or not `debug` level logs should be shown

An example of a few correct ways to run this script might be:
`python3 backup-disks.py --cluster prod --backup datahub --delete 3 --verbose --test`

`python3 backup-disks.py --cluster dev --backup datahub-dev --create-disk`

`python3 backup-disks.py --cluster prod --replace pvc-5cab5673-1987-11e7-88ce-42010a800027 example_snapshot_disk`

### Requirements
Python 3 with the Python Google Cloud Client, `google-api-python-client`, and `kubernetes`
and necessary permissions to access the cluster

### Blueprint
![Blueprint Banner](https://cloud.githubusercontent.com/assets/2468904/11998649/8a12f970-aa5d-11e5-8dab-7eef0766c793.png)

This project was worked on in close collaboration with **[Cal Blueprint](http://www.calblueprint.org/)**. Cal Blueprint is a student-run UC Berkeley organization devoted to matching the skills of its members to our desire to see social good enacted in our community. Each semester, teams of 4-5 students work closely with a non-profit to bring technological solutions to the problems they face every day.

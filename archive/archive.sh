#!/bin/bash

# gcloud node where this script is being run
node="provisioner-01"

# directory where tarballs are written
tarball_dir="/var/tmp/archives"

# gce bucket
bucket_name="berkeley-dsep"

# 
# arguments:
#   claim: of the form claim-<user-name>-NNN
#   namespace: e.g. datahub, stat28, prob140
#   pd: google persistend disk, e.g. gke-prod-long-uuid-looking-thing
function make_archive {
	ns=$1 ; claim=$2 ; pd=$3

	# if claim is not a user's, continue
	if [[ $claim != claim-* ]]; then continue ; fi

	echo archiving $claim

	# extract user name from "claim-<user-name>-NNN"
	user=$(echo $claim | cut -d'-' -f2- | rev | cut -d'-' -f2- | rev)
	email="${user}@berkeley.edu"

    # name the things
	archive_name="${ns}-${user}"
	snapshot="snapshot-${ns}-${user}"
	archive_disk="archive-disk-${ns}-${user}"
	mount_dir=/mnt/disks/${archive_disk}
	block_device=/dev/disk/by-id/google-${archive_disk}
	tar_file="${ns}-${user}.tar.gz"
    url="https://storage.cloud.google.com/${bucket_name}/${tar_file}"

	# Create a snapshot of the disk
	gcloud compute disks snapshot --snapshot-names ${snapshot} ${pd} ||
        return

	# Create an archive disk from the snapshot
	gcloud compute disks create ${archive_disk} \
		--source-snapshot ${snapshot} || \
        return

	# Attach archive disk
	gcloud compute instances attach-disk ${node} --disk ${archive_disk} \
		--device-name ${archive_disk} || \
        return

	# Mount the disk
	sudo mkdir ${mount_dir}
	sudo mount ${block_device} ${mount_dir} || return

	# Create the tar file
	sudo tar czf ${tarball_dir}/${tar_file} -C /mnt/disks ${archive_disk} || \
        return

	# Upload the tarball to Google archival storage
	gsutil cp ${tarball_dir}/${tar_file} gs://${bucket_name}/ || \
        return

	# Allow student to access their bucket
	gsutil acl ch -u ${email}:R gs://${bucket_name}/${tar_file} || \
        return

	# Unmount disk
	sudo umount ${mount_dir} || \
        return

	# Detach archive disk
	gcloud compute instances detach-disk ${node} --disk ${archive_disk} || \
        return

	# Delete archive disk
	gcloud -q compute disks delete ${archive_disk} || \
        return

	# Delete snapshot
	gcloud -q compute snapshots delete ${snapshot} ||
        return

	# Delete tar file
	rm -f ${tarball_dir}/${tar_file} ||
        return

    echo ${url}
}

# main

# Create tarbar directory
if [ ! -d ${tarball_dir} ]; then
	mkdir ${tarball_dir}
fi

# Create bucket if it doesn't exist
gsutil ls -b gs://${bucket_name}/ > /dev/null 2>&1 ||
    ( gsutil mb gs://${bucket_name}/ && \
        ( echo Unable to create bucket: $bucket_name 1>&2 ; exit 1 )
    )

# Go through piped data
while read line ; do
    set -f $line

    make_archive $1 $2 $3
done

# vim:set ts=4 sw=4 et:

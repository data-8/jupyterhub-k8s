Archive to GCloud
=================

1. Generate the list of persistent volume claims to archive:

`kubectl get pv -o jsonpath="{range .items[*]}{.spec['claimRef.namespace','claimRef.name','gcePersistentDisk.pdName']} {end}" | xargs -n 3 > claims.tsv`

2. Archive the volumes:

`cat claims.tsv | archive.sh`

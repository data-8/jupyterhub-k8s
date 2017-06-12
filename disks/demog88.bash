#!/bin/sh
# uploads data for immigrants lab
set -e

wget http://courses.demog.berkeley.edu/mason88/data/immigrants0.tgz
tar -xzvf immigrants0.tgz
rm immigrants0.tgz

exit 0

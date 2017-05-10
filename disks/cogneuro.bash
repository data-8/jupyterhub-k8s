#!/bin/bash

set -e

# Added data for the final exam
wget https://www.dropbox.com/s/dkyn897kscbp6bc/data8_final.tar.gz
tar -xvf data8_final.tar.gz
rm data8_final.tar.gz

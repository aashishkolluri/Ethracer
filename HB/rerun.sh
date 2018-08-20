#!/bin/bash
cd /mnt/c/Happens-Before/HB/
echo "Getting inactive processes"
python parse_ps.py --cores $1
chmod 755 toexec.sh
echo "Running toexec.sh"
./toexec.sh

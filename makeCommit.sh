#!/bin/bash
set -euo pipefail

#echo $1 $2 $3 $4


jq '.version=.version+1' config.json > tmp.json && mv tmp.json config.json

git add -A && git commit -a -m "$(jq '.version' config.json)" && git push

ssh 130.56.244.137 -C "cd /var/www/faims/exporters/d20170518-4034-181uwm7/; git pull"

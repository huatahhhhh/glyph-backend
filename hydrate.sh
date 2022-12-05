#!/bin/bash
cd /home/ubuntu2/projects/twitter_bot
source ./load_env.sh
/home/ubuntu2/anaconda3/envs/twitter/bin/python hydrate_db.py
now=$(date +"%T")
echo "Ran on : $now" >> /home/ubuntu2/hydrate_logs.txt

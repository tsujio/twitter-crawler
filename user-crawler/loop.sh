#!/bin/bash

LOCKFILE=~/twitter-user-crawler.lock

while true; do
    if [ -e $LOCKFILE ]; then
        echo "Found $LOCKFILE. Skip crawling." 1>&2
    else
        mkdir $LOCKFILE

        docker run \
               --env-file twitter-api-token.txt \
               -v ~/data:/app/data \
               --rm \
               twitter-user-crawler \
               python /app/main.py

        rmdir $LOCKFILE
    fi
    sleep 60
done

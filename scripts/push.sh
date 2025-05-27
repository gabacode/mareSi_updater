#!/bin/bash

git config user.name "autoupdate"
git config user.email "actions@users.noreply.github.com"

git add -A

timestamp=$(date --iso-8601=seconds)
git commit -m "update: ${timestamp}" || exit 0

git push

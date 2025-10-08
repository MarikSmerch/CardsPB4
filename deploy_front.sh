#!/usr/bin/env bash
set -e
cd /home/mark/sites/cardspb4
git pull
cd frontend
npm ci
npm run build
rm -rf /home/mark/sites/cardspb4/web/*
cp -r dist/* /home/mark/sites/cardspb4/web/
echo "✅ Front deployed"

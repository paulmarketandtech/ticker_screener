#!/bin/bash
docker compose up -d --build
docker image prune -f
echo "✅ Deployed and cleaned up!"

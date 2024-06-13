#! /bin/sh
curl -X POST \
  https://192.168.10.128:9443/api/auth \
  -k \
  -H "Content-Type: application/json" \
  -d '{
        "username": "admin",
        "password": "veryhungryphage"
      }'


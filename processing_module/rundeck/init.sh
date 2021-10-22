#!/bin/sh

# https://docs.rundeck.com/docs/api/rundeck-api.html
# https://stackoverflow.com/questions/65037081/auto-create-rundeck-jobs-on-startup-rundeck-in-docker-container
sleep 120

curl -X POST rundeck:4440/api/14/projects -H "X-Rundeck-Auth-Token:testtoken" -H "Content-Type: application/json" --data '{"name": "twitter"}'
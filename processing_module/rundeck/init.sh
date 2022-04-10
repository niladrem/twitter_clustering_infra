#!/bin/sh

# https://docs.rundeck.com/docs/api/rundeck-api.html
# https://stackoverflow.com/questions/65037081/auto-create-rundeck-jobs-on-startup-rundeck-in-docker-container

export RD_TOKEN="testtoken"
export RD_URL="rundeck:4440"
export RD_JOB_PATH="/etc/rundeck"

while true
do
  sleep 30
  echo "Check rundeck health"
  HEALTH=$(curl "$RD_URL/health")
  if [ "$HEALTH" = "ok" ]; then
    break
  fi
done

curl -X POST "$RD_URL/api/14/projects" -H "X-Rundeck-Auth-Token:$RD_TOKEN" -H "Content-Type: application/json" --data '{"name": "twitter"}'
curl -kSsv -H "X-Rundeck-Auth-Token:$RD_TOKEN" -H "Content-Token: application/yaml" -H "fileformat: yaml" -F xmlBatch=@"$RD_JOB_PATH/Download_tweets.yaml" "$RD_URL/api/14/project/twitter/jobs/import?fileformat=yaml&dupeOption=update"

curl -kSsv -H "X-Rundeck-Auth-Token:$RD_TOKEN" -H "Content-Token: application/yaml" -H "fileformat: yaml" -F xmlBatch=@"$RD_JOB_PATH/Parse_tweets.yaml" "$RD_URL/api/14/project/twitter/jobs/import?fileformat=yaml&dupeOption=update"

curl -kSsv -H "X-Rundeck-Auth-Token:$RD_TOKEN" -H "Content-Token: application/yaml" -H "fileformat: yaml" -F xmlBatch=@"$RD_JOB_PATH/Insert_into_postgres.yaml" "$RD_URL/api/14/project/twitter/jobs/import?fileformat=yaml&dupeOption=update"

curl -kSsv -H "X-Rundeck-Auth-Token:$RD_TOKEN" -H "Content-Token: application/yaml" -H "fileformat: yaml" -F xmlBatch=@"$RD_JOB_PATH/Run_flow.yaml" "$RD_URL/api/14/project/twitter/jobs/import?fileformat=yaml&dupeOption=update"

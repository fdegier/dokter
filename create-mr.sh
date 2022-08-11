#!/bin/bash
# This script was adapted from:
# https://about.gitlab.com/2017/09/05/how-to-automatically-create-a-new-mr-on-gitlab-with-gitlab-ci/

DOKTER_BRANCH="dokter/${CI_COMMIT_REF_NAME}"

# Setup git
DOCKERFILE=${DOKTER_DOCKERFILE}

if [[ $(git status --untracked-files=no -s | grep -c "${DOCKERFILE}" ) -eq 0 ]]
then
  echo "${DOCKERFILE} not changed so exiting"
  exit 0
fi

git add "${DOCKERFILE}"
git config --global user.email "dokter@gitlab.com"
git config --global user.name "Dokter"
git checkout -b "${DOKTER_BRANCH}"
ssh-keyscan "${CI_SERVER_HOST}" > ~/.ssh/known_hosts
git remote set-url --push origin "git@${CI_SERVER_HOST}:${CI_PROJECT_PATH}.git"
git commit -m "Implement fixes from Dokter"
git push -u origin -f "${DOKTER_BRANCH}"

# Create MR
HOST="${CI_API_V4_URL}/projects/${CI_PROJECT_ID}"

MR_TITLE="Dokter results for: ${CI_COMMIT_REF_NAME}"

# The description of our new MR, we want to remove the branch after the MR has been closed
BODY="{
\"project_id\": ${CI_PROJECT_ID},
\"source_branch\": \"${DOKTER_BRANCH}\",
\"target_branch\": \"${CI_COMMIT_REF_NAME}\",
\"remove_source_branch\": true,
\"force_remove_source_branch\": false,
\"allow_collaboration\": true,
\"subscribed\" : true,
\"title\": \"${MR_TITLE}\",
\"assignee_id\": \"${GITLAB_USER_ID}\"
}";

# Require a list of all the merge request and take a look if there is already one with the same source branch
LIST_MRS=$(curl --silent "${HOST}/merge_requests?state=opened" --header "PRIVATE-TOKEN:${GITLAB_API_TOKEN}");
COUNT_BRANCHES=$(echo "${LIST_MRS}" | grep -o "\"source_branch\":\"${DOKTER_BRANCH}\"" | wc -l);

# No MR found, let's create a new one
if [ "${COUNT_BRANCHES}" -eq "0" ]; then
    RESPONSE=$(curl -X POST "${HOST}/merge_requests" \
    --header "PRIVATE-TOKEN:${GITLAB_API_TOKEN}" \
    --header "Content-Type: application/json" \
    --data "${BODY}")
    if [ "$RESPONSE" = 200 ]
    then
      echo "Opened a new merge request: ${MR_TITLE}";
    else
      echo "Failed to create MR"
    fi
    exit;
else
    echo "No new merge request opened"
fi

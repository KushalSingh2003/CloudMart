#!/bin/bash
set -e

CHANGESET_NAME="changeset-${STACK_NAME}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"

if aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" >/dev/null 2>&1; then
    CHANGESET_TYPE="UPDATE"
else
    CHANGESET_TYPE="CREATE"
fi

echo "Creating ${CHANGESET_TYPE} change set..."

aws cloudformation create-change-set \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGESET_NAME}" \
  --change-set-type "${CHANGESET_TYPE}" \
  --template-url "${TEMPLATE_S3_URL}" \
  --parameters "file://${PARAMETERS_FILE}" \
  --tags "file://${TAGS_FILE}" \
  --capabilities CAPABILITY_NAMED_IAM

echo "Waiting for Change Set to become ready..."

for i in $(seq 1 20); do

  STATUS=$(aws cloudformation describe-change-set \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGESET_NAME}" \
    --query 'Status' \
    --output text)

  REASON=$(aws cloudformation describe-change-set \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGESET_NAME}" \
    --query 'StatusReason' \
    --output text)

  echo "Attempt ${i}/20 — Status: ${STATUS}"

  if [ "${STATUS}" = "CREATE_COMPLETE" ]; then
    echo "Change Set is ready."
    break
  fi

  if [ "${STATUS}" = "FAILED" ]; then
    echo "Change Set creation failed."
    echo "Reason: ${REASON}"
    exit 1
  fi

  sleep 15

done

echo "changeset_name=${CHANGESET_NAME}" >> "${GITHUB_OUTPUT}"

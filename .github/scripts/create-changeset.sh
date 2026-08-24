#!/bin/bash
set -e

echo "=========================================="
echo "Creating CloudFormation Change Set"
echo "=========================================="

CHANGESET_NAME="changeset-${STACK_NAME}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"

echo "Stack: ${STACK_NAME}"
echo "Change Set: ${CHANGESET_NAME}"

if aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    >/dev/null 2>&1; then

  CHANGESET_TYPE="UPDATE"
  echo "Existing stack detected."
  echo "Change Set type: UPDATE"

else

  CHANGESET_TYPE="CREATE"
  echo "Stack does not exist."
  echo "Change Set type: CREATE"

fi

aws cloudformation create-change-set \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGESET_NAME}" \
  --change-set-type "${CHANGESET_TYPE}" \
  --template-url "${TEMPLATE_S3_URL}" \
  --parameters "file://${PARAMETERS_FILE}" \
  --tags "file://${TAGS_FILE}" \
  --capabilities CAPABILITY_NAMED_IAM

echo "Change Set created."

echo "changeset_name=${CHANGESET_NAME}" >> "${GITHUB_OUTPUT}"

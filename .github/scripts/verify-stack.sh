#!/bin/bash
set -e

echo "=========================================="
echo "Verifying CloudFormation Stack"
echo "=========================================="

STATUS=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --query 'Stacks[0].StackStatus' \
  --output text)

echo "Stack: ${STACK_NAME}"
echo "Status: ${STATUS}"

if [[ "${STATUS}" == *"COMPLETE"* ]]; then

  echo "Stack is healthy."

else

  echo "Stack verification failed."
  exit 1

fi

echo ""
echo "Stack Outputs:"
echo "------------------------------------------"

aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --query 'Stacks[0].Outputs[*].{Key:OutputKey,Value:OutputValue}' \
  --output table

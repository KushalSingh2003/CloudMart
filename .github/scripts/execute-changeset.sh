#!/bin/bash
set -e

echo "=========================================="
echo "Executing Change Set"
echo "=========================================="

echo "Stack: ${STACK_NAME}"
echo "Change Set: ${CHANGESET_NAME}"

aws cloudformation execute-change-set \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGESET_NAME}"

echo "Change Set execution started."

echo "Waiting for stack to stabilize..."

for i in $(seq 1 40); do

  STATUS=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query 'Stacks[0].StackStatus' \
    --output text)

  echo "Attempt ${i}/40 — Status: ${STATUS}"

  case "${STATUS}" in

    CREATE_COMPLETE|UPDATE_COMPLETE)
      echo "Stack deployment successful."
      exit 0
      ;;

    CREATE_IN_PROGRESS|UPDATE_IN_PROGRESS|UPDATE_COMPLETE_CLEANUP_IN_PROGRESS)
      sleep 30
      ;;

    CREATE_FAILED|UPDATE_FAILED|ROLLBACK_COMPLETE|ROLLBACK_FAILED|UPDATE_ROLLBACK_FAILED)
      echo "Stack deployment failed."

      aws cloudformation describe-stack-events \
        --stack-name "${STACK_NAME}" \
        --query 'StackEvents[:10].{Time:Timestamp,Status:ResourceStatus,Resource:LogicalResourceId,Reason:ResourceStatusReason}' \
        --output table

      exit 1
      ;;

    *)
      echo "Unexpected status: ${STATUS}"
      sleep 30
      ;;

  esac

done

echo "Stack did not stabilize within the expected time."
exit 1

#!/bin/bash
set -e

echo "=========================================="
echo "Executing Change Set"
echo "=========================================="

echo "Stack: ${STACK_NAME}"
echo "Change Set: ${CHANGESET_NAME}"

# --------------------------------------------------
# 1. Verify Change Set is ready
# --------------------------------------------------

echo ""
echo "Checking Change Set status..."

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

echo "Change Set status: ${STATUS}"

if [ "${STATUS}" != "CREATE_COMPLETE" ]; then
  echo "ERROR: Change Set is not ready for execution."
  echo "Reason: ${REASON}"
  exit 1
fi

# --------------------------------------------------
# 2. Execute Change Set
# --------------------------------------------------

echo ""
echo "Executing Change Set..."

aws cloudformation execute-change-set \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGESET_NAME}"

echo "Change Set execution started."

# --------------------------------------------------
# 3. Wait for Stack to stabilize
# --------------------------------------------------

echo ""
echo "Waiting for stack to stabilize..."
echo "Maximum wait time: 20 minutes"

for i in $(seq 1 40); do

  STATUS=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query 'Stacks[0].StackStatus' \
    --output text)

  echo ""
  echo "Attempt ${i}/40 — Stack status: ${STATUS}"

  case "${STATUS}" in

    CREATE_COMPLETE|UPDATE_COMPLETE)
      echo ""
      echo "=========================================="
      echo "Stack deployment succeeded."
      echo "=========================================="
      exit 0
      ;;

    CREATE_IN_PROGRESS|UPDATE_IN_PROGRESS|UPDATE_COMPLETE_CLEANUP_IN_PROGRESS|ROLLBACK_IN_PROGRESS|UPDATE_ROLLBACK_IN_PROGRESS)
      echo "Stack is still in progress."
      echo "Waiting 30 seconds..."
      sleep 30
      ;;

    CREATE_FAILED|UPDATE_FAILED|ROLLBACK_COMPLETE|ROLLBACK_FAILED|UPDATE_ROLLBACK_COMPLETE|UPDATE_ROLLBACK_FAILED)
      echo ""
      echo "=========================================="
      echo "ERROR: Stack deployment failed."
      echo "Status: ${STATUS}"
      echo "=========================================="

      echo ""
      echo "--- Recent Stack Events ---"

      aws cloudformation describe-stack-events \
        --stack-name "${STACK_NAME}" \
        --query 'StackEvents[:10].{Time:Timestamp,Status:ResourceStatus,Resource:LogicalResourceId,Reason:ResourceStatusReason}' \
        --output table

      exit 1
      ;;

    *)
      echo "Unexpected stack status: ${STATUS}"
      echo "Waiting 30 seconds..."
      sleep 30
      ;;

  esac

done

echo ""
echo "=========================================="
echo "ERROR: Stack did not stabilize within 20 minutes."
echo "=========================================="

exit 1

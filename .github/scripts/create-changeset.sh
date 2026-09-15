# #!/bin/bash
# set -e

# echo "=========================================="
# echo "Creating CloudFormation Change Set"
# echo "Creating CloudFormation Change Set for running the jobs again"
# echo "=========================================="
# CHANGESET_NAME="changeset-${STACK_NAME}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
# echo "Change Set Name: ${CHANGESET_NAME}"

# # --------------------------------------------------
# # 1. Determine whether stack already exists
# # --------------------------------------------------

# if aws cloudformation describe-stacks \
#     --stack-name "${STACK_NAME}" >/dev/null 2>&1; then

#     CHANGESET_TYPE="UPDATE"
#     echo "Stack exists — change set type: UPDATE"

# else

#     CHANGESET_TYPE="CREATE"
#     echo "Stack does not exist — change set type: CREATE"

# fi

# # --------------------------------------------------
# # 2. Validate template URL
# # --------------------------------------------------

# echo "Template URL: ${TEMPLATE_S3_URL}"

# if [ -z "${TEMPLATE_S3_URL}" ]; then
#     echo "ERROR: TEMPLATE_S3_URL is empty."
#     exit 1
# fi

# # --------------------------------------------------
# # 3. Create Change Set
# # --------------------------------------------------

# echo ""
# echo "Creating change set:"
# echo "${CHANGESET_NAME}"
# PARAMETERS_WITH_AUTH=$(mktemp)

# jq --arg token "$AUTH_TOKEN" \
#   '. + [{"ParameterKey":"AuthToken","ParameterValue":$token}]' \
#   "$PARAMETERS_FILE" > "$PARAMETERS_WITH_AUTH"

# aws cloudformation create-change-set \
#     --stack-name "${STACK_NAME}" \
#     --change-set-name "${CHANGESET_NAME}" \
#     --change-set-type "${CHANGESET_TYPE}" \
#     --template-url "${TEMPLATE_S3_URL}" \
#     --parameters "file://${PARAMETERS_WITH_AUTH}" \
#     --tags "file://${TAGS_FILE}" \
#     --capabilities CAPABILITY_NAMED_IAM

# # --------------------------------------------------
# # 4. Wait for Change Set to become ready
# # --------------------------------------------------

# echo ""
# echo "Polling change set status..."
# echo "Maximum attempts: 20"
# echo "Interval: 15 seconds"

# FINAL_STATUS=""

# for i in $(seq 1 20); do

#     STATUS=$(aws cloudformation describe-change-set \
#         --stack-name "${STACK_NAME}" \
#         --change-set-name "${CHANGESET_NAME}" \
#         --query 'Status' \
#         --output text)

#     REASON=$(aws cloudformation describe-change-set \
#         --stack-name "${STACK_NAME}" \
#         --change-set-name "${CHANGESET_NAME}" \
#         --query 'StatusReason' \
#         --output text)

#     echo ""
#     echo "Attempt ${i}/20"
#     echo "Status: ${STATUS}"

#     if [ "${REASON}" != "None" ] && [ -n "${REASON}" ]; then
#         echo "Reason: ${REASON}"
#     fi

#     case "${STATUS}" in

#         CREATE_COMPLETE)
#             echo "Change set is ready for execution."
#             FINAL_STATUS="${STATUS}"
#             break
#             ;;

#         CREATE_IN_PROGRESS|REVIEW_IN_PROGRESS)
#             echo "Change set is still being prepared."
#             echo "Waiting 15 seconds..."
#             sleep 15
#             ;;

#         FAILED)
#             echo "Change set creation failed."

#             if echo "${REASON}" | grep -qi "didn't contain changes"; then
#                 echo "No changes detected."
#                 FINAL_STATUS="NO_CHANGES"
#                 break
#             fi

#             echo "Failure reason: ${REASON}"
#             FINAL_STATUS="FAILED"
#             break
#             ;;

#         *)
#             echo "Unexpected Change Set status: ${STATUS}"
#             echo "Reason: ${REASON}"
#             FINAL_STATUS="${STATUS}"
#             break
#             ;;

#     esac

# done

# # --------------------------------------------------
# # 5. Timeout protection
# # --------------------------------------------------

# if [ -z "${FINAL_STATUS}" ]; then
#     echo ""
#     echo "ERROR: Change set did not become ready after 5 minutes."
#     exit 1
# fi

# # --------------------------------------------------
# # 6. Handle failure
# # --------------------------------------------------

# if [ "${FINAL_STATUS}" = "FAILED" ]; then
#     echo "Change set creation failed."
#     exit 1
# fi

# # --------------------------------------------------
# # 7. Export outputs for GitHub Actions
# # --------------------------------------------------

# echo "changeset_status=${FINAL_STATUS}" >> "${GITHUB_OUTPUT}"
# echo "changeset_name=${CHANGESET_NAME}" >> "${GITHUB_OUTPUT}"

# # --------------------------------------------------
# # 8. Print Change Set details
# # --------------------------------------------------

# echo ""
# echo "=========================================="
# echo "Change Set Summary"
# echo "=========================================="

# aws cloudformation describe-change-set \
#     --stack-name "${STACK_NAME}" \
#     --change-set-name "${CHANGESET_NAME}" \
#     --query 'Changes[*].{Action:ResourceChange.Action,Resource:ResourceChange.LogicalResourceId,Type:ResourceChange.ResourceType,Replacement:ResourceChange.Replacement}' \
#     --output table || echo "No changes to display."

# echo ""
# echo "Change Set processing completed."
# echo "Status: ${FINAL_STATUS}"
#!/bin/bash

set -e

echo "=========================================="
echo "Creating CloudFormation Change Set"
echo "Creating CloudFormation Change Set for running the jobs again"
echo "=========================================="

CHANGESET_NAME="changeset-${STACK_NAME}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"

echo "Change Set Name: ${CHANGESET_NAME}"

# --------------------------------------------------
# 1. Determine whether stack already exists
# --------------------------------------------------

if aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" >/dev/null 2>&1; then

    CHANGESET_TYPE="UPDATE"
    echo "Stack exists — change set type: UPDATE"

else

    CHANGESET_TYPE="CREATE"
    echo "Stack does not exist — change set type: CREATE"

fi

# --------------------------------------------------
# 2. Validate template URL
# --------------------------------------------------

echo "Template URL: ${TEMPLATE_S3_URL}"

if [ -z "${TEMPLATE_S3_URL}" ]; then
    echo "ERROR: TEMPLATE_S3_URL is empty."
    exit 1
fi

# --------------------------------------------------
# 3. Create parameters file
# --------------------------------------------------



echo ""
echo "Preparing CloudFormation parameters..."

PARAMETERS_WITH_AUTH=$(mktemp)

if [ -n "${PARAMETERS_FILE}" ]; then

    echo "Using parameters file: ${PARAMETERS_FILE}"

    jq \
      --arg runid "$GITHUB_RUN_ID" \
      --arg token "$AUTH_TOKEN" \
      '. + [
        {"ParameterKey":"GitHubRunId","ParameterValue":$runid},
        {"ParameterKey":"AuthToken","ParameterValue":$token}
      ]' \
      "$PARAMETERS_FILE" > "$PARAMETERS_WITH_AUTH"

else

    echo "No parameters file provided."
    echo "Using GitHub Secrets for database parameters."

    jq -n \
      --arg environment "$ENVIRONMENT" \
      --arg dbname "$DB_NAME" \
      --arg username "$DB_USERNAME" \
      --arg password "$DB_PASSWORD" \
      '[
        {"ParameterKey":"Environment","ParameterValue":$environment},
        {"ParameterKey":"DatabaseName","ParameterValue":$dbname},
        {"ParameterKey":"MasterUsername","ParameterValue":$username},
        {"ParameterKey":"MasterUserPassword","ParameterValue":$password}
      ]' > "$PARAMETERS_WITH_AUTH"

fi

echo "CloudFormation parameters prepared."
# --------------------------------------------------
# 4. Create Change Set
# --------------------------------------------------

echo ""
echo "Creating change set:"
echo "${CHANGESET_NAME}"

aws cloudformation create-change-set \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGESET_NAME}" \
    --change-set-type "${CHANGESET_TYPE}" \
    --template-url "${TEMPLATE_S3_URL}" \
    --parameters "file://${PARAMETERS_WITH_AUTH}" \
    --tags "file://${TAGS_FILE}" \
    --capabilities CAPABILITY_NAMED_IAM

# --------------------------------------------------
# 5. Wait for Change Set to become ready
# --------------------------------------------------

echo ""
echo "Polling change set status..."
echo "Maximum attempts: 20"
echo "Interval: 15 seconds"

FINAL_STATUS=""

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

    echo ""
    echo "Attempt ${i}/20"
    echo "Status: ${STATUS}"

    if [ "${REASON}" != "None" ] && [ -n "${REASON}" ]; then
        echo "Reason: ${REASON}"
    fi

    case "${STATUS}" in

        CREATE_COMPLETE)
            echo "Change set is ready for execution."
            FINAL_STATUS="${STATUS}"
            break
            ;;

        CREATE_IN_PROGRESS|REVIEW_IN_PROGRESS)
            echo "Change set is still being prepared."
            echo "Waiting 15 seconds..."
            sleep 15
            ;;

        FAILED)
            echo "Change set creation failed."

            if echo "${REASON}" | grep -qi "didn't contain changes"; then
                echo "No changes detected."
                FINAL_STATUS="NO_CHANGES"
                break
            fi

            echo "Failure reason: ${REASON}"
            FINAL_STATUS="FAILED"
            break
            ;;

        *)
            echo "Unexpected Change Set status: ${STATUS}"
            echo "Reason: ${REASON}"
            FINAL_STATUS="${STATUS}"
            break
            ;;

    esac

done

# --------------------------------------------------
# 6. Timeout protection
# --------------------------------------------------

if [ -z "${FINAL_STATUS}" ]; then
    echo ""
    echo "ERROR: Change set did not become ready after 5 minutes."
    exit 1
fi

# --------------------------------------------------
# 7. Handle failure
# --------------------------------------------------

if [ "${FINAL_STATUS}" = "FAILED" ]; then
    echo "Change set creation failed."
    exit 1
fi

# --------------------------------------------------
# 8. Export outputs for GitHub Actions
# --------------------------------------------------

echo "changeset_status=${FINAL_STATUS}" >> "${GITHUB_OUTPUT}"
echo "changeset_name=${CHANGESET_NAME}" >> "${GITHUB_OUTPUT}"

# --------------------------------------------------
# 9. Print Change Set details
# --------------------------------------------------

echo ""
echo "=========================================="
echo "Change Set Summary"
echo "=========================================="

aws cloudformation describe-change-set \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGESET_NAME}" \
    --query 'Changes[*].{Action:ResourceChange.Action,Resource:ResourceChange.LogicalResourceId,Type:ResourceChange.ResourceType,Replacement:ResourceChange.Replacement}' \
    --output table || echo "No changes to display."

echo ""
echo "Change Set processing completed."
echo "Status: ${FINAL_STATUS}"

# --------------------------------------------------
# 10. Cleanup temporary file
# --------------------------------------------------

rm -f "${PARAMETERS_WITH_AUTH}"
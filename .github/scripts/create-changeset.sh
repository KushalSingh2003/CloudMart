- name: Create Change Set
  id: create-changeset
  env:
    STACK_NAME: ${{ inputs.stack_name }}
    PARAMETERS_FILE: ${{ inputs.parameters_file }}
    TAGS_FILE: ${{ inputs.tags_file }}
    TEMPLATE_S3_URL: ${{ steps.upload.outputs.template_s3_url }}
    AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}
  run: |
    #!/bin/bash

    set -e

    echo "=========================================="
    echo "Creating CloudFormation Change Set"
    echo "=========================================="

    CHANGESET_NAME="changeset-${STACK_NAME}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"

    echo "Stack Name: ${STACK_NAME}"
    echo "Change Set Name: ${CHANGESET_NAME}"
    echo "GitHub Run ID: ${GITHUB_RUN_ID}"
    echo "GitHub Run Attempt: ${GITHUB_RUN_ATTEMPT}"

    # --------------------------------------------------
    # 1. Determine whether stack already exists
    # --------------------------------------------------

    echo ""
    echo "Checking whether stack exists..."

    if aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" >/dev/null 2>&1; then

        CHANGESET_TYPE="UPDATE"

        echo "Stack exists."
        echo "Change set type: UPDATE"

    else

        CHANGESET_TYPE="CREATE"

        echo "Stack does not exist."
        echo "Change set type: CREATE"

    fi

    # --------------------------------------------------
    # 2. Validate template URL
    # --------------------------------------------------

    echo ""
    echo "Validating template URL..."

    echo "Template URL: ${TEMPLATE_S3_URL}"

    if [ -z "${TEMPLATE_S3_URL}" ]; then
        echo "ERROR: TEMPLATE_S3_URL is empty."
        exit 1
    fi

    # --------------------------------------------------
    # 3. Check parameters file exists
    # --------------------------------------------------

    echo ""
    echo "Checking parameters file..."

    if [ ! -f "${PARAMETERS_FILE}" ]; then
        echo "ERROR: Parameters file does not exist:"
        echo "${PARAMETERS_FILE}"
        exit 1
    fi

    echo "Parameters file found:"
    echo "${PARAMETERS_FILE}"

    # --------------------------------------------------
    # 4. Check tags file exists
    # --------------------------------------------------

    echo ""
    echo "Checking tags file..."

    if [ ! -f "${TAGS_FILE}" ]; then
        echo "ERROR: Tags file does not exist:"
        echo "${TAGS_FILE}"
        exit 1
    fi

    echo "Tags file found:"
    echo "${TAGS_FILE}"

    # --------------------------------------------------
    # 5. Validate original parameters JSON
    # --------------------------------------------------

    echo ""
    echo "=========================================="
    echo "Original CloudFormation Parameters"
    echo "=========================================="

    cat "${PARAMETERS_FILE}"

    echo ""
    echo "Validating original parameters JSON..."

    if ! jq empty "${PARAMETERS_FILE}"; then
        echo "ERROR: Original parameters file contains invalid JSON."
        exit 1
    fi

    echo "Original parameters JSON is valid."

    # --------------------------------------------------
    # 6. Prepare CloudFormation parameters
    # --------------------------------------------------

    echo ""
    echo "=========================================="
    echo "Preparing CloudFormation Parameters"
    echo "=========================================="

    PARAMETERS_WITH_AUTH=$(mktemp)

    if [ "${STACK_NAME}" = "application-stack-CloudMart" ]; then

        echo "Application stack detected."

        echo "Removing any existing:"
        echo "  - AuthToken"
        echo "  - GitHubRunId"

        echo "Adding current:"
        echo "  - AuthToken"
        echo "  - GitHubRunId"

        jq \
          --arg token "${AUTH_TOKEN}" \
          --arg run_id "${GITHUB_RUN_ID}" \
          'map(
              select(
                .ParameterKey != "AuthToken" and
                .ParameterKey != "GitHubRunId"
              )
           )
           + [
              {
                "ParameterKey": "AuthToken",
                "ParameterValue": $token
              },
              {
                "ParameterKey": "GitHubRunId",
                "ParameterValue": $run_id
              }
           ]' \
          "${PARAMETERS_FILE}" > "${PARAMETERS_WITH_AUTH}"

    else

        echo "Non-application stack detected."

        echo "Using parameters file without AuthToken."

        cp "${PARAMETERS_FILE}" "${PARAMETERS_WITH_AUTH}"

    fi

    # --------------------------------------------------
    # 7. Validate generated parameters JSON
    # --------------------------------------------------

    echo ""
    echo "=========================================="
    echo "Validating Generated Parameters"
    echo "=========================================="

    if ! jq empty "${PARAMETERS_WITH_AUTH}"; then

        echo "ERROR: Generated parameters file contains invalid JSON."

        echo ""
        echo "Generated file:"
        cat "${PARAMETERS_WITH_AUTH}"

        exit 1

    fi

    echo "Generated parameters JSON is valid."

    # --------------------------------------------------
    # 8. Display generated parameters safely
    # --------------------------------------------------

    echo ""
    echo "=========================================="
    echo "Parameters Being Passed to CloudFormation"
    echo "=========================================="

    jq '
      map(
        if .ParameterKey == "AuthToken"
        then
          .ParameterValue = "***REDACTED***"
        else
          .
        end
      )
    ' "${PARAMETERS_WITH_AUTH}"

    # --------------------------------------------------
    # 9. Verify GitHubRunId
    # --------------------------------------------------

    echo ""
    echo "Checking GitHubRunId parameter..."

    GENERATED_RUN_ID=$(jq -r '
      .[]
      | select(.ParameterKey == "GitHubRunId")
      | .ParameterValue
    ' "${PARAMETERS_WITH_AUTH}")

    if [ -z "${GENERATED_RUN_ID}" ] || [ "${GENERATED_RUN_ID}" = "null" ]; then

        echo "ERROR: GitHubRunId was not added to the parameters."

        exit 1

    fi

    echo "GitHubRunId: ${GENERATED_RUN_ID}"

    if [ "${GENERATED_RUN_ID}" != "${GITHUB_RUN_ID}" ]; then

        echo "ERROR: GitHubRunId does not match GITHUB_RUN_ID."

        echo "Expected: ${GITHUB_RUN_ID}"
        echo "Actual:   ${GENERATED_RUN_ID}"

        exit 1

    fi

    echo "GitHubRunId matches GITHUB_RUN_ID."

    # --------------------------------------------------
    # 10. Create Change Set
    # --------------------------------------------------

    echo ""
    echo "=========================================="
    echo "Creating CloudFormation Change Set"
    echo "=========================================="

    echo "Stack: ${STACK_NAME}"
    echo "Change Set: ${CHANGESET_NAME}"
    echo "Change Set Type: ${CHANGESET_TYPE}"
    echo "Template: ${TEMPLATE_S3_URL}"

    aws cloudformation create-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGESET_NAME}" \
        --change-set-type "${CHANGESET_TYPE}" \
        --template-url "${TEMPLATE_S3_URL}" \
        --parameters "file://${PARAMETERS_WITH_AUTH}" \
        --tags "file://${TAGS_FILE}" \
        --capabilities CAPABILITY_NAMED_IAM

    echo ""
    echo "Change set creation request submitted successfully."

    # --------------------------------------------------
    # 11. Wait for Change Set
    # --------------------------------------------------

    echo ""
    echo "=========================================="
    echo "Polling Change Set Status"
    echo "=========================================="

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

                if [ "${i}" -lt 20 ]; then
                    echo "Waiting 15 seconds..."
                    sleep 15
                fi

                ;;

            FAILED)

                echo "Change set creation failed."

                if echo "${REASON}" | grep -qiE \
                    "didn't contain changes|No updates are to be performed"; then

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
    # 12. Timeout protection
    # --------------------------------------------------

    if [ -z "${FINAL_STATUS}" ]; then

        echo ""
        echo "ERROR: Change set did not become ready after 5 minutes."

        exit 1

    fi

    # --------------------------------------------------
    # 13. Handle Change Set failure
    # --------------------------------------------------

    if [ "${FINAL_STATUS}" = "FAILED" ]; then

        echo ""
        echo "=========================================="
        echo "Change Set FAILED"
        echo "=========================================="

        echo "Failure reason:"
        aws cloudformation describe-change-set \
            --stack-name "${STACK_NAME}" \
            --change-set-name "${CHANGESET_NAME}" \
            --query 'StatusReason' \
            --output text

        exit 1

    fi

    # --------------------------------------------------
    # 14. Handle no changes
    # --------------------------------------------------

    if [ "${FINAL_STATUS}" = "NO_CHANGES" ]; then

        echo ""
        echo "=========================================="
        echo "No Infrastructure Changes Detected"
        echo "=========================================="

        echo "CloudFormation has no infrastructure changes to apply."

        echo "changeset_status=${FINAL_STATUS}" >> "${GITHUB_OUTPUT}"
        echo "changeset_name=${CHANGESET_NAME}" >> "${GITHUB_OUTPUT}"

        rm -f "${PARAMETERS_WITH_AUTH}"

        exit 0

    fi

    # --------------------------------------------------
    # 15. Export outputs for GitHub Actions
    # --------------------------------------------------

    echo ""
    echo "Exporting Change Set outputs..."

    echo "changeset_status=${FINAL_STATUS}" >> "${GITHUB_OUTPUT}"
    echo "changeset_name=${CHANGESET_NAME}" >> "${GITHUB_OUTPUT}"

    # --------------------------------------------------
    # 16. Print Change Set details
    # --------------------------------------------------

    echo ""
    echo "=========================================="
    echo "Change Set Summary"
    echo "=========================================="

    aws cloudformation describe-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGESET_NAME}" \
        --query 'Changes[*].{
          Action:ResourceChange.Action,
          Resource:ResourceChange.LogicalResourceId,
          Type:ResourceChange.ResourceType,
          Replacement:ResourceChange.Replacement
        }' \
        --output table || echo "No changes to display."

    echo ""
    echo "=========================================="
    echo "Change Set Processing Completed"
    echo "=========================================="

    echo "Status: ${FINAL_STATUS}"
    echo "Change Set: ${CHANGESET_NAME}"

    # --------------------------------------------------
    # 17. Cleanup
    # --------------------------------------------------

    rm -f "${PARAMETERS_WITH_AUTH}"

    echo ""
    echo "Temporary files cleaned up."
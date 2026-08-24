#!/bin/bash
set -e

S3_KEY="templates/${STACK_NAME}/run-${GITHUB_RUN_ID}/infrastructure.yaml"

echo "=========================================="
echo "Uploading CloudFormation template"
echo "=========================================="

echo "Source:"
echo "${TEMPLATE_FILE}"

echo "Destination:"
echo "s3://${CFN_BUCKET}/${S3_KEY}"

aws s3 cp \
  "${TEMPLATE_FILE}" \
  "s3://${CFN_BUCKET}/${S3_KEY}"

TEMPLATE_S3_URL="https://${CFN_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${S3_KEY}"

echo "Template uploaded successfully."

echo "template_s3_url=${TEMPLATE_S3_URL}" >> "${GITHUB_OUTPUT}"

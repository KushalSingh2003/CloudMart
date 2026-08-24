#!/bin/bash
set -e

echo "=========================================="
echo "Validating CloudFormation template"
echo "=========================================="

echo "Template: ${TEMPLATE_FILE}"

pip install cfn-lint -q

echo "Running cfn-lint..."
cfn-lint "${TEMPLATE_FILE}"

echo "Validating with AWS CloudFormation..."

aws cloudformation validate-template \
  --template-body "file://${TEMPLATE_FILE}"

echo "Template validation successful."

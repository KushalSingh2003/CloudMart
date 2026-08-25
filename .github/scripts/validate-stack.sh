#!/bin/bash
set -e

echo "=========================================="
echo "Validating CloudFormation template"
echo "=========================================="

echo "Template: ${TEMPLATE_FILE}"

pip install cfn-lint -q

echo ""
echo "Running cfn-lint..."

if cfn-lint "${TEMPLATE_FILE}"; then
    echo "cfn-lint validation passed."
else
    echo ""
    echo "ERROR: cfn-lint found validation errors."
    exit 1
fi

echo ""
echo "Validating with AWS CloudFormation..."

aws cloudformation validate-template \
  --template-body "file://${TEMPLATE_FILE}"

echo ""
echo "=========================================="
echo "Template validation successful."
echo "=========================================="

#!/bin/bash
set -e

echo "=========================================="
echo "Validating CloudFormation template"
echo "=========================================="

echo "Template: ${TEMPLATE_FILE}"

pip install cfn-lint -q

echo ""
echo "Running cfn-lint..."

LINT_OUTPUT=$(cfn-lint "${TEMPLATE_FILE}" 2>&1 || true)

echo "${LINT_OUTPUT}"

# Fail only if cfn-lint reports an actual E#### error.
if echo "${LINT_OUTPUT}" | grep -qE '(^|[[:space:]])E[0-9]{4}'; then
    echo ""
    echo "ERROR: cfn-lint found actual validation errors."
    exit 1
fi

echo ""
echo "cfn-lint validation passed."
echo "Warnings are present, but they are non-blocking."

echo ""
echo "Validating with AWS CloudFormation..."

aws cloudformation validate-template \
  --template-body "file://${TEMPLATE_FILE}"

echo ""
echo "=========================================="
echo "Template validation successful."
echo "=========================================="

GitHub Actions AWS OIDC Deployment Runbook

This runbook describes the AWS and GitHub configuration required to allow a GitHub Actions workflow to deploy CloudFormation stacks and other AWS resources using OIDC authentication.

The setup avoids storing long-term AWS access keys in GitHub.

1. Prerequisites

Before starting, make sure you have:

An AWS account with permission to create IAM resources.

A GitHub repository containing the deployment workflows.

The AWS region where the application will be deployed.

The required CloudFormation templates and deployment workflows.

The database credentials and Flask secret required by the application.

Part A — AWS Configuration

2. Create the GitHub OIDC Identity Provider

Open:

AWS Console → IAM → Identity providers → Add provider

Configure it as follows:

Setting

Value

Provider type

OpenID Connect

Provider URL

https://token.actions.githubusercontent.com

Audience

sts.amazonaws.com

Create the provider.

GitHub Actions will use this provider to obtain temporary AWS credentials through the IAM role.

3. Create the GitHub Actions IAM Role

Create an IAM role that GitHub Actions will assume.

Choose:

Trusted entity type → Custom trust policy

Use the trust policy in the next section.

After creating the role, attach the permissions required by the GitHub Actions deployment.

Depending on the project, these may include permissions for:

CloudFormation

S3

Lambda

API Gateway

IAM

EC2

RDS

EventBridge

SNS

CloudWatch

SSM Parameter Store

Cognito

Development option: AdministratorAccess can be used when appropriate for development/testing.

Production recommendation: Replace broad administrative access with only the permissions required by the deployment.

4. Configure the IAM Role Trust Policy

Open:

IAM → Roles → <GitHub Actions Role> → Trust relationships → Edit trust policy

Use the following trust policy:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::117173314907:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "ForAnyValue:StringLike": {
                    "token.actions.githubusercontent.com:sub": [
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/main",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/feature/database-initializer",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/feature/Order-API",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/feature/reporting-monitoring",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/feature/admin-login",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/fix/order-lambda",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/fix/product-lambda",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/fix/report-lambda",
                        "repo:KushalSingh2003@*/CloudMart@*:ref:refs/heads/feature/dashboard-ui"
                    ]
                }
            }
        }
    ]
}

Important: The trust policy controls which GitHub Actions identities are allowed to assume the IAM role. If additional deployment branches are created, update the trust policy accordingly.

5. Create the S3 Buckets

Create the S3 buckets required by the GitHub Actions pipeline.

5.1 CloudFormation Bucket

Create a bucket for CloudFormation templates and/or deployment artifacts.

Record its bucket name. It will be used as:

CFN_BUCKET

5.2 Lambda Code Bucket

Create a bucket for packaged Lambda code.

Record its bucket name. It will be used as:

LAMBDA_CODE_BUCKET

S3 bucket names must be globally unique.

5.3 Additional Buckets

Create any other buckets required by the application, such as report or application-data buckets, according to the project's CloudFormation templates.

Part B — GitHub Configuration

6. Add GitHub Repository Variables

Open:

GitHub → Repository → Settings → Secrets and variables → Actions → Variables

Create the following repository variables:

Variable

Value

AWS_ROLE_ARN

ARN of the GitHub Actions IAM role

CFN_BUCKET

Name of the CloudFormation bucket

LAMBDA_CODE_BUCKET

Name of the Lambda code bucket

AWS_REGION

AWS deployment region

ENVIRONMENT

Deployment environment, such as dev or prod

Example:

AWS_ROLE_ARN       = arn:aws:iam::<AWS_ACCOUNT_ID>:role/<GITHUB_ACTIONS_ROLE>
CFN_BUCKET         = <CFN_BUCKET_NAME>
LAMBDA_CODE_BUCKET = <LAMBDA_CODE_BUCKET_NAME>
AWS_REGION         = ap-south-1
ENVIRONMENT        = dev

Replace the example values with the values from your AWS account.

7. Add GitHub Repository Secrets

Open:

GitHub → Repository → Settings → Secrets and variables → Actions → Secrets

Add:

Secret

Description

DB_NAME

RDS database name

DB_USERNAME

RDS database username

DB_PASSWORD

RDS database password

FLASK_SECRET_KEY

Secret key used by the Flask application

Security

Do not place passwords, database credentials, Flask secret keys, or other sensitive values directly inside:

GitHub workflow files

CloudFormation templates

GitHub Variables

Source code

Use GitHub Secrets for sensitive values.

Part C — GitHub Actions Deployment

8. Verify the Workflow Configuration

The GitHub Actions workflow should use the configured IAM role through OIDC.

The workflow should reference:

AWS_ROLE_ARN
AWS_REGION
CFN_BUCKET
LAMBDA_CODE_BUCKET
ENVIRONMENT

The workflow should not require long-term:

AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

when OIDC authentication is configured correctly.

9. Run the GitHub Actions Workflow

Push the workflow or application changes to an authorized branch.

Then open:

GitHub → Repository → Actions

Select the deployment workflow.

Select the appropriate branch/environment if the workflow provides these options.

Run the workflow.

Check the workflow logs.

Verify that AWS authentication succeeds.

Verify that CloudFormation stacks and required resources are created or updated successfully.

Part D — Verification Checklist

AWS

GitHub OIDC provider exists.

Provider URL is https://token.actions.githubusercontent.com.

Audience is sts.amazonaws.com.

GitHub Actions IAM role exists.

IAM role has the required deployment permissions.

Trust policy is configured.

Required deployment branches are present in the trust policy.

CFN bucket exists.

Lambda Code bucket exists.

GitHub Variables

AWS_ROLE_ARN

CFN_BUCKET

LAMBDA_CODE_BUCKET

AWS_REGION

ENVIRONMENT

GitHub Secrets

DB_NAME

DB_USERNAME

DB_PASSWORD

FLASK_SECRET_KEY

Deployment

GitHub Actions can authenticate with AWS.

CloudFormation templates can be uploaded.

Lambda packages can be uploaded.

CloudFormation stacks deploy successfully.

Required AWS resources are created/updated.

Part E — Troubleshooting

GitHub Actions Cannot Assume the IAM Role

Check:

The GitHub OIDC provider exists in the correct AWS account.

The provider URL is exactly:

https://token.actions.githubusercontent.com

The audience is:

sts.amazonaws.com

AWS_ROLE_ARN points to the correct IAM role.

The branch running the workflow is allowed by the IAM role trust policy.

The repository and branch values in the trust policy match the workflow's GitHub repository and branch.

The workflow has the required OIDC permission:

permissions:
  id-token: write
  contents: read

CloudFormation Cannot Upload Templates

Check:

CFN_BUCKET is correct.

The IAM role has the required S3 permissions.

The bucket exists in the expected AWS account.

The workflow is using the correct AWS region.

Lambda Deployment Fails

Check:

LAMBDA_CODE_BUCKET is correct.

The Lambda package was uploaded successfully.

The IAM role has the required Lambda and S3 permissions.

The CloudFormation parameters reference the correct bucket/key.

Database Configuration Fails

Check that the following GitHub Secrets exist and contain the correct values:

DB_NAME
DB_USERNAME
DB_PASSWORD

Do not print these values in GitHub Actions logs.

Part F — Architecture Overview

                         GitHub Repository
                                │
                                │ GitHub Actions
                                ▼
                    GitHub OIDC Provider
              token.actions.githubusercontent.com
                                │
                                │ AssumeRoleWithWebIdentity
                                ▼
                     AWS IAM Deployment Role
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        CloudFormation         S3              Lambda
              │                 │                 │
              └──────────── AWS Deployment ───────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
         API Gateway           RDS           EventBridge
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
             SNS           CloudWatch            SSM
                                │
                                ▼
                             Cognito

Final Setup Summary

The complete deployment flow is:

1. Create GitHub OIDC Provider
              ↓
2. Create IAM Deployment Role
              ↓
3. Configure Trust Policy
              ↓
4. Attach Required IAM Permissions
              ↓
5. Create CFN Bucket
              ↓
6. Create Lambda Code Bucket
              ↓
7. Add GitHub Repository Variables
              ↓
8. Add GitHub Repository Secrets
              ↓
9. Configure GitHub Actions Workflow
              ↓
10. Run Deployment
              ↓
11. Verify CloudFormation Resources

Once these steps are completed, GitHub Actions can authenticate with AWS using OIDC and deploy the CloudMart infrastructure without storing permanent AWS access keys in GitHub.
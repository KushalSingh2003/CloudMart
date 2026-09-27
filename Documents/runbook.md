CloudMart Deployment Runbook (Condensed)
Overview
Serverless e-commerce app on AWS (CloudFormation + GitHub Actions/OIDC). Components: VPC (2 AZs), RDS MySQL, Lambda, API Gateway + Lambda Authorizer, EventBridge, SNS, S3, SSM Parameter Store, EC2 Flask dashboard, VPC Endpoints.

Deployment Order
Network – VPC, subnets, route tables, security groups, VPC endpoints (SSM, CloudWatch Logs/Monitoring, EventBridge, S3 Gateway)
Data – RDS MySQL; exports endpoint/credentials to SSM (/cloudmart/<env>/db-*)
Application – Lambdas (DB Init, Product, Order, Check Stock, Report, Authorizer), API Gateway, EventBridge/SNS, IAM
Dashboard – Dashboard stack infra
EC2 (manual, post-deploy) – for DB access/admin
Prerequisites
AWS account/region set; GitHub OIDC connected with required CFN/S3/Lambda/IAM permissions; S3 buckets exist; parameter files populated; Lambda packages built via CI/CD.

Auth Model
No Cognito/JWT. Custom user_id + token auth via Customers table, roles CUSTOMER/ADMIN. Lambda Authorizer validates requests and blocks cross-customer order access.

Manual EC2 Setup
SG: SSH (22) restricted via Prefix List; outbound MySQL (3306) to RDS
RDS SG must allow 3306 from EC2 SG
Flow: Your PC → SSH → EC2 → MariaDB client :3306 → RDS
Install MariaDB client, connect: mariadb -h <endpoint> -P 3306 -u <user> -p
API Testing
Products: GET/POST/PUT/PATCH/DELETE
Orders: create, get, update status, cancel (verify: status→cancelled, stock restored, no cross-customer access)
Reporting
Report Lambda runs on schedule → reads RDS → uploads CSV to reports/sales-report-YYYY-MM-DD.csv in versioned, non-public S3 bucket.

Low-Stock Notifications
Stock < threshold → EventBridge rule → SNS → email subscriber.

Dashboard
EC2 + Flask, reachable, pulls data from RDS.

Post-Deployment Checklist
 Stacks CREATE/UPDATE_COMPLETE
 RDS up
 DB Init ran, tables exist
 Lambdas deployed
 API Gateway reachable
 Auth works
 Product/Order/Stock APIs work
 EventBridge/SNS work
 Report Lambda uploads to S3
 EC2↔RDS connectivity
 MariaDB client works
 Dashboard accessible
 CloudWatch logging active
Troubleshooting
Issue	Check
Lambda→RDS fails	Lambda in private subnets; RDS SG allows 3306 from Lambda SG; SSM creds correct
EC2→RDS fails	EC2 SG outbound MySQL; RDS SG allows EC2 SG; same VPC; client installed
SSH fails	Public IP present; port 22 open; correct Prefix List/key
Report missing	EventBridge execution; Lambda logs; RDS connectivity; S3 permissions/bucket/filename
Dashboard down	EC2 status/IAM role; S3 access; Flask status; logs; RDS connectivity; /etc/cloudmart-dashboard.env
Rollback
Reports bucket has DeletionPolicy/UpdateReplacePolicy: Retain — survives stack deletion. Verify retained resources before redeploying.


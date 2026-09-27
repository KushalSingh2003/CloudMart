# CloudMart

# CloudMart

CloudMart is a serverless e-commerce application built on AWS. The project provides product management, order processing, stock management, user authentication, reporting, notifications, and a web dashboard.

## Architecture

```text
                         Internet
                            |
                     API Gateway
                            |
                  Lambda Authorizer
                            |
              ┌─────────────┴─────────────┐
              │                           │
        Product Lambda              Order Lambda
              │                           │
              └──────────────┬────────────┘
                             |
                         RDS MySQL
                             |
                  ┌──────────┴──────────┐
                  │                     │
            Report Lambda          EventBridge
                  │                     │
                  ▼                     ▼
             S3 Reports               SNS
                                        |
                                      Email

                    Public EC2
                       |
                Flask Dashboard
                       |
                    RDS MySQL
```

## AWS Services

* **Amazon VPC** — network isolation
* **Private Subnets** — Lambda and private resources
* **Public Subnet** — dashboard EC2
* **Amazon RDS MySQL** — application database
* **AWS Lambda** — backend services
* **API Gateway** — REST API
* **Lambda Authorizer** — validates the user ID and token supplied with API requests
* **Amazon EventBridge** — scheduled and event-driven processing
* **Amazon SNS** — low-stock notifications
* **Amazon S3** — Lambda packages and generated reports
* **AWS Systems Manager Parameter Store** — database configuration and credentials
* **Amazon EC2** — Flask dashboard
* **Amazon CloudWatch** — logs and monitoring
* **GitHub Actions** — CI/CD
* **AWS CloudFormation** — infrastructure as code

## Lambda Functions

### DB Init Lambda

The DB Init Lambda initializes the CloudMart database by creating the required database tables and schema in Amazon RDS MySQL.

It ensures that the database structure is available before the application APIs are used.

### Product Lambda

Handles product operations such as creating, retrieving, updating, and deleting products.

### Order Lambda

Handles order creation and order management.

It also handles order cancellation and the associated stock update.

### Check Stock Lambda

Checks product stock availability during order processing.

### Report Lambda

Generates daily sales reports from RDS and uploads them to the Reports S3 bucket.

### Authorizer Lambda

Validates the `user_id` and `token` supplied with API requests and determines whether the user is authorized to perform the requested operation.

## Database

CloudMart uses **Amazon RDS MySQL**.

Main application tables include:

* Customers
* Products
* Categories
* Orders

The application retrieves database configuration from **SSM Parameter Store**.

## Authentication and Authorization

CloudMart uses a **user ID and token-based authentication mechanism**.

A user is first added to the **Customers** table. The customer record contains the user's ID, token, and role.

When making an API request, the client provides the:

```text
user_id
token
```

The Lambda Authorizer validates these values against the Customers table and determines the user's permissions.

Supported roles include:

* `CUSTOMER`
* `ADMIN`

The authorization layer also ensures that customers can only access resources they are permitted to access.

## Reporting

The Report Lambda is triggered by a scheduler and generates a daily CSV sales report.

Example:

```text
sales-report-2026-09-28.csv
```

Reports are stored in the Reports S3 bucket.

The bucket has:

* Versioning enabled
* Public access blocked
* Retention enabled to prevent accidental deletion when the CloudFormation stack is deleted

## Notifications

EventBridge is used for application events and scheduled processing.

Low-stock events trigger the configured SNS notification flow, which sends notifications through the configured email subscription.

## Networking

The VPC contains:

* One public subnet
* Two private subnets
* Internet Gateway
* Public and private route tables
* Security groups
* VPC endpoints

The two private subnets are located in different Availability Zones to provide high availability.

Backend Lambda functions operate in the private subnets, while the Flask dashboard EC2 instance is deployed in the public subnet.

## CI/CD

GitHub Actions is used to deploy the infrastructure and application.

AWS authentication from GitHub Actions uses **OIDC**, avoiding long-lived AWS access keys.

CloudFormation stacks are deployed in the following order:

```text
1. Network Stack
2. Data Stack
3. Application Stack
4. Dashboard Stack
```

## Testing

API testing can be performed using Postman or curl.

Important test cases:

* Product CRUD
* User authentication
* Customer authorization
* Admin authorization
* Order creation
* Order retrieval
* Order cancellation
* Stock update after cancellation
* Low-stock notification
* Daily report generation
* Dashboard access

## Deployment

Refer to [`DEPLOYMENT_RUNBOOK.md`](./DEPLOYMENT_RUNBOOK.md) for the complete deployment and validation procedure.

## Security

The project uses:

* Private subnets for backend resources
* Security groups for network-level access control
* User ID and token-based authorization
* Lambda Authorizer
* SSM Parameter Store for database credentials
* S3 public-access blocking
* VPC endpoints for private AWS service access
* GitHub Actions OIDC authentication

## Project Structure

```text
CloudMart/
├── lambdas/
│   ├── db-init/
│   ├── product/
│   ├── order/
│   ├── check-stock/
│   ├── report/
│   └── authorizer/
├── cloudformation/
│   ├── network/
│   ├── data/
│   ├── application/
│   └── dashboard/
├── dashboard/
├── .github/
│   └── workflows/
├── README.md
└── DEPLOYMENT_RUNBOOK.md
```

## Deployment Status

The project is deployed using AWS CloudFormation and GitHub Actions.

For deployment, testing, troubleshooting, and validation steps, follow the deployment runbook.

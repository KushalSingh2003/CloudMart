# ☁️ CloudMart — AWS Deployment & Operations Runbook

> **Confidential — Not for Public Consumption or Distribution**

CloudMart is a cloud-native e-commerce application deployed on AWS. It uses **CloudFormation, GitHub Actions/OIDC, API Gateway, Lambda, RDS MySQL, S3, EventBridge, CloudWatch, SNS, and a Flask dashboard on EC2**.

---

# 1. 📄 Document Overview

This document provides the information required to understand, deploy, validate, operate, and troubleshoot CloudMart.

It covers:

- Project architecture
- Repository structure
- CI/CD deployment
- API workflow
- Report generation
- Dashboard
- Monitoring and alerts
- Post-deployment validation
- Troubleshooting and recovery

## Core AWS Components

| Component | Technology |
|---|---|
| Infrastructure | CloudFormation |
| CI/CD | GitHub Actions + OIDC |
| Backend | API Gateway + Lambda |
| Database | RDS MySQL |
| Reports | EventBridge + Lambda + S3 |
| Monitoring | CloudWatch + SNS |
| Dashboard | Flask + EC2 |

**AWS Region:** `ap-south-1`

---

# 2. 📁 Repository Structure

```text
CloudMart/
│
├── .github/
│   └── workflows/
│
├── cloudformation/
│   ├── network.yaml
│   ├── data.yaml
│   ├── application.yaml
│   └── dashboard.yaml
│
├── lambdas/
│   ├── authorizer/
│   ├── product/
│   ├── order/
│   ├── checkstock/
│   ├── report/
│   └── dbinit/
│
├── dashboard/
│   ├── app.py
│   ├── templates/
│   └── static/
│
├── database/
│   └── schema.sql
│
└── README.md
```

---

# 3. 🏗️ AWS Architecture — High Level

CloudMart has four main operational workflows.

---

## 3.1 🔄 GitHub CI/CD Workflow

```text
Developer
   → GitHub
   → GitHub Actions
   → GitHub OIDC
   → IAM Deployment Role
   → STS Temporary Credentials
   → CloudFormation
   → AWS Infrastructure
```

**Purpose:** Automatically deploy CloudMart infrastructure and application changes without storing permanent AWS access keys in GitHub.

---

## 3.2 🌐 API Gateway Workflow

```text
Client / Postman
   → API Gateway
   → Lambda Authorizer
   → Product / Order Lambda
   → RDS MySQL
```

**Authorization path:**

```text
Request
   → Lambda Authorizer
      → Allow → Target Lambda → RDS
      → Deny  → Authorization Failure
```

> `GET /products` and `GET /products/{id}` are public product routes according to the current implementation.

---

## 3.3 📊 Report Lambda Workflow

```text
EventBridge
   → Report Lambda
   → SSM Parameter Store
   → RDS MySQL
   → Generate CSV Reports
   → S3 Reports Bucket
   → Flask Dashboard
```

The Report Lambda generates the daily detail and summary reports.

For the report date, the application uses the **India calendar day** and converts its boundaries from IST to UTC before querying RDS.

```text
Report Date
   → IST Start / End
   → UTC Start / End
   → RDS Query
```

Customer details are obtained through:

```text
Orders.user_id
      ↓
Customers.user_id
      ↓
Customer Name / Email
```

---

## 3.4 🖥️ Dashboard Workflow

```text
Admin
   → EC2
   → Flask Dashboard
   → RDS MySQL
```

The dashboard also accesses report files from S3 and displays operational information such as:

```text
Products
Customers
Orders
Revenue
Order Trends
Best-Selling Products
Low Stock
Reports
```

---

# 4. 🎯 High-Level Design

The following workflows show how the major CloudMart components interact.

### GitHub Deployment

```text
Developer → GitHub → Actions → OIDC → IAM → STS → CloudFormation → AWS
```

### API Request

```text
Client → API Gateway → Authorizer → Product/Order Lambda → RDS
```

### Daily Reporting

```text
EventBridge → Report Lambda → RDS → CSV → S3 → Dashboard
```

### Dashboard

```text
Admin → EC2 → Flask → RDS
                  └──→ S3 Reports
```

### Monitoring

```text
Lambda / Application → CloudWatch → Alarm → SNS
```

> **Important:** API Gateway is an AWS-managed regional service and is not deployed inside the VPC. RDS remains in private networking, while required Lambda functions use the configured VPC/networking.

---

# 5. 🔐 Important Security Rules

1. Never commit passwords, tokens, access keys, or secret keys to GitHub.
2. Use GitHub OIDC and temporary AWS credentials for CI/CD.
3. Keep RDS private and restrict database access through security groups.
4. Store application secrets/configuration in the configured AWS parameter/secret mechanism.
5. Use least-privilege IAM and enforce role/customer-based access to protected APIs and data.

---

# 6. 🚀 CI/CD Deployment Procedure

## 6.1 Push Code

```bash
git status
git add .
git commit -m "Deploy CloudMart updates"
git push origin main
```

## 6.2 Deployment Flow

```text
Push
  → GitHub Actions
  → Validate Templates
  → Request OIDC Token
  → Assume IAM Role
  → Get STS Credentials
  → Deploy CloudFormation
  → Initialize Database
  → Deployment Result
```

---

# 7. 📦 Expected Stack Deployment Order

| Order | Stack | Purpose |
|---:|---|---|
| 1 | **Network** | VPC, subnets, routes and security groups |
| 2 | **Data** | RDS MySQL and data resources |
| 3 | **Application** | Lambda, API Gateway, Authorizer, EventBridge, SNS and application resources |
| 4 | **Dashboard** | EC2 and Flask dashboard |

```text
Network → Data → Application → Dashboard
```

---

# 8. ✅ Post-Deployment Validation

### Infrastructure

- [ ] All four stacks are `CREATE_COMPLETE` / `UPDATE_COMPLETE`.
- [ ] Lambda functions and API Gateway are available.
- [ ] RDS is available.
- [ ] S3, EventBridge, CloudWatch and SNS resources exist.

### APIs

- [ ] Authentication works for protected APIs.
- [ ] Public product GET routes work.
- [ ] Product CRUD works according to permissions.
- [ ] Order creation/retrieval/update works.
- [ ] Customer ownership restrictions work.
- [ ] Inventory changes correctly.

### Reporting & Dashboard

- [ ] EventBridge triggers Report Lambda.
- [ ] Daily reports are generated and uploaded to S3.
- [ ] Dashboard displays current data.
- [ ] Report download works.
- [ ] CloudWatch alarms/SNS notifications work.

---

# 9. 📦 Inventory and Alert Validation

```text
Stock Change
   → CloudWatch Metric
   → Alarm
   → SNS Notification
```

Verify:

- Normal stock works correctly.
- Low-stock threshold triggers the expected metric/alarm.
- Zero stock triggers the expected out-of-stock behavior.
- Dashboard inventory matches RDS.

---

# 10. 📊 Report Generation

```text
EventBridge
   → Report Lambda
   → RDS MySQL
   → Detail + Summary CSV
   → S3
   → Dashboard
```

The report uses the India calendar day:

```text
07 Oct 00:00 IST → 06 Oct 18:30 UTC
08 Oct 00:00 IST → 07 Oct 18:30 UTC
```

The database query uses:

```sql
WHERE created_at >= start_utc
  AND created_at < end_utc
```

Customer information is obtained using:

```sql
Orders.user_id = Customers.user_id
```

---

# 11. 🖥️ Flask Dashboard Operations

The dashboard is hosted on EC2 and provides:

- Product/customer/order metrics
- Revenue and order trends
- Best-selling products
- Low-stock information
- CloudWatch/operational information
- Daily report access

For dashboard issues, check:

```text
EC2 → Flask Service → Application Logs → RDS / S3 / IAM
```

---

# 12. 📈 Monitoring and Logs

```text
Lambda / Application
        ↓
CloudWatch
   ┌────┴────┐
   ↓         ↓
 Logs      Metrics
             ↓
           Alarm
             ↓
            SNS
```

Use CloudWatch to investigate Lambda errors, application metrics, inventory alarms, and report-generation failures.

---

# 13. 🛠️ Troubleshooting Runbook

| Problem | Check |
|---|---|
| **GitHub Actions failed** | Workflow logs, OIDC, IAM role, permissions and parameters |
| **OIDC failure** | OIDC provider, trust policy, repository/branch and role ARN |
| **CloudFormation failed** | First failed resource in Stack Events |
| **Lambda → RDS failure** | VPC, subnet, security groups, RDS and SSM |
| **API 401** | Token, Authorization header, authorizer logs and API Gateway configuration |
| **API 5xx** | Lambda logs, permissions, environment variables and RDS |
| **Alarm not triggering** | Metric, dimensions, threshold and evaluation period |
| **SNS not received** | Topic, subscription and alarm state |
| **Report missing** | EventBridge, Lambda logs, RDS and S3 permissions |
| **Dashboard unavailable** | EC2, Flask service, security groups and application logs |

---

# 14. 🔄 Rollback / Recovery

1. Identify the first failed resource.
2. Review CloudFormation and GitHub Actions logs.
3. Fix the root cause or revert the problematic commit.
4. Retry/rollback the stack as appropriate.
5. Repeat post-deployment validation.

> Avoid manually deleting dependent resources unless the impact is understood.

---

# 15. 📋 Final Checklist

### Deployment

- [ ] OIDC and IAM configured
- [ ] Network stack deployed
- [ ] Data stack deployed
- [ ] Application stack deployed
- [ ] Dashboard stack deployed

### Application

- [ ] APIs tested
- [ ] Authentication tested
- [ ] Orders/inventory tested
- [ ] Reports tested
- [ ] Dashboard tested
- [ ] Monitoring/SNS tested

---

# 16. 🏁 Final Architecture Summary

```text
                 ┌──────────────────┐
                 │    Developer     │
                 └────────┬─────────┘
                          ↓
                    GitHub Actions
                          ↓
                       OIDC/IAM
                          ↓
                    CloudFormation
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   API Gateway       EventBridge          EC2
        ↓                 ↓                 ↓
   Authorizer       Report Lambda        Flask
        ↓                 ↓              /    \
 Product/Order         S3             RDS     S3
    Lambda
        ↓
     RDS MySQL

CloudWatch → Alarms → SNS
```

> **Confidential — Not for Public Consumption or Distribution**

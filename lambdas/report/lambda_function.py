# import os
# import csv
# import io
# import boto3
# import pymysql
# from datetime import datetime, timezone


# ssm = boto3.client("ssm")
# s3 = boto3.client("s3")


# def get_parameter(parameter_name):
#     response = ssm.get_parameter(
#         Name=parameter_name,
#         WithDecryption=True
#     )
#     return response["Parameter"]["Value"]


# def get_db_connection():
#     host = get_parameter(os.environ["DB_HOST_PARAMETER"])
#     port = int(get_parameter(os.environ["DB_PORT_PARAMETER"]))
#     database = get_parameter(os.environ["DB_NAME_PARAMETER"])
#     username = get_parameter(os.environ["DB_USER_PARAMETER"])
#     password = get_parameter(os.environ["DB_PASSWORD_PARAMETER"])

#     return pymysql.connect(
#         host=host,
#         port=port,
#         user=username,
#         password=password,
#         database=database,
#         cursorclass=pymysql.cursors.DictCursor,
#         connect_timeout=10
#     )


# def generate_report(connection):
#     """
#     Generate a daily order report.
#     """

#     query = """
#         SELECT
#             o.order_id,
#             o.user_id,
#             c.name AS customer_name,
#             c.email AS customer_email,
#             o.total_amount,
#             o.status,
#             o.created_at,
#             o.changed_at,
#             o.cancelled_at,
#             o.cancel_reason
#         FROM Orders o
#         LEFT JOIN Customers c
#             ON o.user_id = c.user_id
#         WHERE DATE(o.created_at) = CURDATE()
#         ORDER BY o.created_at ASC
#     """

#     with connection.cursor() as cursor:
#         cursor.execute(query)
#         return cursor.fetchall()


# def create_csv(rows):
#     output = io.StringIO()

#     fieldnames = [
#         "order_id",
#         "user_id",
#         "customer_name",
#         "customer_email",
#         "total_amount",
#         "status",
#         "created_at",
#         "changed_at",
#         "cancelled_at",
#         "cancel_reason"
#     ]

#     writer = csv.DictWriter(
#         output,
#         fieldnames=fieldnames
#     )

#     writer.writeheader()

#     for row in rows:
#         writer.writerow(row)

#     return output.getvalue()


# def upload_report(csv_content):
#     bucket_name = os.environ["REPORTS_BUCKET_NAME"]

#     current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

#     key = f"reports/daily-report-{current_date}.csv"

#     s3.put_object(
#         Bucket=bucket_name,
#         Key=key,
#         Body=csv_content.encode("utf-8"),
#         ContentType="text/csv"
#     )

#     return key


# def lambda_handler(event, context):

#     connection = None

#     try:
#         print("Daily Report Lambda started")

#         connection = get_db_connection()

#         print("Connected to RDS")

#         rows = generate_report(connection)

#         print(f"Orders found for today: {len(rows)}")

#         csv_content = create_csv(rows)

#         report_key = upload_report(csv_content)

#         print(
#             f"Report uploaded successfully: "
#             f"s3://{os.environ['REPORTS_BUCKET_NAME']}/{report_key}"
#         )

#         return {
#             "statusCode": 200,
#             "message": "Daily report generated successfully",
#             "report_key": report_key,
#             "records": len(rows)
#         }

#     except Exception as e:

#         print(f"Report generation failed: {str(e)}")

#         raise

#     finally:

#         if connection:
#             connection.close()

#             print("Database connection closed")
import os
import csv
import io
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import boto3
import pymysql


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm = boto3.client("ssm")
s3 = boto3.client("s3")
cloudwatch = boto3.client("cloudwatch")

METRIC_NAMESPACE = "CloudMart/ReportLambda"


# ============================================================
# SSM
# ============================================================

def get_parameter(parameter_name: str) -> str:
    response = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection() -> pymysql.connections.Connection:

    host = get_parameter(
        os.environ["DB_HOST_PARAMETER"]
    )

    port = int(
        get_parameter(
            os.environ["DB_PORT_PARAMETER"]
        )
    )

    database = get_parameter(
        os.environ["DB_NAME_PARAMETER"]
    )

    username = get_parameter(
        os.environ["DB_USER_PARAMETER"]
    )

    password = get_parameter(
        os.environ["DB_PASSWORD_PARAMETER"]
    )

    return pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )


# ============================================================
# GET DAILY ORDERS
# ============================================================

def generate_report(
    connection: pymysql.connections.Connection,
    report_date: str
) -> List[Dict[str, Any]]:

    query = """
        SELECT
            o.order_id,
            o.user_id,
            c.name AS customer_name,
            c.email AS customer_email,
            o.total_amount,
            o.status,
            o.created_at,
            o.changed_at,
            o.cancelled_at,
            o.cancel_reason

        FROM Orders o

        LEFT JOIN Customers c
            ON o.user_id = c.user_id

        WHERE DATE(o.created_at) = %s

        ORDER BY o.created_at ASC
    """

    with connection.cursor() as cursor:

        cursor.execute(
            query,
            (report_date,)
        )

        return cursor.fetchall()


# ============================================================
# GET BEST-SELLING PRODUCT
# ============================================================

def get_best_selling_product(
    connection: pymysql.connections.Connection,
    report_date: str
) -> Dict[str, Any]:

    query = """
        SELECT
            oi.product_name,
            SUM(oi.quantity) AS quantity_sold

        FROM Orders_Items oi

        INNER JOIN Orders o
            ON oi.order_id = o.order_id

        WHERE DATE(o.created_at) = %s
          AND LOWER(o.status) != 'cancelled'

        GROUP BY oi.product_id, oi.product_name

        ORDER BY quantity_sold DESC

        LIMIT 1
    """

    with connection.cursor() as cursor:

        cursor.execute(
            query,
            (report_date,)
        )

        result = cursor.fetchone()

        if not result:
            return {
                "product_name": "N/A",
                "quantity_sold": 0
            }

        return {
            "product_name": result["product_name"],
            "quantity_sold": int(result["quantity_sold"])
        }


# ============================================================
# CSV VALUE FORMATTER
# ============================================================

def format_csv_value(value: Any) -> Any:

    if value is None:
        return "N/A"

    if isinstance(value, Decimal):
        return f"{value:.2f}"

    if isinstance(value, datetime):
        return value.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    return value


# ============================================================
# CREATE DETAIL CSV
# ============================================================

def create_csv(
    rows: List[Dict[str, Any]]
) -> str:

    output = io.StringIO()

    fieldnames = [
        "Order ID",
        "Customer ID",
        "Customer Name",
        "Customer Email",
        "Order Amount",
        "Status",
        "Created At",
        "Changed At",
        "Cancelled At",
        "Cancellation Reason"
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in rows:

        formatted_row = {
            "Order ID": format_csv_value(
                row.get("order_id")
            ),

            "Customer ID": format_csv_value(
                row.get("user_id")
            ),

            "Customer Name": format_csv_value(
                row.get("customer_name")
            ),

            "Customer Email": format_csv_value(
                row.get("customer_email")
            ),

            "Order Amount": format_csv_value(
                row.get("total_amount")
            ),

            "Status": format_csv_value(
                row.get("status")
            ),

            "Created At": format_csv_value(
                row.get("created_at")
            ),

            "Changed At": format_csv_value(
                row.get("changed_at")
            ),

            "Cancelled At": format_csv_value(
                row.get("cancelled_at")
            ),

            "Cancellation Reason": format_csv_value(
                row.get("cancel_reason")
            )
        }

        writer.writerow(formatted_row)

    return output.getvalue()


# ============================================================
# GENERATE SUMMARY
# ============================================================

def generate_summary(
    rows: List[Dict[str, Any]],
    best_selling_product: Dict[str, Any]
) -> Dict[str, Any]:

    total_orders = len(rows)

    completed = [
        row for row in rows
        if str(
            row.get("status", "")
        ).lower() == "completed"
    ]

    cancelled = [
        row for row in rows
        if str(
            row.get("status", "")
        ).lower() == "cancelled"
    ]

    # Revenue is calculated only from completed orders
    total_sales = sum(
        (
            Decimal(
                str(
                    row.get("total_amount") or "0"
                )
            )
            for row in completed
        ),
        Decimal("0")
    )

    average_order_value = (
        total_sales / len(completed)
        if completed
        else Decimal("0")
    )

    cancellation_rate = (
        len(cancelled) / total_orders * 100
        if total_orders
        else 0
    )

    # Status breakdown
    status_breakdown: Dict[str, int] = {}

    for row in rows:

        status = str(
            row.get("status") or "N/A"
        ).upper()

        status_breakdown[status] = (
            status_breakdown.get(status, 0) + 1
        )

    return {
        "total_orders": total_orders,

        "total_sales": (
            f"{total_sales:.2f}"
        ),

        "average_order_value": (
            f"{average_order_value:.2f}"
        ),

        "cancelled_orders": len(cancelled),

        "cancellation_rate": (
            f"{cancellation_rate:.2f}%"
        ),

        "best_selling_product": (
            best_selling_product["product_name"]
        ),

        "best_selling_quantity": (
            best_selling_product["quantity_sold"]
        ),

        "status_breakdown": status_breakdown
    }


# ============================================================
# CREATE SUMMARY CSV
# ============================================================

def create_summary_csv(
    summary: Dict[str, Any],
    report_date: str
) -> str:

    output = io.StringIO()

    writer = csv.writer(output)

    # --------------------------------------------------------
    # Report Header
    # --------------------------------------------------------

    writer.writerow([
        "CLOUDMART DAILY SALES SUMMARY"
    ])

    writer.writerow([
        "Report Date",
        report_date
    ])

    writer.writerow([])

    # --------------------------------------------------------
    # Business Metrics
    # --------------------------------------------------------

    writer.writerow([
        "Metric",
        "Value"
    ])

    writer.writerow([
        "Total Orders",
        summary["total_orders"]
    ])

    writer.writerow([
        "Total Sales",
        summary["total_sales"]
    ])

    writer.writerow([
        "Average Order Value",
        summary["average_order_value"]
    ])

    writer.writerow([
        "Cancelled Orders",
        summary["cancelled_orders"]
    ])

    writer.writerow([
        "Cancellation Rate",
        summary["cancellation_rate"]
    ])

    writer.writerow([])

    # --------------------------------------------------------
    # Best Selling Product
    # --------------------------------------------------------

    writer.writerow([
        "BEST-SELLING PRODUCT"
    ])

    writer.writerow([
        "Product",
        "Quantity Sold"
    ])

    writer.writerow([
        summary["best_selling_product"],
        summary["best_selling_quantity"]
    ])

    writer.writerow([])

    # --------------------------------------------------------
    # Order Status
    # --------------------------------------------------------

    writer.writerow([
        "ORDER STATUS"
    ])

    writer.writerow([
        "Status",
        "Order Count"
    ])

    for status, count in sorted(
        summary["status_breakdown"].items()
    ):

        writer.writerow([
            status,
            count
        ])

    return output.getvalue()


# ============================================================
# UPLOAD REPORTS TO S3
# ============================================================

def upload_report(
    csv_content: str,
    summary_csv_content: str,
    report_date: str
) -> Tuple[str, str]:

    bucket_name = os.environ[
        "REPORTS_BUCKET_NAME"
    ]

    detail_key = (
        f"reports/daily-report-{report_date}.csv"
    )

    summary_key = (
        f"reports/daily-summary-{report_date}.csv"
    )

    # Detail report
    s3.put_object(
        Bucket=bucket_name,
        Key=detail_key,
        Body=csv_content.encode("utf-8"),
        ContentType="text/csv"
    )

    # Summary report
    s3.put_object(
        Bucket=bucket_name,
        Key=summary_key,
        Body=summary_csv_content.encode("utf-8"),
        ContentType="text/csv"
    )

    return detail_key, summary_key


# ============================================================
# CLOUDWATCH METRIC
# ============================================================

def publish_metric(
    metric_name: str,
    value: float = 1.0
) -> None:

    try:

        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,

            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": "Count"
                }
            ]
        )

    except Exception:

        logger.error(
            "Failed to publish CloudWatch metric."
        )


# ============================================================
# LAMBDA HANDLER
# ============================================================

def lambda_handler(
    event: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:

    connection = None

    try:

        logger.info(
            "Daily Report Lambda started"
        )

        report_date = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d")

        # ----------------------------------------------------
        # Database
        # ----------------------------------------------------

        connection = get_db_connection()

        logger.info(
            "Connected to RDS"
        )

        # ----------------------------------------------------
        # Orders
        # ----------------------------------------------------

        rows = generate_report(
            connection,
            report_date
        )

        logger.info(
            f"Orders found for "
            f"{report_date}: {len(rows)}"
        )

        # ----------------------------------------------------
        # Detail CSV
        # ----------------------------------------------------

        logger.info(
            "Creating detail CSV"
        )

        csv_content = create_csv(rows)

        # ----------------------------------------------------
        # Best Selling Product
        # ----------------------------------------------------

        logger.info(
            "Calculating best-selling product"
        )

        best_selling_product = (
            get_best_selling_product(
                connection,
                report_date
            )
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        summary = generate_summary(
            rows,
            best_selling_product
        )

        summary_csv_content = (
            create_summary_csv(
                summary,
                report_date
            )
        )

        # ----------------------------------------------------
        # S3
        # ----------------------------------------------------

        logger.info(
            "Uploading reports to S3"
        )

        detail_key, summary_key = upload_report(
            csv_content,
            summary_csv_content,
            report_date
        )

        logger.info(
            "Reports uploaded successfully"
        )

        # ----------------------------------------------------
        # CloudWatch Metrics
        # ----------------------------------------------------

        publish_metric(
            "ReportGenerationSuccess"
        )

        publish_metric(
            "ReportRowsGenerated",
            float(len(rows))
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {
            "statusCode": 200,

            "message":
                "Daily report generated successfully",

            "report_key":
                detail_key,

            "summary_key":
                summary_key,

            "records":
                len(rows),

            "best_selling_product":
                summary["best_selling_product"],

            "best_selling_quantity":
                summary["best_selling_quantity"]
        }

    except pymysql.MySQLError:

        publish_metric(
            "ReportGenerationFailure"
        )

        logger.error(
            "Database error during report generation."
        )

        raise

    except Exception:

        publish_metric(
            "ReportGenerationFailure"
        )

        logger.error(
            "Report generation failed."
        )

        raise

    finally:

        if connection:

            connection.close()

            logger.info(
                "Database connection closed"
            )
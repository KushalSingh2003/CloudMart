import os
import csv
import io
import boto3
import pymysql
from datetime import datetime, timezone


ssm = boto3.client("ssm")
s3 = boto3.client("s3")


def get_parameter(parameter_name):
    response = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )
    return response["Parameter"]["Value"]


def get_db_connection():
    host = get_parameter(os.environ["DB_HOST_PARAMETER"])
    port = int(get_parameter(os.environ["DB_PORT_PARAMETER"]))
    database = get_parameter(os.environ["DB_NAME_PARAMETER"])
    username = get_parameter(os.environ["DB_USER_PARAMETER"])
    password = get_parameter(os.environ["DB_PASSWORD_PARAMETER"])

    return pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )


def generate_report(connection):
    """
    Generate a daily order report.
    """

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
        WHERE DATE(o.created_at) = CURDATE()
        ORDER BY o.created_at ASC
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def create_csv(rows):
    output = io.StringIO()

    fieldnames = [
        "order_id",
        "user_id",
        "customer_name",
        "customer_email",
        "total_amount",
        "status",
        "created_at",
        "changed_at",
        "cancelled_at",
        "cancel_reason"
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    return output.getvalue()


def upload_report(csv_content):
    bucket_name = os.environ["REPORTS_BUCKET_NAME"]

    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    key = f"reports/daily-report-{current_date}.csv"

    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=csv_content.encode("utf-8"),
        ContentType="text/csv"
    )

    return key


def lambda_handler(event, context):

    connection = None

    try:
        print("Daily Report Lambda started")

        connection = get_db_connection()

        print("Connected to RDS")

        rows = generate_report(connection)

        print(f"Orders found for today: {len(rows)}")

        csv_content = create_csv(rows)

        report_key = upload_report(csv_content)

        print(
            f"Report uploaded successfully: "
            f"s3://{os.environ['REPORTS_BUCKET_NAME']}/{report_key}"
        )

        return {
            "statusCode": 200,
            "message": "Daily report generated successfully",
            "report_key": report_key,
            "records": len(rows)
        }

    except Exception as e:

        print(f"Report generation failed: {str(e)}")

        raise

    finally:

        if connection:
            connection.close()

            print("Database connection closed")
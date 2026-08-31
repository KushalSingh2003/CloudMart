import os
import json
import boto3
import pymysql


ssm = boto3.client("ssm")


DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]


def get_db_password():

    parameter = ssm.get_parameter(
        Name=DB_PASSWORD_PARAMETER,
        WithDecryption=True
    )

    return parameter["Parameter"]["Value"]


def lambda_handler(event, context):

    connection = None

    try:

        print("Starting Order Lambda RDS connection test")

        # Get password from SSM
        db_password = get_db_password()

        print("Database password retrieved from SSM")

        # Connect to RDS
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=db_password,
            database=DB_NAME,
            connect_timeout=10
        )

        print("Successfully connected to RDS")

        # Test database query
        with connection.cursor() as cursor:

            cursor.execute("SELECT 1")

            result = cursor.fetchone()

        print(
            json.dumps({
                "level": "INFO",
                "message": "SQL query executed successfully",
                "result": result[0]
            })
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Order Lambda successfully connected to RDS",
                "query_result": result[0]
            })
        }

    except Exception as e:

        print(
            json.dumps({
                "level": "ERROR",
                "message": "RDS connection failed",
                "error": str(e)
            })
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "RDS connection failed",
                "error": str(e)
            })
        }

    finally:

        if connection:

            connection.close()

            print("RDS connection closed")
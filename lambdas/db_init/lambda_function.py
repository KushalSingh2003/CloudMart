import os
import json

import boto3
import pymysql


# ------------------------------------------------------------
# Environment variables
# ------------------------------------------------------------

DB_HOST_PARAMETER = os.environ["DB_HOST_PARAMETER"]
DB_PORT_PARAMETER = os.environ["DB_PORT_PARAMETER"]
DB_NAME_PARAMETER = os.environ["DB_NAME_PARAMETER"]
DB_USER_PARAMETER = os.environ["DB_USER_PARAMETER"]
DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]


# ------------------------------------------------------------
# AWS clients
# ------------------------------------------------------------

ssm = boto3.client("ssm")


# ------------------------------------------------------------
# Get parameter from SSM Parameter Store
# ------------------------------------------------------------

def get_ssm_parameter(parameter_name):
    response = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


# ------------------------------------------------------------
# Connect to RDS MySQL
# ------------------------------------------------------------

def get_connection():

    host = get_ssm_parameter(DB_HOST_PARAMETER)
    port = int(get_ssm_parameter(DB_PORT_PARAMETER))
    database = get_ssm_parameter(DB_NAME_PARAMETER)
    user = get_ssm_parameter(DB_USER_PARAMETER)
    password = get_ssm_parameter(DB_PASSWORD_PARAMETER)

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


# ------------------------------------------------------------
# Initialize database using schema.sql
# ------------------------------------------------------------

def initialize_database(connection):

    print(json.dumps({
        "level": "INFO",
        "message": "Starting database initialization"
    }))

    try:

        # schema.sql is packaged inside the Lambda ZIP
        with open("/var/task/schema.sql", "r") as file:
            sql_script = file.read()

        print(json.dumps({
            "level": "INFO",
            "message": "schema.sql loaded successfully"
        }))

        # Split SQL file into individual statements
        statements = sql_script.split(";")

        executed_statements = 0

        with connection.cursor() as cursor:

            for statement in statements:

                statement = statement.strip()

                if not statement:
                    continue

                cursor.execute(statement)

                executed_statements += 1

        connection.commit()

        print(json.dumps({
            "level": "INFO",
            "message": "Database initialization completed",
            "statements_executed": executed_statements
        }))

    except Exception as e:

        connection.rollback()

        print(json.dumps({
            "level": "ERROR",
            "message": "Database initialization failed",
            "error": str(e)
        }))

        raise


# ------------------------------------------------------------
# Lambda handler
# ------------------------------------------------------------

def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    connection = None

    try:

        # ----------------------------------------------------
        # Connect to RDS
        # ----------------------------------------------------

        connection = get_connection()

        print(json.dumps({
            "level": "INFO",
            "message": "Successfully connected to RDS"
        }))

        # ----------------------------------------------------
        # Create / initialize all database tables
        # ----------------------------------------------------

        initialize_database(connection)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Database initialized successfully"
            })
        }

    except pymysql.MySQLError as e:

        print(json.dumps({
            "level": "ERROR",
            "message": "Database error",
            "error": str(e)
        }))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Database initialization failed",
                "error": str(e)
            })
        }

    except Exception as e:

        print(json.dumps({
            "level": "ERROR",
            "message": "Unexpected error",
            "error": str(e)
        }))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Database initialization failed",
                "error": str(e)
            })
        }

    finally:

        if connection:
            connection.close()

            print(json.dumps({
                "level": "INFO",
                "message": "RDS connection closed"
            }))
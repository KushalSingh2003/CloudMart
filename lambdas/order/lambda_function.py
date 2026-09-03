# import os
# import json
# import boto3
# import pymysql


# ssm = boto3.client("ssm")


# DB_HOST = os.environ["DB_HOST"]
# DB_PORT = int(os.environ.get("DB_PORT", 3306))
# DB_NAME = os.environ["DB_NAME"]
# DB_USER = os.environ["DB_USER"]
# DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]


# def get_db_password():

#     parameter = ssm.get_parameter(
#         Name=DB_PASSWORD_PARAMETER,
#         WithDecryption=True
#     )

#     return parameter["Parameter"]["Value"]


# def lambda_handler(event, context):

#     connection = None

#     try:

#         print("Starting Order Lambda RDS connection test")

#         # Get password from SSM
#         db_password = get_db_password()

#         print("Database password retrieved from SSM")

#         # Connect to RDS
#         connection = pymysql.connect(
#             host=DB_HOST,
#             port=DB_PORT,
#             user=DB_USER,
#             password=db_password,
#             database=DB_NAME,
#             connect_timeout=10
#         )

#         print("Successfully connected to RDS")

#         # Test database query
#         with connection.cursor() as cursor:

#             cursor.execute("SELECT 1")

#             result = cursor.fetchone()

#         print(
#             json.dumps({
#                 "level": "INFO",
#                 "message": "SQL query executed successfully",
#                 "result": result[0]
#             })
#         )

#         return {
#             "statusCode": 200,
#             "body": json.dumps({
#                 "message": "Order Lambda successfully connected to RDS",
#                 "query_result": result[0]
#             })
#         }

#     except Exception as e:

#         print(
#             json.dumps({
#                 "level": "ERROR",
#                 "message": "RDS connection failed",
#                 "error": str(e)
#             })
#         )

#         return {
#             "statusCode": 500,
#             "body": json.dumps({
#                 "message": "RDS connection failed",
#                 "error": str(e)
#             })
#         }

#     finally:

#         if connection:

#             connection.close()

#             print("RDS connection closed")
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


ssm = boto3.client("ssm")


# ------------------------------------------------------------
# Get SSM parameter
# ------------------------------------------------------------

def get_ssm_parameter(parameter_name):

    response = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


# ------------------------------------------------------------
# Database connection
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
# Lambda handler
# ------------------------------------------------------------

def lambda_handler(event, context):

    print("HTTP METHOD:", event.get("httpMethod"))
    print("PATH PARAMETERS:", event.get("pathParameters"))
    print("BODY:", event.get("body"))

    connection = None

    try:

        # ----------------------------------------------------
        # Connect to database
        # ----------------------------------------------------

        connection = get_connection()

        print(json.dumps({
            "level": "INFO",
            "message": "Successfully connected to RDS"
        }))


        # ----------------------------------------------------
        # HTTP method
        # ----------------------------------------------------

        http_method = event.get("httpMethod")


        # ----------------------------------------------------
        # Path parameters
        # ----------------------------------------------------

        path_parameters = event.get("pathParameters") or {}

        order_id = path_parameters.get("orderId")


        # ----------------------------------------------------
        # Request body
        # ----------------------------------------------------

        body = event.get("body")

        if body:
            body = json.loads(body)


        # ====================================================
        # GET /orders
        # ====================================================

        if http_method == "GET" and not order_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        order_id AS OrderID,
                        customer_id AS CustomerID,
                        total_amount AS TotalAmount,
                        status AS Status,
                        created_at AS CreatedAt
                    FROM Orders
                    ORDER BY created_at DESC
                    """
                )

                orders = cursor.fetchall()

            connection.commit()

            return response(
                200,
                orders
            )


        # ====================================================
        # GET /orders/{orderId}
        # ====================================================

        if http_method == "GET" and order_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        order_id AS OrderID,
                        customer_id AS CustomerID,
                        total_amount AS TotalAmount,
                        status AS Status,
                        created_at AS CreatedAt
                    FROM Orders
                    WHERE order_id = %s
                    """,
                    (order_id,)
                )

                order = cursor.fetchone()


            if not order:

                connection.rollback()

                return response(
                    404,
                    {
                        "message": "Order not found"
                    }
                )


            connection.commit()

            return response(
                200,
                order
            )


        # ====================================================
        # POST /orders
        # ====================================================

        if http_method == "POST":

            if not body:

                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )


            # ------------------------------------------------
            # Required fields
            # ------------------------------------------------

            required_fields = [
                "CustomerID",
                "TotalAmount"
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in body
            ]

            if missing_fields:

                connection.rollback()

                return response(
                    400,
                    {
                        "message": "Missing required fields",
                        "fields": missing_fields
                    }
                )


            customer_id = body["CustomerID"]
            total_amount = body["TotalAmount"]


            # ------------------------------------------------
            # Validate CustomerID
            # ------------------------------------------------

            if (
                isinstance(customer_id, bool)
                or not isinstance(customer_id, int)
                or customer_id <= 0
            ):

                connection.rollback()

                return response(
                    400,
                    {
                        "message": "CustomerID must be a positive integer"
                    }
                )


            # ------------------------------------------------
            # Validate TotalAmount
            # ------------------------------------------------

            try:

                total_amount = float(total_amount)

            except (ValueError, TypeError):

                connection.rollback()

                return response(
                    400,
                    {
                        "message": "TotalAmount must be a valid number"
                    }
                )


            if total_amount < 0:

                connection.rollback()

                return response(
                    400,
                    {
                        "message": "TotalAmount cannot be negative"
                    }
                )


            # ------------------------------------------------
            # Create order
            # ------------------------------------------------

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO Orders
                    (
                        customer_id,
                        total_amount,
                        status
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        'PENDING'
                    )
                    """,
                    (
                        customer_id,
                        total_amount
                    )
                )

                new_order_id = cursor.lastrowid


            connection.commit()

            return response(
                201,
                {
                    "message": "Order created",
                    "OrderID": new_order_id
                }
            )


        # ====================================================
        # Unsupported operation
        # ====================================================

        connection.rollback()

        return response(
            400,
            {
                "message": "Unsupported operation"
            }
        )


    # ========================================================
    # Error handling
    # ========================================================

    except json.JSONDecodeError:

        if connection:
            connection.rollback()

        print(json.dumps({
            "level": "ERROR",
            "message": "Invalid JSON request body"
        }))

        return response(
            400,
            {
                "message": "Invalid JSON request body"
            }
        )


    except pymysql.err.IntegrityError as e:

        if connection:
            connection.rollback()

        print(json.dumps({
            "level": "ERROR",
            "message": "Database integrity error",
            "error": str(e)
        }))

        return response(
            400,
            {
                "message": "Database constraint violation"
            }
        )


    except pymysql.MySQLError as e:

        if connection:
            connection.rollback()

        print(json.dumps({
            "level": "ERROR",
            "message": "Database error",
            "error": str(e)
        }))

        return response(
            500,
            {
                "message": "Database error"
            }
        )


    except Exception as e:

        if connection:
            connection.rollback()

        print(json.dumps({
            "level": "ERROR",
            "message": "Unexpected error",
            "error": str(e)
        }))

        return response(
            500,
            {
                "message": "Internal server error"
            }
        )


    finally:

        if connection:
            connection.close()


# ------------------------------------------------------------
# API response
# ------------------------------------------------------------

def response(status_code, body):

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=str)
    }
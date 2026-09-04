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
# import os
# import json

# import boto3
# import pymysql


# # ------------------------------------------------------------
# # Environment variables
# # ------------------------------------------------------------

# DB_HOST_PARAMETER = os.environ["DB_HOST_PARAMETER"]
# DB_PORT_PARAMETER = os.environ["DB_PORT_PARAMETER"]
# DB_NAME_PARAMETER = os.environ["DB_NAME_PARAMETER"]
# DB_USER_PARAMETER = os.environ["DB_USER_PARAMETER"]
# DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]


# ssm = boto3.client("ssm")


# # ------------------------------------------------------------
# # Get SSM parameter
# # ------------------------------------------------------------

# def get_ssm_parameter(parameter_name):

#     response = ssm.get_parameter(
#         Name=parameter_name,
#         WithDecryption=True
#     )

#     return response["Parameter"]["Value"]


# # ------------------------------------------------------------
# # Database connection
# # ------------------------------------------------------------

# def get_connection():

#     host = get_ssm_parameter(DB_HOST_PARAMETER)
#     port = int(get_ssm_parameter(DB_PORT_PARAMETER))
#     database = get_ssm_parameter(DB_NAME_PARAMETER)
#     user = get_ssm_parameter(DB_USER_PARAMETER)
#     password = get_ssm_parameter(DB_PASSWORD_PARAMETER)

#     return pymysql.connect(
#         host=host,
#         port=port,
#         user=user,
#         password=password,
#         database=database,
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=False
#     )


# # ------------------------------------------------------------
# # Lambda handler
# # ------------------------------------------------------------

# def lambda_handler(event, context):

#     print("HTTP METHOD:", event.get("httpMethod"))
#     print("PATH PARAMETERS:", event.get("pathParameters"))
#     print("BODY:", event.get("body"))

#     connection = None

#     try:

#         # ----------------------------------------------------
#         # Connect to database
#         # ----------------------------------------------------

#         connection = get_connection()

#         print(json.dumps({
#             "level": "INFO",
#             "message": "Successfully connected to RDS"
#         }))


#         # ----------------------------------------------------
#         # HTTP method
#         # ----------------------------------------------------

#         http_method = event.get("httpMethod")


#         # ----------------------------------------------------
#         # Path parameters
#         # ----------------------------------------------------

#         path_parameters = event.get("pathParameters") or {}

#         order_id = path_parameters.get("orderId")


#         # ----------------------------------------------------
#         # Request body
#         # ----------------------------------------------------

#         body = event.get("body")

#         if body:
#             body = json.loads(body)


#         # ====================================================
#         # GET /orders
#         # ====================================================

#         if http_method == "GET" and not order_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     SELECT
#                         order_id AS OrderID,
#                         customer_id AS CustomerID,
#                         total_amount AS TotalAmount,
#                         status AS Status,
#                         created_at AS CreatedAt
#                     FROM Orders
#                     ORDER BY created_at DESC
#                     """
#                 )

#                 orders = cursor.fetchall()

#             connection.commit()

#             return response(
#                 200,
#                 orders
#             )


#         # ====================================================
#         # GET /orders/{orderId}
#         # ====================================================

#         if http_method == "GET" and order_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     SELECT
#                         order_id AS OrderID,
#                         customer_id AS CustomerID,
#                         total_amount AS TotalAmount,
#                         status AS Status,
#                         created_at AS CreatedAt
#                     FROM Orders
#                     WHERE order_id = %s
#                     """,
#                     (order_id,)
#                 )

#                 order = cursor.fetchone()


#             if not order:

#                 connection.rollback()

#                 return response(
#                     404,
#                     {
#                         "message": "Order not found"
#                     }
#                 )


#             connection.commit()

#             return response(
#                 200,
#                 order
#             )


#         # ====================================================
#         # POST /orders
#         # ====================================================

#         if http_method == "POST":

#             if not body:

#                 return response(
#                     400,
#                     {
#                         "message": "Request body is required"
#                     }
#                 )


#             # ------------------------------------------------
#             # Required fields
#             # ------------------------------------------------

#             required_fields = [
#                 "CustomerID",
#                 "TotalAmount"
#             ]

#             missing_fields = [
#                 field
#                 for field in required_fields
#                 if field not in body
#             ]

#             if missing_fields:

#                 connection.rollback()

#                 return response(
#                     400,
#                     {
#                         "message": "Missing required fields",
#                         "fields": missing_fields
#                     }
#                 )


#             customer_id = body["CustomerID"]
#             total_amount = body["TotalAmount"]


#             # ------------------------------------------------
#             # Validate CustomerID
#             # ------------------------------------------------

#             if (
#                 isinstance(customer_id, bool)
#                 or not isinstance(customer_id, int)
#                 or customer_id <= 0
#             ):

#                 connection.rollback()

#                 return response(
#                     400,
#                     {
#                         "message": "CustomerID must be a positive integer"
#                     }
#                 )


#             # ------------------------------------------------
#             # Validate TotalAmount
#             # ------------------------------------------------

#             try:

#                 total_amount = float(total_amount)

#             except (ValueError, TypeError):

#                 connection.rollback()

#                 return response(
#                     400,
#                     {
#                         "message": "TotalAmount must be a valid number"
#                     }
#                 )


#             if total_amount < 0:

#                 connection.rollback()

#                 return response(
#                     400,
#                     {
#                         "message": "TotalAmount cannot be negative"
#                     }
#                 )


#             # ------------------------------------------------
#             # Create order
#             # ------------------------------------------------

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     INSERT INTO Orders
#                     (
#                         customer_id,
#                         total_amount,
#                         status
#                     )
#                     VALUES
#                     (
#                         %s,
#                         %s,
#                         'PENDING'
#                     )
#                     """,
#                     (
#                         customer_id,
#                         total_amount
#                     )
#                 )

#                 new_order_id = cursor.lastrowid


#             connection.commit()

#             return response(
#                 201,
#                 {
#                     "message": "Order created",
#                     "OrderID": new_order_id
#                 }
#             )


#         # ====================================================
#         # Unsupported operation
#         # ====================================================

#         connection.rollback()

#         return response(
#             400,
#             {
#                 "message": "Unsupported operation"
#             }
#         )


#     # ========================================================
#     # Error handling
#     # ========================================================

#     except json.JSONDecodeError:

#         if connection:
#             connection.rollback()

#         print(json.dumps({
#             "level": "ERROR",
#             "message": "Invalid JSON request body"
#         }))

#         return response(
#             400,
#             {
#                 "message": "Invalid JSON request body"
#             }
#         )


#     except pymysql.err.IntegrityError as e:

#         if connection:
#             connection.rollback()

#         print(json.dumps({
#             "level": "ERROR",
#             "message": "Database integrity error",
#             "error": str(e)
#         }))

#         return response(
#             400,
#             {
#                 "message": "Database constraint violation"
#             }
#         )


#     except pymysql.MySQLError as e:

#         if connection:
#             connection.rollback()

#         print(json.dumps({
#             "level": "ERROR",
#             "message": "Database error",
#             "error": str(e)
#         }))

#         return response(
#             500,
#             {
#                 "message": "Database error"
#             }
#         )


#     except Exception as e:

#         if connection:
#             connection.rollback()

#         print(json.dumps({
#             "level": "ERROR",
#             "message": "Unexpected error",
#             "error": str(e)
#         }))

#         return response(
#             500,
#             {
#                 "message": "Internal server error"
#             }
#         )


#     finally:

#         if connection:
#             connection.close()


# # ------------------------------------------------------------
# # API response
# # ------------------------------------------------------------

# def response(status_code, body):

#     return {
#         "statusCode": status_code,
#         "headers": {
#             "Content-Type": "application/json"
#         },
#         "body": json.dumps(body, default=str)
#     }
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
        # Only ACTIVE orders are returned.
        # Optional filter: ?customerId=X
        # ====================================================

        if http_method == "GET" and not order_id:

            query_parameters = event.get("queryStringParameters") or {}
            customer_id = query_parameters.get("customerId")

            query = """
                SELECT
                    order_id AS OrderID,
                    customer_id AS CustomerID,
                    total_amount AS TotalAmount,
                    status AS Status,
                    created_at AS CreatedAt
                FROM Orders
                WHERE status = 'ACTIVE'
            """
            params = []

            if customer_id is not None:
                try:
                    customer_id = int(customer_id)
                except (ValueError, TypeError):
                    connection.rollback()
                    return response(400, {"message": "customerId must be a valid integer"})

                if customer_id <= 0:
                    connection.rollback()
                    return response(400, {"message": "customerId must be a positive integer"})

                query += " AND customer_id = %s"
                params.append(customer_id)

            query += " ORDER BY created_at DESC"

            with connection.cursor() as cursor:
                cursor.execute(query, params)
                orders = cursor.fetchall()

            connection.commit()

            return response(200, orders)


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
                      AND status = 'ACTIVE'
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
        # PUT /orders/{orderId}
        # Full update of an ACTIVE order.
        # ====================================================

        if http_method == "PUT" and order_id:

            if not body:
                connection.rollback()
                return response(400, {"message": "Request body is required"})

            required_fields = ["CustomerID", "TotalAmount", "Status"]
            missing_fields = [field for field in required_fields if field not in body]

            if missing_fields:
                connection.rollback()
                return response(
                    400,
                    {"message": "Missing required fields", "fields": missing_fields}
                )

            customer_id = body["CustomerID"]
            total_amount = body["TotalAmount"]
            status = body["Status"]

            if (
                isinstance(customer_id, bool)
                or not isinstance(customer_id, int)
                or customer_id <= 0
            ):
                connection.rollback()
                return response(400, {"message": "CustomerID must be a positive integer"})

            try:
                total_amount = float(total_amount)
            except (ValueError, TypeError):
                connection.rollback()
                return response(400, {"message": "TotalAmount must be a valid number"})

            if total_amount < 0:
                connection.rollback()
                return response(400, {"message": "TotalAmount cannot be negative"})

            if status not in ("ACTIVE", "PENDING", "COMPLETED", "CANCELLED"):
                connection.rollback()
                return response(
                    400,
                    {"message": "Status must be one of ACTIVE, PENDING, COMPLETED, CANCELLED"}
                )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT order_id
                    FROM Orders
                    WHERE order_id = %s
                      AND status = 'ACTIVE'
                    """,
                    (order_id,)
                )

                if not cursor.fetchone():
                    connection.rollback()
                    return response(404, {"message": "Active order not found"})

                cursor.execute(
                    """
                    UPDATE Orders
                    SET customer_id = %s,
                        total_amount = %s,
                        status = %s
                    WHERE order_id = %s
                      AND status = 'ACTIVE'
                    """,
                    (customer_id, total_amount, status, order_id)
                )

            connection.commit()

            return response(
                200,
                {"message": "Order updated", "OrderID": order_id}
            )


        # ====================================================
        # PATCH /orders/{orderId}
        # Partial update of an ACTIVE order.
        # ====================================================

        if http_method == "PATCH" and order_id:

            if not body:
                connection.rollback()
                return response(400, {"message": "Request body is required"})

            allowed_fields = {"CustomerID", "TotalAmount", "Status"}
            invalid_fields = [field for field in body if field not in allowed_fields]

            if invalid_fields:
                connection.rollback()
                return response(
                    400,
                    {"message": "Invalid fields", "fields": invalid_fields}
                )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT customer_id, total_amount, status
                    FROM Orders
                    WHERE order_id = %s
                      AND status = 'ACTIVE'
                    """,
                    (order_id,)
                )

                existing_order = cursor.fetchone()

                if not existing_order:
                    connection.rollback()
                    return response(404, {"message": "Active order not found"})

                customer_id = existing_order["customer_id"]
                total_amount = existing_order["total_amount"]
                status = existing_order["status"]

                if "CustomerID" in body:
                    customer_id = body["CustomerID"]
                    if (
                        isinstance(customer_id, bool)
                        or not isinstance(customer_id, int)
                        or customer_id <= 0
                    ):
                        connection.rollback()
                        return response(
                            400,
                            {"message": "CustomerID must be a positive integer"}
                        )

                if "TotalAmount" in body:
                    try:
                        total_amount = float(body["TotalAmount"])
                    except (ValueError, TypeError):
                        connection.rollback()
                        return response(
                            400,
                            {"message": "TotalAmount must be a valid number"}
                        )

                    if total_amount < 0:
                        connection.rollback()
                        return response(
                            400,
                            {"message": "TotalAmount cannot be negative"}
                        )

                if "Status" in body:
                    status = body["Status"]
                    if status not in ("ACTIVE", "PENDING", "COMPLETED", "CANCELLED"):
                        connection.rollback()
                        return response(
                            400,
                            {"message": "Status must be one of ACTIVE, PENDING, COMPLETED, CANCELLED"}
                        )

                cursor.execute(
                    """
                    UPDATE Orders
                    SET customer_id = %s,
                        total_amount = %s,
                        status = %s
                    WHERE order_id = %s
                      AND status = 'ACTIVE'
                    """,
                    (customer_id, total_amount, status, order_id)
                )

            connection.commit()

            return response(
                200,
                {"message": "Order partially updated", "OrderID": order_id}
            )


        # ====================================================
        # DELETE /orders/{orderId}
        # Soft delete: change status to INACTIVE.
        # ====================================================

        if http_method == "DELETE" and order_id:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE Orders
                    SET status = 'INACTIVE'
                    WHERE order_id = %s
                      AND status = 'ACTIVE'
                    """,
                    (order_id,)
                )

                if cursor.rowcount == 0:
                    connection.rollback()
                    return response(404, {"message": "Active order not found"})

            connection.commit()

            return response(
                200,
                {"message": "Order deleted", "OrderID": order_id}
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
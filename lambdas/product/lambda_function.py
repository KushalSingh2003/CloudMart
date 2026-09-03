# import os
# import json
# import boto3
# import pymysql


# # ------------------------------------------------------------
# # Environment variables
# # ------------------------------------------------------------

# DB_HOST = os.environ["DB_HOST"]
# DB_PORT = int(os.environ.get("DB_PORT", 3306))
# DB_NAME = os.environ["DB_NAME"]
# DB_USER = os.environ["DB_USER"]
# DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]


# # add a new comment
# # added antoher comment

# # ------------------------------------------------------------
# # AWS clients
# # ------------------------------------------------------------

# ssm = boto3.client("ssm")



# # ------------------------------------------------------------
# # Get DB password from SSM
# # ------------------------------------------------------------

# def get_db_password():

#     response = ssm.get_parameter(
#         Name=DB_PASSWORD_PARAMETER,
#         WithDecryption=True
#     )

#     return response["Parameter"]["Value"]


# # ------------------------------------------------------------
# # Connect to RDS
# # ------------------------------------------------------------
# #checking the connection to the database using pymysql and returning the connection object.
# def get_connection():

#     password = get_db_password()

#     return pymysql.connect(
#         host=DB_HOST,
#         port=DB_PORT,
#         user=DB_USER,
#         password=password,
#         database=DB_NAME,
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )


# # ------------------------------------------------------------
# # Create Products table
# # ------------------------------------------------------------

# def create_products_table(connection):

#     query = """
#     CREATE TABLE IF NOT EXISTS Products (
#         ProductID INT AUTO_INCREMENT PRIMARY KEY,
#         Name VARCHAR(255) NOT NULL,
#         Description TEXT,
#         Price DECIMAL(10,2) NOT NULL,
#         Stock INT NOT NULL DEFAULT 0,
#         CategoryID INT NOT NULL
#     )
#     """

#     with connection.cursor() as cursor:
#         cursor.execute(query)


# # ------------------------------------------------------------
# # Lambda handler
# # ------------------------------------------------------------

# def lambda_handler(event, context):

#     connection = None

#     try:

#         # Connect to database
#         connection = get_connection()

#         # Make sure Products table exists
#         create_products_table(connection)

#         # API Gateway HTTP method
#         http_method = event.get("httpMethod")

#         # Path parameters
#         path_parameters = event.get("pathParameters") or {}

#         product_id = path_parameters.get("productId")

#         # Request body
#         body = event.get("body")

#         if body:
#             body = json.loads(body)

#         # ----------------------------------------------------
#         # GET /products
#         # ----------------------------------------------------

#         if http_method == "GET" and not product_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     SELECT *
#                     FROM Products
#                     """
#                 )

#                 products = cursor.fetchall()

#             return response(
#                 200,
#                 products
#             )

#         # ----------------------------------------------------
#         # GET /products/{productId}
#         # ----------------------------------------------------

#         if http_method == "GET" and product_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     SELECT *
#                     FROM Products
#                     WHERE ProductID = %s
#                     """,
#                     (product_id,)
#                 )

#                 product = cursor.fetchone()

#             if not product:

#                 return response(
#                     404,
#                     {"message": "Product not found"}
#                 )

#             return response(
#                 200,
#                 product
#             )

#         # ----------------------------------------------------
#         # POST /products
#         # ----------------------------------------------------

#         if http_method == "POST":

#             name = body["Name"]
#             description = body.get("Description")
#             price = body["Price"]
#             stock = body.get("Stock", 0)
#             category_id = body["CategoryID"]

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     INSERT INTO Products
#                     (Name, Description, Price, Stock, CategoryID)
#                     VALUES (%s, %s, %s, %s, %s)
#                     """,
#                     (
#                         name,
#                         description,
#                         price,
#                         stock,
#                         category_id
#                     )
#                 )

#                 new_product_id = cursor.lastrowid

          

#             return response(
#                 201,
#                 {
#                     "message": "Product created",
#                     "ProductID": new_product_id
#                 }
#             )

#         # ----------------------------------------------------
#         # PUT /products/{productId}
#         # ----------------------------------------------------

#         if http_method == "PUT" and product_id:

#             name = body["Name"]
#             description = body.get("Description")
#             price = body["Price"]
#             stock = body.get("Stock", 0)
#             category_id = body["CategoryID"]

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     UPDATE Products
#                     SET
#                         Name = %s,
#                         Description = %s,
#                         Price = %s,
#                         Stock = %s,
#                         CategoryID = %s
#                     WHERE ProductID = %s
#                     """,
#                     (
#                         name,
#                         description,
#                         price,
#                         stock,
#                         category_id,
#                         product_id
#                     )
#                 )

#                 if cursor.rowcount == 0:

#                     return response(
#                         404,
#                         {"message": "Product not found"}
#                     )

          

#         # ----------------------------------------------------
#         # DELETE /products/{productId}
#         # ----------------------------------------------------

#         if http_method == "DELETE" and product_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     DELETE FROM Products
#                     WHERE ProductID = %s
#                     """,
#                     (product_id,)
#                 )

#                 if cursor.rowcount == 0:

#                     return response(
#                         404,
#                         {"message": "Product not found"}
#                     )

            
#             return response(
#                 200,
#                 {"message": "Product deleted"}
#             )

#         return response(
#             400,
#             {"message": "Unsupported operation"}
#         )

#     except Exception as e:

#         print(f"Error: {str(e)}")

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
# # EventBridge
# # ------------------------------------------------------------




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
# 
# import os
# import json
# import boto3
# import pymysql


# # ------------------------------------------------------------
# # Environment variables
# # ------------------------------------------------------------

# DB_HOST = os.environ["DB_HOST"]
# DB_PORT = int(os.environ.get("DB_PORT", 3306))
# DB_NAME = os.environ["DB_NAME"]
# DB_USER = os.environ["DB_USER"]
# DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]


# # ------------------------------------------------------------
# # AWS clients
# # ------------------------------------------------------------

# ssm = boto3.client("ssm")
# events = boto3.client("events")

# LOW_STOCK_THRESHOLD = 5


# # ------------------------------------------------------------
# # Get DB password from SSM Parameter Store
# # ------------------------------------------------------------

# def get_db_password():

#     response = ssm.get_parameter(
#         Name=DB_PASSWORD_PARAMETER,
#         WithDecryption=True
#     )

#     return response["Parameter"]["Value"]


# # ------------------------------------------------------------
# # Connect to RDS MySQL
# # ------------------------------------------------------------

# def get_connection():

#     password = get_db_password()

#     return pymysql.connect(
#         host=DB_HOST,
#         port=DB_PORT,
#         user=DB_USER,
#         password=password,
#         database=DB_NAME,
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )


# # ------------------------------------------------------------
# # Initialize database using schema.sql
# # ------------------------------------------------------------

# def initialize_database(connection):

#     print(json.dumps({
#         "level": "INFO",
#         "message": "Starting database initialization"
#     }))

#     try:

#         with open("/var/task/schema.sql", "r") as file:
#             sql_script = file.read()

#         print(json.dumps({
#             "level": "INFO",
#             "message": "schema.sql loaded successfully"
#         }))

#         statements = sql_script.split(";")

#         executed_statements = 0

#         with connection.cursor() as cursor:

#             for statement in statements:

#                 statement = statement.strip()

#                 if not statement:
#                     continue

#                 cursor.execute(statement)

#                 executed_statements += 1

#         print(json.dumps({
#             "level": "INFO",
#             "message": "Database initialization completed",
#             "statements_executed": executed_statements
#         }))

#     except Exception as e:

#         print(json.dumps({
#             "level": "ERROR",
#             "message": "Database initialization failed",
#             "error": str(e)
#         }))

#         raise


# # ------------------------------------------------------------
# # Lambda handler
# # ------------------------------------------------------------

# def lambda_handler(event, context):

#     print("EVENT:", json.dumps(event))
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
#         # Create / initialize database tables
#         # ----------------------------------------------------

#         initialize_database(connection)


#         # ----------------------------------------------------
#         # API Gateway HTTP method
#         # ----------------------------------------------------

#         http_method = event.get("httpMethod")


#         # ----------------------------------------------------
#         # Path parameters
#         # ----------------------------------------------------

#         path_parameters = event.get("pathParameters") or {}

#         product_id = path_parameters.get("productId")


#         # ----------------------------------------------------
#         # Request body
#         # ----------------------------------------------------

#         body = event.get("body")

#         if body:

#             body = json.loads(body)


#         # ====================================================
#         # GET /products
#         #
#         # Return only ACTIVE products
#         # ====================================================

#         if http_method == "GET" and not product_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     SELECT
#                         product_id AS ProductID,
#                         name AS Name,
#                         description AS Description,
#                         price AS Price,
#                         stock AS Stock,
#                         category_id AS CategoryID,
#                         status AS Status
#                     FROM Products
#                     WHERE status = 'ACTIVE'
#                     """
#                 )

#                 products = cursor.fetchall()

#             return response(
#                 200,
#                 products
#             )


#         # ====================================================
#         # GET /products/{productId}
#         #
#         # Return product only if it is ACTIVE
#         # ====================================================

#         if http_method == "GET" and product_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     SELECT
#                         product_id AS ProductID,
#                         name AS Name,
#                         description AS Description,
#                         price AS Price,
#                         stock AS Stock,
#                         category_id AS CategoryID,
#                         status AS Status
#                     FROM Products
#                     WHERE product_id = %s
#                     AND status = 'ACTIVE'
#                     """,
#                     (product_id,)
#                 )

#                 product = cursor.fetchone()


#             if not product:

#                 return response(
#                     404,
#                     {
#                         "message": "Product not found"
#                     }
#                 )


#             return response(
#                 200,
#                 product
#             )


#         # ====================================================
#         # POST /products
#         # ====================================================

#         if http_method == "POST":

#             if not body:

#                 return response(
#                     400,
#                     {
#                         "message": "Request body is required"
#                     }
#                 )


#             # API request fields remain PascalCase
#             name = body["Name"]

#             description = body.get("Description")

#             price = body["Price"]

#             stock = body.get("Stock", 0)

#             category_id = body["CategoryID"]
#             if stock<0  or price < 0:
#                 return response(
#                     400,
#                     {
#                         "message": "Stock and price cannot be negative"
#                     }
#                 )


#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     INSERT INTO Products
#                     (
#                         name,
#                         description,
#                         price,
#                         stock,
#                         category_id,
#                         status
#                     )
#                     VALUES
#                     (
#                         %s,
#                         %s,
#                         %s,
#                         %s,
#                         %s,
#                         'ACTIVE'
#                     )
#                     """,
#                     (
#                         name,
#                         description,
#                         price,
#                         stock,
#                         category_id
#                     )
#                 )

#                 new_product_id = cursor.lastrowid


#             return response(
#                 201,
#                 {
#                     "message": "Product created",
#                     "ProductID": new_product_id
#                 }
#             )


#         # ====================================================
#         # PUT /products/{productId}
#         #
#         # Only ACTIVE products can be updated
#         # ====================================================

#         if http_method == "PUT" and product_id:

#             if not body:

#                 return response(
#                     400,
#                     {
#                         "message": "Request body is required"
#                     }
#                 )


#             # API request fields remain PascalCase
#             name = body["Name"]

#             description = body.get("Description")

#             price = body["Price"]

#             stock = body.get("Stock", 0)

#             category_id = body["CategoryID"]

#             if stock<0  or price < 0:
#                 return response(
#                     400,
#                     {
#                         "message": "Stock and price cannot be negative"
#                     }
#                 )
#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     UPDATE Products
#                     SET
#                         name = %s,
#                         description = %s,
#                         price = %s,
#                         stock = %s,
#                         category_id = %s
#                     WHERE product_id = %s
#                     AND status = 'ACTIVE'
#                     """,
#                     (
#                         name,
#                         description,
#                         price,
#                         stock,
#                         category_id,
#                         product_id
#                     )
#                 )


#                 if cursor.rowcount == 0:

#                     return response(
#                         404,
#                         {
#                             "message": "Product not found"
#                         }
#                     )


#             # ------------------------------------------------
#             # Low stock event
#             # ------------------------------------------------

#             if stock < LOW_STOCK_THRESHOLD:

#                 events.put_events(
#                     Entries=[
#                         {
#                             "EventBusName": os.environ["EVENT_BUS_NAME"],
#                             "Source": "cloudmart.inventory",
#                             "DetailType": "Low Stock Alert",
#                             "Detail": json.dumps({
#                                 "ProductID": product_id,
#                                 "Stock": stock,
#                                 "Threshold": LOW_STOCK_THRESHOLD
#                             })
#                         }
#                     ]
#                 )


#             return response(
#                 200,
#                 {
#                     "message": "Product updated",
#                     "ProductID": product_id
#                 }
#             )


#         # ====================================================
#         # DELETE /products/{productId}
#         #
#         # Soft delete:
#         # ACTIVE -> INACTIVE
#         # ====================================================

#         if http_method == "DELETE" and product_id:

#             with connection.cursor() as cursor:

#                 cursor.execute(
#                     """
#                     UPDATE Products
#                     SET status = 'INACTIVE'
#                     WHERE product_id = %s
#                     AND status = 'ACTIVE'
#                     """,
#                     (product_id,)
#                 )


#                 if cursor.rowcount == 0:

#                     return response(
#                         404,
#                         {
#                             "message": "Product not found"
#                         }
#                     )


#             return response(
#                 200,
#                 {
#                     "message": "Product deleted",
#                     "ProductID": product_id
#                 }
#             )


#         # ====================================================
#         # Unsupported operation
#         # ====================================================

#         return response(
#             400,
#             {
#                 "message": "Unsupported operation"
#             }
#         )


#     # ========================================================
#     # Error handling
#     # ========================================================

#     except KeyError as e:

#         print(f"Missing required field: {str(e)}")

#         return response(
#             400,
#             {
#                 "message": f"Missing required field: {str(e)}"
#             }
#         )


#     except json.JSONDecodeError:

#         print("Invalid JSON request body.")

#         return response(
#             400,
#             {
#                 "message": "Invalid JSON request body"
#             }
#         )


#     except Exception as e:

#         print(f"Error: {str(e)}")

#         return response(
#             500,
#             {
#                 "message": "Internal server error",
#                 "error": str(e)
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
from decimal import Decimal, InvalidOperation

import boto3
import pymysql


# ------------------------------------------------------------
# Environment variables
# ------------------------------------------------------------

DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]


# ------------------------------------------------------------
# AWS clients
# ------------------------------------------------------------

ssm = boto3.client("ssm")
events = boto3.client("events")

LOW_STOCK_THRESHOLD = 5


# ------------------------------------------------------------
# Get DB password from SSM Parameter Store
# ------------------------------------------------------------

def get_db_password():

    response = ssm.get_parameter(
        Name=DB_PASSWORD_PARAMETER,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


# ------------------------------------------------------------
# Connect to RDS MySQL
# ------------------------------------------------------------

def get_connection():

    password = get_db_password()

    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=password,
        database=DB_NAME,
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

        with open("/var/task/schema.sql", "r") as file:
            sql_script = file.read()

        print(json.dumps({
            "level": "INFO",
            "message": "schema.sql loaded successfully"
        }))

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
# Validate product request
# ------------------------------------------------------------

def validate_product_request(body):

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    required_fields = [
        "Name",
        "Price",
        "CategoryID"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in body
    ]

    if missing_fields:

        return (
            False,
            response(
                400,
                {
                    "message": "Missing required fields",
                    "fields": missing_fields
                }
            )
        )


    # --------------------------------------------------------
    # Name validation
    # --------------------------------------------------------

    name = body["Name"]

    if not isinstance(name, str):

        return (
            False,
            response(
                400,
                {
                    "message": "Name must be a string"
                }
            )
        )

    name = name.strip()

    if not name:

        return (
            False,
            response(
                400,
                {
                    "message": "Name cannot be empty"
                }
            )
        )

    if len(name) > 255:

        return (
            False,
            response(
                400,
                {
                    "message": "Name cannot exceed 255 characters"
                }
            )
        )


    # --------------------------------------------------------
    # Description validation
    # --------------------------------------------------------

    description = body.get("Description")

    if description is not None and not isinstance(description, str):

        return (
            False,
            response(
                400,
                {
                    "message": "Description must be a string"
                }
            )
        )


    # --------------------------------------------------------
    # Price validation
    # --------------------------------------------------------

    price = body["Price"]

    try:

        # Convert to Decimal for accurate monetary handling
        price = Decimal(str(price))

    except (InvalidOperation, ValueError, TypeError):

        return (
            False,
            response(
                400,
                {
                    "message": "Price must be a valid decimal number"
                }
            )
        )


    if price < 0:

        return (
            False,
            response(
                400,
                {
                    "message": "Price cannot be negative"
                }
            )
        )


    # --------------------------------------------------------
    # Stock validation
    # --------------------------------------------------------

    stock = body.get("Stock", 0)

    # bool is technically an int in Python,
    # so explicitly reject True/False.
    if isinstance(stock, bool) or not isinstance(stock, int):

        return (
            False,
            response(
                400,
                {
                    "message": "Stock must be a non-negative integer"
                }
            )
        )


    if stock < 0:

        return (
            False,
            response(
                400,
                {
                    "message": "Stock cannot be negative"
                }
            )
        )


    # --------------------------------------------------------
    # CategoryID validation
    # --------------------------------------------------------

    category_id = body["CategoryID"]

    if isinstance(category_id, bool) or not isinstance(category_id, int):

        return (
            False,
            response(
                400,
                {
                    "message": "CategoryID must be an integer"
                }
            )
        )


    if category_id <= 0:

        return (
            False,
            response(
                400,
                {
                    "message": "CategoryID must be greater than zero"
                }
            )
        )


    return (
        True,
        {
            "Name": name,
            "Description": description,
            "Price": price,
            "Stock": stock,
            "CategoryID": category_id
        }
    )


# ------------------------------------------------------------
# Validate category exists
# ------------------------------------------------------------

def category_exists(connection, category_id):

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT category_id
            FROM Category 
            WHERE category_id = %s
            """,
            (category_id,)
        )

        category = cursor.fetchone()

    return category is not None


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
        # Initialize database
        # ----------------------------------------------------

        initialize_database(connection)


        # ----------------------------------------------------
        # HTTP method
        # ----------------------------------------------------

        http_method = event.get("httpMethod")


        # ----------------------------------------------------
        # Path parameters
        # ----------------------------------------------------

        path_parameters = event.get("pathParameters") or {}

        product_id = path_parameters.get("productId")


        # ----------------------------------------------------
        # Request body
        # ----------------------------------------------------

        body = event.get("body")

        if body:

            body = json.loads(body)


        # ====================================================
        # GET /products
        # ====================================================

        if http_method == "GET" and not product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        product_id AS ProductID,
                        name AS Name,
                        description AS Description,
                        price AS Price,
                        stock AS Stock,
                        category_id AS CategoryID,
                        status AS Status
                    FROM Products
                    WHERE status = 'ACTIVE'
                    """
                )

                products = cursor.fetchall()

            connection.commit()

            return response(
                200,
                products
            )


        # ====================================================
        # GET /products/{productId}
        # ====================================================

        if http_method == "GET" and product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        product_id AS ProductID,
                        name AS Name,
                        description AS Description,
                        price AS Price,
                        stock AS Stock,
                        category_id AS CategoryID,
                        status AS Status
                    FROM Products
                    WHERE product_id = %s
                    AND status = 'ACTIVE'
                    """,
                    (product_id,)
                )

                product = cursor.fetchone()


            if not product:

                connection.rollback()

                return response(
                    404,
                    {
                        "message": "Product not found"
                    }
                )


            connection.commit()

            return response(
                200,
                product
            )


        # ====================================================
        # POST /products
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
            # Validate request
            # ------------------------------------------------

            valid, result = validate_product_request(body)

            if not valid:

                connection.rollback()

                return result


            name = result["Name"]
            description = result["Description"]
            price = result["Price"]
            stock = result["Stock"]
            category_id = result["CategoryID"]


            # ------------------------------------------------
            # Validate category
            # ------------------------------------------------

            if not category_exists(connection, category_id):

                connection.rollback()

                return response(
                    404,
                    {
                        "message": "Category not found",
                        "CategoryID": category_id
                    }
                )


            # ------------------------------------------------
            # Insert product
            # ------------------------------------------------

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO Products
                    (
                        name,
                        description,
                        price,
                        stock,
                        category_id,
                        status
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'ACTIVE'
                    )
                    """,
                    (
                        name,
                        description,
                        price,
                        stock,
                        category_id
                    )
                )

                new_product_id = cursor.lastrowid


            connection.commit()

            return response(
                201,
                {
                    "message": "Product created",
                    "ProductID": new_product_id
                }
            )


        # ====================================================
        # PUT /products/{productId}
        # ====================================================

        if http_method == "PUT" and product_id:

            if not body:

                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )


            # ------------------------------------------------
            # Validate request
            # ------------------------------------------------

            valid, result = validate_product_request(body)

            if not valid:

                connection.rollback()

                return result


            name = result["Name"]
            description = result["Description"]
            price = result["Price"]
            stock = result["Stock"]
            category_id = result["CategoryID"]


            # ------------------------------------------------
            # Validate category
            # ------------------------------------------------

            if not category_exists(connection, category_id):

                connection.rollback()

                return response(
                    404,
                    {
                        "message": "Category not found",
                        "CategoryID": category_id
                    }
                )


            # ------------------------------------------------
            # Update product
            # ------------------------------------------------

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE Products
                    SET
                        name = %s,
                        description = %s,
                        price = %s,
                        stock = %s,
                        category_id = %s
                    WHERE product_id = %s
                    AND status = 'ACTIVE'
                    """,
                    (
                        name,
                        description,
                        price,
                        stock,
                        category_id,
                        product_id
                    )
                )


                if cursor.rowcount == 0:

                    connection.rollback()

                    return response(
                        404,
                        {
                            "message": "Product not found"
                        }
                    )


            connection.commit()


            # ------------------------------------------------
            # Low stock event
            # ------------------------------------------------

            if stock < LOW_STOCK_THRESHOLD:

                events.put_events(
                    Entries=[
                        {
                            "EventBusName": os.environ["EVENT_BUS_NAME"],
                            "Source": "cloudmart.inventory",
                            "DetailType": "Low Stock Alert",
                            "Detail": json.dumps({
                                "ProductID": product_id,
                                "Stock": stock,
                                "Threshold": LOW_STOCK_THRESHOLD
                            })
                        }
                    ]
                )


            return response(
                200,
                {
                    "message": "Product updated",
                    "ProductID": product_id
                }
            )
        # ====================================================
        # ====================================================
        # PATCH /products/{productId}
        #
        # Partial update:
        # Only fields provided in the request are updated.
        # Only ACTIVE products can be updated.
        # ====================================================

        if http_method == "PATCH" and product_id:

            if not body:

                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )

            allowed_fields = {
                "Name",
                "Description",
                "Price",
                "Stock",
                "CategoryID"
            }

            unknown_fields = [
                field
                for field in body
                if field not in allowed_fields
            ]

            if unknown_fields:

                return response(
                    400,
                    {
                        "message": "Invalid fields",
                        "fields": unknown_fields
                    }
                )

            # Validate Name
            if "Name" in body:

                name = body["Name"]

                if not isinstance(name, str):
                    return response(400, {"message": "Name must be a string"})

                name = name.strip()

                if not name:
                    return response(400, {"message": "Name cannot be empty"})

                if len(name) > 255:
                    return response(400, {"message": "Name cannot exceed 255 characters"})

            # Validate Description
            if "Description" in body:

                description = body["Description"]

                if description is not None and not isinstance(description, str):
                    return response(400, {"message": "Description must be a string"})

            # Validate Price
            if "Price" in body:

                try:
                    price = Decimal(str(body["Price"]))
                except (InvalidOperation, ValueError, TypeError):
                    return response(
                        400,
                        {"message": "Price must be a valid decimal number"}
                    )

                if price < 0:
                    return response(400, {"message": "Price cannot be negative"})

            # Validate Stock
            if "Stock" in body:

                stock = body["Stock"]

                if isinstance(stock, bool) or not isinstance(stock, int):
                    return response(
                        400,
                        {"message": "Stock must be a non-negative integer"}
                    )

                if stock < 0:
                    return response(400, {"message": "Stock cannot be negative"})

            # Validate CategoryID
            if "CategoryID" in body:

                category_id = body["CategoryID"]

                if isinstance(category_id, bool) or not isinstance(category_id, int):
                    return response(400, {"message": "CategoryID must be an integer"})

                if category_id <= 0:
                    return response(400, {"message": "CategoryID must be greater than zero"})

                if not category_exists(connection, category_id):
                    return response(
                        404,
                        {
                            "message": "Category not found",
                            "CategoryID": category_id
                        }
                    )

            # Build dynamic UPDATE query
            update_fields = []
            values = []

            if "Name" in body:
                update_fields.append("name = %s")
                values.append(name)

            if "Description" in body:
                update_fields.append("description = %s")
                values.append(body["Description"])

            if "Price" in body:
                update_fields.append("price = %s")
                values.append(price)

            if "Stock" in body:
                update_fields.append("stock = %s")
                values.append(body["Stock"])

            if "CategoryID" in body:
                update_fields.append("category_id = %s")
                values.append(body["CategoryID"])

            values.append(product_id)

            update_query = f"""
                UPDATE Products
                SET {", ".join(update_fields)}
                WHERE product_id = %s
                AND status = 'ACTIVE'
            """

            try:
                with connection.cursor() as cursor:
                    cursor.execute(update_query, tuple(values))

                    if cursor.rowcount == 0:
                        connection.rollback()
                        return response(
                            404,
                            {"message": "Product not found"}
                        )

                connection.commit()

                # Low stock event
                if "Stock" in body and body["Stock"] < LOW_STOCK_THRESHOLD:
                    events.put_events(
                        Entries=[
                            {
                                "EventBusName": os.environ["EVENT_BUS_NAME"],
                                "Source": "cloudmart.inventory",
                                "DetailType": "Low Stock Alert",
                                "Detail": json.dumps({
                                    "ProductID": product_id,
                                    "Stock": body["Stock"],
                                    "Threshold": LOW_STOCK_THRESHOLD
                                })
                            }
                        ]
                    )

                return response(
                    200,
                    {
                        "message": "Product updated",
                        "ProductID": product_id
                    }
                )

            except Exception:
                connection.rollback()
                raise

        # ====================================================
        # DELETE /products/{productId}
        # ====================================================

        if http_method == "DELETE" and product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE Products
                    SET status = 'INACTIVE'
                    WHERE product_id = %s
                    AND status = 'ACTIVE'
                    """,
                    (product_id,)
                )


                if cursor.rowcount == 0:

                    connection.rollback()

                    return response(
                        404,
                        {
                            "message": "Product not found"
                        }
                    )


            connection.commit()

            return response(
                200,
                {
                    "message": "Product deleted",
                    "ProductID": product_id
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
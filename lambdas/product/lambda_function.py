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
import os
import json
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


# ------------------------------------------------------------
# Get DB password from SSM
# ------------------------------------------------------------

def get_db_password():

    response = ssm.get_parameter(
        Name=DB_PASSWORD_PARAMETER,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


# ------------------------------------------------------------
# Connect to RDS
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
        autocommit=True
    )


# ------------------------------------------------------------
# Create Products table / migrate existing table
# ------------------------------------------------------------

def create_products_table(connection):

    # Create table if it does not already exist.
    # Status is included for new tables.

    create_query = """
    CREATE TABLE IF NOT EXISTS Products (
        ProductID INT AUTO_INCREMENT PRIMARY KEY,
        Name VARCHAR(255) NOT NULL,
        Description TEXT,
        Price DECIMAL(10,2) NOT NULL,
        Stock INT NOT NULL DEFAULT 0,
        CategoryID INT NOT NULL,
        Status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
    )
    """

    with connection.cursor() as cursor:
        cursor.execute(create_query)


    # --------------------------------------------------------
    # Check whether Status column exists
    # --------------------------------------------------------

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT COUNT(*) AS column_exists
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'Products'
            AND COLUMN_NAME = 'Status'
            """,
            (DB_NAME,)
        )

        result = cursor.fetchone()


    # --------------------------------------------------------
    # Add Status column to existing Products table
    # --------------------------------------------------------

    if result["column_exists"] == 0:

        print("Status column not found. Adding Status column...")

        with connection.cursor() as cursor:

            cursor.execute(
                """
                ALTER TABLE Products
                ADD COLUMN Status VARCHAR(20)
                NOT NULL DEFAULT 'ACTIVE'
                """
            )

        print("Status column added successfully.")

    else:

        print("Status column already exists.")


# ------------------------------------------------------------
# Lambda handler
# ------------------------------------------------------------

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))
    print("HTTP METHOD:", event.get("httpMethod"))
    print("PATH PARAMETERS:", event.get("pathParameters"))
    print("BODY:", event.get("body"))

    connection = None

    try:

        # ----------------------------------------------------
        # Connect to database
        # ----------------------------------------------------

        connection = get_connection()


        # ----------------------------------------------------
        # Create / migrate Products table
        # ----------------------------------------------------

        create_products_table(connection)


        # ----------------------------------------------------
        # API Gateway HTTP method
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


        # ----------------------------------------------------
        # GET /products
        #
        # Return only ACTIVE products
        # ----------------------------------------------------

        if http_method == "GET" and not product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        ProductID,
                        Name,
                        Description,
                        Price,
                        Stock,
                        CategoryID,
                        Status
                    FROM Products
                    WHERE Status = 'ACTIVE'
                    """
                )

                products = cursor.fetchall()


            return response(
                200,
                products
            )


        # ----------------------------------------------------
        # GET /products/{productId}
        #
        # Return product only if it is ACTIVE
        # ----------------------------------------------------

        if http_method == "GET" and product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        ProductID,
                        Name,
                        Description,
                        Price,
                        Stock,
                        CategoryID,
                        Status
                    FROM Products
                    WHERE ProductID = %s
                    AND Status = 'ACTIVE'
                    """,
                    (product_id,)
                )

                product = cursor.fetchone()


            if not product:

                return response(
                    404,
                    {
                        "message": "Product not found"
                    }
                )


            return response(
                200,
                product
            )


        # ----------------------------------------------------
        # POST /products
        # ----------------------------------------------------

        if http_method == "POST":

            if not body:

                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )


            name = body["Name"]

            description = body.get("Description")

            price = body["Price"]

            stock = body.get("Stock", 0)

            category_id = body["CategoryID"]


            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO Products
                    (
                        Name,
                        Description,
                        Price,
                        Stock,
                        CategoryID,
                        Status
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


            return response(
                201,
                {
                    "message": "Product created",
                    "ProductID": new_product_id
                }
            )


        # ----------------------------------------------------
        # PUT /products/{productId}
        #
        # Only ACTIVE products can be updated
        # ----------------------------------------------------

        if http_method == "PUT" and product_id:

            if not body:

                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )


            name = body["Name"]

            description = body.get("Description")

            price = body["Price"]

            stock = body.get("Stock", 0)

            category_id = body["CategoryID"]


            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE Products
                    SET
                        Name = %s,
                        Description = %s,
                        Price = %s,
                        Stock = %s,
                        CategoryID = %s
                    WHERE ProductID = %s
                    AND Status = 'ACTIVE'
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

                    return response(
                        404,
                        {
                            "message": "Product not found"
                        }
                    )


            return response(
                200,
                {
                    "message": "Product updated",
                    "ProductID": product_id
                }
            )


        # ----------------------------------------------------
        # DELETE /products/{productId}
        #
        # Soft delete:
        # Change Status from ACTIVE to INACTIVE.
        #
        # The product remains in the database.
        # ----------------------------------------------------

        if http_method == "DELETE" and product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE Products
                    SET Status = 'INACTIVE'
                    WHERE ProductID = %s
                    AND Status = 'ACTIVE'
                    """,
                    (product_id,)
                )


                if cursor.rowcount == 0:

                    return response(
                        404,
                        {
                            "message": "Product not found"
                        }
                    )


            return response(
                200,
                {
                    "message": "Product deleted",
                    "ProductID": product_id
                }
            )


        # ----------------------------------------------------
        # Unsupported operation
        # ----------------------------------------------------

        return response(
            400,
            {
                "message": "Unsupported operation"
            }
        )


    except KeyError as e:

        print(f"Missing required field: {str(e)}")

        return response(
            400,
            {
                "message": f"Missing required field: {str(e)}"
            }
        )


    except json.JSONDecodeError:

        print("Invalid JSON request body.")

        return response(
            400,
            {
                "message": "Invalid JSON request body"
            }
        )


    except Exception as e:

        print(f"Error: {str(e)}")

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
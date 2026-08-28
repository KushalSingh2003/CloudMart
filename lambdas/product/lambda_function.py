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

EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME")


# ------------------------------------------------------------
# AWS clients
# ------------------------------------------------------------

ssm = boto3.client("ssm")
events = boto3.client("events")


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
# Create Products table
# ------------------------------------------------------------

def create_products_table(connection):

    query = """
    CREATE TABLE IF NOT EXISTS Products (
        ProductID INT AUTO_INCREMENT PRIMARY KEY,
        Name VARCHAR(255) NOT NULL,
        Description TEXT,
        Price DECIMAL(10,2) NOT NULL,
        Stock INT NOT NULL DEFAULT 0,
        CategoryID INT NOT NULL
    )
    """

    with connection.cursor() as cursor:
        cursor.execute(query)


# ------------------------------------------------------------
# Lambda handler
# ------------------------------------------------------------

def lambda_handler(event, context):

    connection = None

    try:

        # Connect to database
        connection = get_connection()

        # Make sure Products table exists
        create_products_table(connection)

        # API Gateway HTTP method
        http_method = event.get("httpMethod")

        # Path parameters
        path_parameters = event.get("pathParameters") or {}

        product_id = path_parameters.get("productId")

        # Request body
        body = event.get("body")

        if body:
            body = json.loads(body)

        # ----------------------------------------------------
        # GET /products
        # ----------------------------------------------------

        if http_method == "GET" and not product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT *
                    FROM Products
                    """
                )

                products = cursor.fetchall()

            return response(
                200,
                products
            )

        # ----------------------------------------------------
        # GET /products/{productId}
        # ----------------------------------------------------

        if http_method == "GET" and product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT *
                    FROM Products
                    WHERE ProductID = %s
                    """,
                    (product_id,)
                )

                product = cursor.fetchone()

            if not product:

                return response(
                    404,
                    {"message": "Product not found"}
                )

            return response(
                200,
                product
            )

        # ----------------------------------------------------
        # POST /products
        # ----------------------------------------------------

        if http_method == "POST":

            name = body["Name"]
            description = body.get("Description")
            price = body["Price"]
            stock = body.get("Stock", 0)
            category_id = body["CategoryID"]

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO Products
                    (Name, Description, Price, Stock, CategoryID)
                    VALUES (%s, %s, %s, %s, %s)
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

            publish_event(
                "ProductCreated",
                {
                    "ProductID": new_product_id,
                    "Name": name
                }
            )

            return response(
                201,
                {
                    "message": "Product created",
                    "ProductID": new_product_id
                }
            )

        # ----------------------------------------------------
        # PUT /products/{productId}
        # ----------------------------------------------------

        if http_method == "PUT" and product_id:

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
                        {"message": "Product not found"}
                    )

            publish_event(
                "ProductUpdated",
                {
                    "ProductID": product_id
                }
            )

            return response(
                200,
                {"message": "Product updated"}
            )

        # ----------------------------------------------------
        # DELETE /products/{productId}
        # ----------------------------------------------------

        if http_method == "DELETE" and product_id:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM Products
                    WHERE ProductID = %s
                    """,
                    (product_id,)
                )

                if cursor.rowcount == 0:

                    return response(
                        404,
                        {"message": "Product not found"}
                    )

            publish_event(
                "ProductDeleted",
                {
                    "ProductID": product_id
                }
            )

            return response(
                200,
                {"message": "Product deleted"}
            )

        return response(
            400,
            {"message": "Unsupported operation"}
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
# EventBridge
# ------------------------------------------------------------




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
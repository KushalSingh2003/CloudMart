# import boto3
# import pymysql
# from flask import Flask, render_template

# app = Flask(__name__)

# REGION = "ap-south-1"
# ENVIRONMENT = "dev"


# def get_parameter(name, decrypt=False):
#     ssm = boto3.client("ssm", region_name=REGION)

#     response = ssm.get_parameter(
#         Name=name,
#         WithDecryption=decrypt
#     )

#     return response["Parameter"]["Value"]


# def get_db_connection():

#     endpoint = get_parameter(
#         f"/cloudmart/{ENVIRONMENT}/db-endpoint"
#     )

#     port = int(get_parameter(
#         f"/cloudmart/{ENVIRONMENT}/db-port"
#     ))

#     database = get_parameter(
#         f"/cloudmart/{ENVIRONMENT}/db-name"
#     )

#     username = get_parameter(
#         f"/cloudmart/{ENVIRONMENT}/db-username"
#     )

#     password = get_parameter(
#         f"/cloudmart/{ENVIRONMENT}/db-password",
#         decrypt=True
#     )

#     return pymysql.connect(
#         host=endpoint,
#         port=port,
#         user=username,
#         password=password,
#         database=database,
#         cursorclass=pymysql.cursors.DictCursor
#     )


# @app.route("/")
# def dashboard():

#     connection = get_db_connection()

#     try:
#         with connection.cursor() as cursor:

#             # Total products
#             cursor.execute(
#                 "SELECT COUNT(*) AS total FROM Products"
#             )
#             total_products = cursor.fetchone()["total"]

#             # Total customers
#             cursor.execute(
#                 "SELECT COUNT(*) AS total FROM Customers"
#             )
#             total_customers = cursor.fetchone()["total"]

#             # Total active orders
#             cursor.execute(
#                 """
#                 SELECT COUNT(*) AS total
#                 FROM Orders
#                 WHERE is_deleted = 0
#                 """
#             )
#             total_orders = cursor.fetchone()["total"]

#             # Total sales
#             cursor.execute(
#                 """
#                 SELECT COALESCE(SUM(total_amount), 0) AS total
#                 FROM Orders
#                 WHERE is_deleted = 0
#                 AND LOWER(status) != 'cancelled'
#                 """
#             )
#             total_sales = cursor.fetchone()["total"]

#             # Low-stock products
#             cursor.execute(
#                 """
#                 SELECT
#                     product_id,
#                     name,
#                     stock,
#                     price,
#                     status
#                 FROM Products
#                 WHERE stock <= 5
#                 ORDER BY stock ASC
#                 """
#             )
#             low_stock = cursor.fetchall()

#             # Recent orders
#             cursor.execute(
#                 """
#                 SELECT
#                     o.order_id,
#                     c.name AS customer_name,
#                     o.total_amount,
#                     o.status,
#                     o.created_at
#                 FROM Orders o
#                 LEFT JOIN Customers c
#                     ON o.user_id = c.user_id
#                 WHERE o.is_deleted = 0
#                 ORDER BY o.created_at DESC
#                 LIMIT 10
#                 """
#             )
#             recent_orders = cursor.fetchall()

#             # Best-selling products
#             cursor.execute(
#                 """
#                 SELECT
#                     product_id,
#                     product_name,
#                     SUM(quantity) AS total_quantity
#                 FROM Orders_Items
#                 GROUP BY product_id, product_name
#                 ORDER BY total_quantity DESC
#                 LIMIT 5
#                 """
#             )
#             best_selling = cursor.fetchall()

#             # Order status summary
#             cursor.execute(
#                 """
#                 SELECT
#                     status,
#                     COUNT(*) AS total
#                 FROM Orders
#                 WHERE is_deleted = 0
#                 GROUP BY status
#                 ORDER BY total DESC
#                 """
#             )
#             order_status = cursor.fetchall()

#         return render_template(
#             "dashboard.html",
#             total_products=total_products,
#             total_customers=total_customers,
#             total_orders=total_orders,
#             total_sales=total_sales,
#             low_stock=low_stock,
#             recent_orders=recent_orders,
#             best_selling=best_selling,
#             order_status=order_status
#         )

#     finally:
#         connection.close()


# if __name__ == "__main__":
#     app.run(
#         host="0.0.0.0",
#         port=80
#     )
from flask import Flask, render_template, request
import pymysql
import boto3

app = Flask(__name__)


def get_db_connection():
    ssm = boto3.client("ssm", region_name="ap-south-1")

    endpoint = ssm.get_parameter(
        Name="/cloudmart/dev/db-endpoint"
    )["Parameter"]["Value"]

    port = int(
        ssm.get_parameter(
            Name="/cloudmart/dev/db-port"
        )["Parameter"]["Value"]
    )

    database = ssm.get_parameter(
        Name="/cloudmart/dev/db-name"
    )["Parameter"]["Value"]

    username = ssm.get_parameter(
        Name="/cloudmart/dev/db-username"
    )["Parameter"]["Value"]

    password = ssm.get_parameter(
        Name="/cloudmart/dev/db-password",
        WithDecryption=True
    )["Parameter"]["Value"]

    return pymysql.connect(
        host=endpoint,
        port=port,
        user=username,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route("/")
def dashboard():

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) AS total FROM Products"
            )
            total_products = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM Customers"
            )
            total_customers = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM Orders
                WHERE is_deleted = 0
            """)
            total_orders = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) AS total
                FROM Orders
                WHERE is_deleted = 0
                AND LOWER(status) != 'cancelled'
            """)
            total_sales = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT
                    o.order_id,
                    c.name AS customer_name,
                    o.total_amount,
                    o.status,
                    o.created_at
                FROM Orders o
                JOIN Customers c
                    ON o.user_id = c.user_id
                WHERE o.is_deleted = 0
                ORDER BY o.created_at DESC
                LIMIT 10
            """)
            recent_orders = cursor.fetchall()

            cursor.execute("""
                SELECT
                    status,
                    COUNT(*) AS total
                FROM Orders
                WHERE is_deleted = 0
                GROUP BY status
            """)
            order_status = cursor.fetchall()

            cursor.execute("""
                SELECT
                    oi.product_id,
                    oi.product_name,
                    SUM(oi.quantity) AS total_quantity
                FROM Orders_Items oi
                JOIN Orders o
                    ON oi.order_id = o.order_id
                WHERE o.is_deleted = 0
                AND LOWER(o.status) != 'cancelled'
                GROUP BY oi.product_id, oi.product_name
                ORDER BY total_quantity DESC
                LIMIT 5
            """)
            best_selling = cursor.fetchall()

            cursor.execute("""
                SELECT
                    product_id,
                    name,
                    stock
                FROM Products
                WHERE stock <= 5
                ORDER BY stock ASC
            """)
            low_stock = cursor.fetchall()

        return render_template(
            "dashboard.html",
            total_products=total_products,
            total_customers=total_customers,
            total_orders=total_orders,
            total_sales=total_sales,
            recent_orders=recent_orders,
            order_status=order_status,
            best_selling=best_selling,
            low_stock=low_stock
        )

    finally:
        conn.close()


@app.route("/products")
def products():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            if search:

                cursor.execute("""
                    SELECT
                        p.product_id,
                        p.name,
                        p.description,
                        p.price,
                        p.stock,
                        p.status,
                        c.name AS category_name
                    FROM Products p
                    LEFT JOIN Category c
                        ON p.category_id = c.category_id
                    WHERE p.name LIKE %s
                       OR p.description LIKE %s
                    ORDER BY p.product_id DESC
                """, (
                    f"%{search}%",
                    f"%{search}%"
                ))

            else:

                cursor.execute("""
                    SELECT
                        p.product_id,
                        p.name,
                        p.description,
                        p.price,
                        p.stock,
                        p.status,
                        c.name AS category_name
                    FROM Products p
                    LEFT JOIN Category c
                        ON p.category_id = c.category_id
                    ORDER BY p.product_id DESC
                """)

            products = cursor.fetchall()

        return render_template(
            "products.html",
            products=products,
            search=search
        )

    finally:
        conn.close()
@app.route("/products/<int:product_id>")
def product_details(product_id):

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    p.product_id,
                    p.name,
                    p.description,
                    p.price,
                    p.stock,
                    p.status,
                    p.category_id,
                    c.name AS category_name
                FROM Products p
                LEFT JOIN Category c
                    ON p.category_id = c.category_id
                WHERE p.product_id = %s
            """, (product_id,))

            product = cursor.fetchone()

            if not product:
                return "Product not found", 404

            return render_template(
                "product-details.html",
                product=product
            )

    finally:
        connection.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=80
    )
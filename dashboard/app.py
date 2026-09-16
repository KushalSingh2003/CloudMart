import boto3
import pymysql
from flask import Flask, render_template

app = Flask(__name__)

REGION = "ap-south-1"
ENVIRONMENT = "dev"


def get_parameter(name, decrypt=False):
    ssm = boto3.client("ssm", region_name=REGION)

    response = ssm.get_parameter(
        Name=name,
        WithDecryption=decrypt
    )

    return response["Parameter"]["Value"]


def get_db_connection():

    endpoint = get_parameter(
        f"/cloudmart/{ENVIRONMENT}/db-endpoint"
    )

    port = int(get_parameter(
        f"/cloudmart/{ENVIRONMENT}/db-port"
    ))

    database = get_parameter(
        f"/cloudmart/{ENVIRONMENT}/db-name"
    )

    username = get_parameter(
        f"/cloudmart/{ENVIRONMENT}/db-username"
    )

    password = get_parameter(
        f"/cloudmart/{ENVIRONMENT}/db-password",
        decrypt=True
    )

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

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            # Total products
            cursor.execute(
                "SELECT COUNT(*) AS total FROM Products"
            )
            total_products = cursor.fetchone()["total"]

            # Total customers
            cursor.execute(
                "SELECT COUNT(*) AS total FROM Customers"
            )
            total_customers = cursor.fetchone()["total"]

            # Total active orders
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM Orders
                WHERE is_deleted = 0
                """
            )
            total_orders = cursor.fetchone()["total"]

            # Total sales
            cursor.execute(
                """
                SELECT COALESCE(SUM(total_amount), 0) AS total
                FROM Orders
                WHERE is_deleted = 0
                AND LOWER(status) != 'cancelled'
                """
            )
            total_sales = cursor.fetchone()["total"]

            # Low-stock products
            cursor.execute(
                """
                SELECT
                    product_id,
                    name,
                    stock,
                    price,
                    status
                FROM Products
                WHERE stock <= 5
                ORDER BY stock ASC
                """
            )
            low_stock = cursor.fetchall()

            # Recent orders
            cursor.execute(
                """
                SELECT
                    o.order_id,
                    c.name AS customer_name,
                    o.total_amount,
                    o.status,
                    o.created_at
                FROM Orders o
                LEFT JOIN Customers c
                    ON o.user_id = c.user_id
                WHERE o.is_deleted = 0
                ORDER BY o.created_at DESC
                LIMIT 10
                """
            )
            recent_orders = cursor.fetchall()

            # Best-selling products
            cursor.execute(
                """
                SELECT
                    product_id,
                    product_name,
                    SUM(quantity) AS total_quantity
                FROM Orders_Items
                GROUP BY product_id, product_name
                ORDER BY total_quantity DESC
                LIMIT 5
                """
            )
            best_selling = cursor.fetchall()

            # Order status summary
            cursor.execute(
                """
                SELECT
                    status,
                    COUNT(*) AS total
                FROM Orders
                WHERE is_deleted = 0
                GROUP BY status
                ORDER BY total DESC
                """
            )
            order_status = cursor.fetchall()

        return render_template(
            "dashboard.html",
            total_products=total_products,
            total_customers=total_customers,
            total_orders=total_orders,
            total_sales=total_sales,
            low_stock=low_stock,
            recent_orders=recent_orders,
            best_selling=best_selling,
            order_status=order_status
        )

    finally:
        connection.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=80
    )
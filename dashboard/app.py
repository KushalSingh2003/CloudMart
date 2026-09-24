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

from flask import Flask, render_template, request, redirect, session, url_for
from functools import wraps
import os
import pymysql
import boto3
from datetime import datetime
from zoneinfo import ZoneInfo
app = Flask(__name__)
REPORTS_BUCKET = os.environ["REPORTS_BUCKET_NAME"]
app.secret_key = os.environ["FLASK_SECRET_KEY"]
def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "ADMIN":
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


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

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user_id = request.form.get("user_id", "").strip()
        token = request.form.get("token", "").strip()

        if not user_id or not token:
            return render_template(
                "login.html",
                error="User ID and token are required."
            )

        conn = get_db_connection()

        try:
            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT user_id, name, email, Role
                    FROM Customers
                    WHERE user_id = %s
                    AND token = %s
                    """,
                    (user_id, token)
                )

                user = cursor.fetchone()

            if not user:
                return render_template(
                    "login.html",
                    error="Invalid User ID or token."
                )

            if not user["Role"] or user["Role"].upper() != "ADMIN":
                return render_template(
                    "login.html",
                    error="Access denied. Admin access required."
                )
                    

            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["role"] = user["Role"]

            return redirect(url_for("dashboard"))

        finally:
            conn.close()

    return render_template("login.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/")
@admin_required
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
        today = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).date().isoformat()

        return render_template(
            "dashboard.html",
            total_products=total_products,
            total_customers=total_customers,
            total_orders=total_orders,
            total_sales=total_sales,
            recent_orders=recent_orders,
            order_status=order_status,
            best_selling=best_selling,
            low_stock=low_stock,
            today=today
        )

    finally:
        conn.close()


@app.route("/products")
@admin_required
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
@admin_required
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
@app.route("/customers")
@admin_required
def customers():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            if search:

                cursor.execute("""
                    SELECT
                        user_id,
                        name,
                        email,
                        phone,
                        Role,
                        created_at
                    FROM Customers
                    WHERE name LIKE %s
                       OR email LIKE %s
                       OR phone LIKE %s
                    ORDER BY user_id DESC
                """, (
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                ))

            else:

                cursor.execute("""
                    SELECT
                        user_id,
                        name,
                        email,
                        phone,
                        Role,
                        created_at
                    FROM Customers
                    ORDER BY user_id DESC
                """)

            customers = cursor.fetchall()

        return render_template(
            "customers.html",
            customers=customers,
            search=search
        )

    finally:
        conn.close()


@app.route("/customers/<int:user_id>")
@admin_required
def customer_details(user_id):

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    user_id,
                    name,
                    email,
                    phone,
                    Role,
                    created_at
                FROM Customers
                WHERE user_id = %s
            """, (user_id,))

            customer = cursor.fetchone()

            if not customer:
                return "Customer not found", 404

            cursor.execute("""
                SELECT
                    order_id,
                    total_amount,
                    status,
                    created_at,
                    changed_at,
                    cancelled_at,
                    cancel_reason
                FROM Orders
                WHERE user_id = %s
                  AND is_deleted = 0
                ORDER BY created_at DESC
            """, (user_id,))

            orders = cursor.fetchall()

        return render_template(
            "customer-details.html",
            customer=customer,
            orders=orders
        )

    finally:
        conn.close()
@app.route("/orders")
@admin_required

def orders():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            if search:

                cursor.execute("""
                    SELECT
                        o.order_id,
                        o.user_id,
                        c.name AS customer_name,
                        o.total_amount,
                        o.status,
                        o.created_at
                    FROM Orders o
                    LEFT JOIN Customers c
                        ON o.user_id = c.user_id
                    WHERE o.is_deleted = 0
                      AND (
                          CAST(o.order_id AS CHAR) LIKE %s
                          OR c.name LIKE %s
                          OR o.status LIKE %s
                      )
                    ORDER BY o.created_at DESC
                """, (
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                ))

            else:

                cursor.execute("""
                    SELECT
                        o.order_id,
                        o.user_id,
                        c.name AS customer_name,
                        o.total_amount,
                        o.status,
                        o.created_at
                    FROM Orders o
                    LEFT JOIN Customers c
                        ON o.user_id = c.user_id
                    WHERE o.is_deleted = 0
                    ORDER BY o.created_at DESC
                """)

            orders = cursor.fetchall()

        return render_template(
            "orders.html",
            orders=orders,
            search=search
        )

    finally:
        conn.close()


@app.route("/orders/<int:order_id>")
@admin_required
def order_details(order_id):

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            # Order information
            cursor.execute("""
                SELECT
                    o.order_id,
                    o.user_id,
                    c.name AS customer_name,
                    c.email AS customer_email,
                    c.phone AS customer_phone,
                    o.total_amount,
                    o.status,
                    o.is_deleted,
                    o.created_at,
                    o.changed_at,
                    o.cancelled_at,
                    o.cancel_reason
                FROM Orders o
                LEFT JOIN Customers c
                    ON o.user_id = c.user_id
                WHERE o.order_id = %s
            """, (order_id,))

            order = cursor.fetchone()

            if not order:
                return "Order not found", 404

            # Order items
            cursor.execute("""
                SELECT
                    oi.order_item_id,
                    oi.product_id,
                    oi.product_name,
                    oi.quantity,
                    oi.price,
                    (oi.quantity * oi.price) AS subtotal
                FROM Orders_Items oi
                WHERE oi.order_id = %s
                ORDER BY oi.order_item_id
            """, (order_id,))

            items = cursor.fetchall()

        return render_template(
            "order-details.html",
            order=order,
            items=items
        )

    finally:
        conn.close()
@app.route("/download-report")
@admin_required
def download_report():

    report_date = request.args.get("date")

    if not report_date:
        return "Please select a report date.", 400

    try:
        selected_date = datetime.strptime(
            report_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return "Invalid date format.", 400

    # Current date in India
    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date()

    # Prevent future dates
    if selected_date > today:
        return "Future dates are not allowed.", 400

    # S3 file name
    file_key = f"reports/daily-report-{report_date}.csv"

    s3 = boto3.client(
        "s3",
        region_name="ap-south-1"
    )

    try:

        # Check whether the report exists
        s3.head_object(
            Bucket=REPORTS_BUCKET,
            Key=file_key
        )

        # Generate temporary download URL
        download_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": REPORTS_BUCKET,
                "Key": file_key
            },
            ExpiresIn=300
        )

        return redirect(download_url)

    except s3.exceptions.ClientError as e:

        error_code = e.response["Error"]["Code"]

        if error_code in ["404", "NoSuchKey", "NotFound"]:

            return (
                f"Report for {report_date} is not available yet.",
                404
            )

        return "Unable to download the report.", 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=80
    )
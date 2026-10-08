
import os
import json
from decimal import Decimal, InvalidOperation

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

EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
MAX_ORDER_ITEMS = int(os.environ["MAX_ORDER_ITEMS"])


# ------------------------------------------------------------
# AWS clients
# ------------------------------------------------------------

ssm = boto3.client("ssm")
events = boto3.client("events")
cloudwatch = boto3.client("cloudwatch")

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
# Publish EventBridge event
# ------------------------------------------------------------

def publish_event(detail_type, detail):

    try:

        result = events.put_events(
            Entries=[
                {
                    "EventBusName": EVENT_BUS_NAME,
                    "Source": "cloudmart",
                    "DetailType": detail_type,
                    "Detail": json.dumps(
                        detail,
                        default=str
                    )
                }
            ]
        )

        if result.get("FailedEntryCount", 0) > 0:

            print(
                f"EventBridge failed to publish: {detail_type}"
            )

        else:

            print(
                f"EventBridge event published: {detail_type}"
            )

    except Exception as e:

        print(
            f"EventBridge error for {detail_type}: {str(e)}"
        )
# ------------------------------------------------------------
# Publish CloudWatch business metric
# ------------------------------------------------------------

def publish_metric(metric_name):
    try:
        cloudwatch.put_metric_data(
            Namespace="CloudMart/Business",
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": 1,
                    "Unit": "Count"
                }
            ]
        )

        print(f"CloudWatch metric published: {metric_name}")

    except Exception as e:
        print(f"CloudWatch metric error for {metric_name}: {str(e)}")


# ------------------------------------------------------------
# Lambda handler
# ------------------------------------------------------------

def get_authenticated_user(event):
    

    authorizer = (
        event.get("requestContext", {}).get("authorizer", {})
        or {}
    )

    user_id = authorizer.get("user_id")
    role = authorizer.get("role")

    if user_id is None:
        return None, None

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None, None

    return user_id, role


def lambda_handler(event, context):

    print("HTTP METHOD:", event.get("httpMethod"))
    print("PATH PARAMETERS:", event.get("pathParameters"))
    print("BODY:", event.get("body"))

    connection = None

    try:

        connection = get_connection()

        http_method = event.get("httpMethod")

        path_parameters = event.get("pathParameters") or {}
        
        order_id = path_parameters.get("orderId")

        if order_id is not None:
            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                return response(
                    400,
                    {
                        "message": "OrderID must be a valid integer"
                    }
                )

            if order_id <= 0:
                return response(
                    400,
                    {
                        "message": "OrderID must be a positive integer"
                    }
                )

        

        body = event.get("body")

        if body:
            body = json.loads(body)
            if not isinstance(body, dict):
                return response(
                    400,
                    {
                        "message": "Request body must be a JSON object"
                    }
                )
        #getting user_id and role from header

        user_id, role = get_authenticated_user(event)

        if user_id is None:
            return response(
                401,
                {
                    "message": "Authenticated user not found"
                }
            )

        if role not in ("CUSTOMER", "ADMIN"):
            return response(
                403,
                {
                    "message": "Invalid user role"
                }
            )


        # ====================================================
        # GET /orders
        # ====================================================
        # CUSTOMER -> only their own orders
        # ADMIN    -> all orders
        # ====================================================

        if http_method == "GET" and not order_id:

            query = """
                SELECT
                    order_id AS OrderID,
                    user_id AS UserID,
                    total_amount AS TotalAmount,
                    status AS Status,
                    is_deleted AS IsDeleted,
                    created_at AS CreatedAt,
                    changed_at AS ChangedAt,
                    cancelled_at AS CancelledAt,
                    cancel_reason AS CancelReason
                FROM Orders
                WHERE is_deleted = FALSE
            """

            params = []

            if role == "CUSTOMER":
                query += "AND user_id = %s" # this adds the partcular user id to the above query
                params.append(user_id)
            # if the user is admin , then no changes  in the query is made

            query += " ORDER BY created_at DESC"

            with connection.cursor() as cursor:
                cursor.execute(query, params)
                orders = cursor.fetchall()

            connection.commit()

            return response(200, orders)


        # ====================================================
        # GET /orders/{orderId}
        # ====================================================
        # CUSTOMER -> only their own order
        # ADMIN    -> any order
        # ====================================================

        if http_method == "GET" and order_id:

            with connection.cursor() as cursor:

                if role == "CUSTOMER":
                    cursor.execute(
                        """
                        SELECT
                            order_id AS OrderID,
                            user_id AS UserID,
                            total_amount AS TotalAmount,
                            status AS Status,
                            is_deleted AS IsDeleted,
                            created_at AS CreatedAt,
                            changed_at AS ChangedAt,
                            cancelled_at AS CancelledAt,
                            cancel_reason AS CancelReason
                        FROM Orders
                        WHERE order_id = %s
                          AND user_id = %s
                          AND is_deleted = FALSE
                        """,
                        (order_id, user_id)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT
                            order_id AS OrderID,
                            user_id AS UserID,
                            total_amount AS TotalAmount,
                            status AS Status,
                            is_deleted AS IsDeleted,
                            created_at AS CreatedAt,
                            changed_at AS ChangedAt,
                            cancelled_at AS CancelledAt,
                            cancel_reason AS CancelReason
                        FROM Orders
                        WHERE order_id = %s
                          AND is_deleted = FALSE
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
                # need to add all the items that were present in that orders
                

                cursor.execute(
                    """
                    SELECT
                        order_item_id AS OrderItemID,
                        product_id AS ProductID,
                        product_name AS ProductName,
                        quantity AS Quantity,
                        price AS Price
                    FROM Orders_Items
                    WHERE order_id = %s
                    """,
                    (order_id,)
                )
                # adding a key called Items in which all the items related to that order is present

                order["Items"] = cursor.fetchall()

            connection.commit()

            return response(200, order)


        # ====================================================
        # POST /orders
        # ====================================================
        # Customer information is NOT accepted from the client.
        # The authenticated user_id from the authorizer is used.
        # ====================================================

        if http_method == "POST":

            if not body:
                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )

            items = body.get("Items")
           

            if not isinstance(items, list) or not items:
                return response(
                    400,
                    {
                        "message": "Items must be a non-empty list"
                    }
                )
            if len(items) > MAX_ORDER_ITEMS:
                return response(
                    400,
                    {
                        "message": f"Order cannot contain more than {MAX_ORDER_ITEMS} items"}
                )

            with connection.cursor() as cursor:

                total_amount = Decimal("0.00")
                item_rows = []

                # ------------------------------------------------
                # Validate items and combine duplicate ProductIDs
                # ------------------------------------------------

                combined_items = {}

                for item in items:

                    if not isinstance(item, dict):
                        connection.rollback()
                        return response(
                            400,
                            {
                                "message": "Each item must be an object"
                            }
                        )

                    product_id = item.get("ProductID")
                    quantity = item.get("Quantity")

                    if (
                        isinstance(product_id, bool)
                        or not isinstance(product_id, int)
                        or product_id <= 0
                    ):
                        connection.rollback()
                        return response(
                            400,
                            {
                                "message": "ProductID must be a positive integer"
                            }
                        )

                    if (
                        isinstance(quantity, bool)
                        or not isinstance(quantity, int)
                        or quantity <= 0
                        
                    ):
                        connection.rollback()
                        return response(
                            400,
                            {
                                "message": f"Quantity must be a positive integer"
                            }
                        )

                    if product_id in combined_items:
                        combined_items[product_id] += quantity
                    else:
                        combined_items[product_id] = quantity

                # ------------------------------------------------
                # Validate products and calculate total
                # ------------------------------------------------

                for product_id, quantity in sorted(combined_items.items()):

                    cursor.execute(
                        """
                        SELECT
                            product_id,
                            name,
                            price,
                            stock,
                            max_order_quantity 
                        FROM Products
                        WHERE product_id = %s
                          AND status = 'ACTIVE'
                        FOR UPDATE
                        """,
                        (product_id,)
                    )

                    product = cursor.fetchone()

                    if not product:
                        connection.rollback()
                        publish_event(
                            "OrderFailed",
                            {
                                "customer_id": user_id,
                                "product_id": product_id,
                                "requested_quantity": quantity,
                                "reason": "Product not found"
                            }
                        )
                        publish_metric("OrdersFailed")
                        return response(
                            404,
                            {
                                "message": "Product not found",
                                "ProductID": product_id
                            }
                        )
                    if quantity > product["max_order_quantity"]:
                        connection.rollback()
                        publish_event(
                            "OrderFailed",
                            {
                                "customer_id": user_id,
                                "product_id": product_id,
                                "requested_quantity": quantity,
                                "max_order_quantity": product["max_order_quantity"],
                                "reason": "Maximum order quantity exceeded"
                            }
                        )
                        publish_metric("OrdersFailed")

                        return response(
                            400,
                            {
                                "message": "Requested quantity exceeds the maximum allowed quantity for this product",
                                "ProductID": product_id,
                                "RequestedQuantity": quantity,
                                "MaxOrderQuantity": product["max_order_quantity"]
                            }
                        )

                    if product["stock"] < quantity:
                        connection.rollback()
                        publish_event(
                            "OrderFailed",
                            {
                                "customer_id": user_id,
                                "product_id": product_id,
                                "requested_quantity": quantity,
                                "available_stock": product["stock"],
                                "reason": "Insufficient stock"
                            }
                        )
                        publish_metric("OrdersFailed")
                        return response(
                            400,
                            {
                                "message": "Order Failed",
                                
                            }
                        )

                    price = Decimal(str(product["price"]))
                    total_amount += price * quantity

                    item_rows.append(
                        {
                            "product_id": product_id,
                            "product_name": product["name"],
                            "quantity": quantity,
                            "price": price
                        }
                    )

                # ------------------------------------------------
                # Create order using authenticated user_id
                # ------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO Orders
                    (
                        user_id,
                        total_amount,
                        status,
                        is_deleted
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        'PENDING',
                        FALSE
                    )
                    """,
                    (user_id, total_amount)
                )
                # order_id of the new order created

                new_order_id = cursor.lastrowid

                # ------------------------------------------------
                # Create order items and reduce stock
                # ------------------------------------------------

                for item in item_rows:

                    cursor.execute(
                        """
                        INSERT INTO Orders_Items
                        (
                            order_id,
                            product_id,
                            product_name,
                            quantity,
                            price
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            new_order_id,
                            item["product_id"],
                            item["product_name"],
                            item["quantity"],
                            item["price"]
                        )
                    )

                    cursor.execute(
                        """
                        UPDATE Products
                        SET stock = stock - %s
                        WHERE product_id = %s
                          AND stock >= %s
                          AND status = 'ACTIVE'
                        """,
                        (
                            item["quantity"],
                            item["product_id"],
                            item["quantity"]
                        )
                    )

                    if cursor.rowcount == 0:
                        connection.rollback()
                        publish_event(
                            "OrderFailed",
                            {
                                "customer_id": user_id,
                                "product_id": item["product_id"],
                                "requested_quantity": item["quantity"],
                                "reason": "Unable to update stock"
                            }
                        )
                        publish_metric("OrdersFailed")
                        return response(
                            400,
                            {
                                "message": "Unable to update stock",
                                "ProductID": item["product_id"]
                            }
                        )

                # ------------------------------------------------
                # Initial order history
                # ------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO Orders_History
                    (
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        'PENDING',
                        FALSE
                    )
                    """,
                    (
                        new_order_id,
                        user_id,
                        total_amount
                    )
                )

            connection.commit()

            publish_event(
                "OrderCreated",
                {
                    "order_id": new_order_id,
                    "customer_id": user_id,
                    "total_amount": total_amount,
                    "status": "PENDING"
                }
            )
            publish_metric("OrdersCreated")

            return response(
                201,
                {
                    "message": "Order created",
                    "OrderID": new_order_id,
                    "CustomerID": user_id,
                    "TotalAmount": total_amount
                }
            )


        # ====================================================
        # PATCH /orders/{orderId}
        # ====================================================
        # CUSTOMER -> can only cancel their own order.
        # ADMIN    -> can partially update any order.
        # Cancellation restores product stock exactly once.
        # ====================================================

        if http_method == "PATCH" and order_id:

            if not body:
                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )

            allowed_fields = {
                "USERID",
                "TotalAmount",
                "Status",
                "IsDeleted",
                "CancelReason"
            }

            invalid_fields = [
                field for field in body
                if field not in allowed_fields
            ]

            if invalid_fields:
                return response(
                    400,
                    {
                        "message": "Invalid fields",
                        "fields": invalid_fields
                    }
                )

            # Customers cannot modify another customer's order and
            # cannot change CustomerID, TotalAmount or IsDeleted.
            if role == "CUSTOMER":

                customer_allowed_fields = {
                    "Status",
                    "CancelReason"
                }
                # if the customer tries to modify any other field, return an error
                customer_invalid_fields = [
                    field
                    for field in body # going through the fields in the request body
                    if field not in customer_allowed_fields
                ]

                if customer_invalid_fields:
                    return response(
                        403,
                        {
                            "message": "Customers can only cancel their own orders",
                            "fields": customer_invalid_fields
                        }
                    )

                if body.get("Status") != "CANCELLED":
                    return response(
                        400,
                        {
                            "message": "Customers can only change order status to CANCELLED"
                        }
                    )

            with connection.cursor() as cursor:

                if role == "CUSTOMER":
                    cursor.execute(
                        """
                        SELECT
                            order_id,
                            user_id,
                            total_amount,
                            status,
                            is_deleted,
                            cancelled_at,
                            cancel_reason
                        FROM Orders
                        WHERE order_id = %s
                          AND user_id = %s
                        FOR UPDATE
                        """,
                        (order_id, user_id)# user id makes sure tghat customers can only access their own orders
                    )
                else:
                    cursor.execute(
                        """
                        SELECT
                            order_id,
                            user_id,
                            total_amount,
                            status,
                            is_deleted,
                            cancelled_at,
                            cancel_reason
                        FROM Orders
                        WHERE order_id = %s
                        FOR UPDATE
                        """,
                        (order_id,)
                    )

                existing_order = cursor.fetchone()

                if not existing_order:
                    connection.rollback()
                    return response(
                        404,
                        {
                            "message": "Order not found"
                        }
                    )

                if existing_order["is_deleted"]:
                    connection.rollback()
                    return response(
                        404,
                        {
                            "message": "Order is already deleted"
                        }
                    )

                user_id = existing_order["user_id"]
                total_amount = existing_order["total_amount"]
                old_status = existing_order["status"]
                status = existing_order["status"]
                is_deleted = existing_order["is_deleted"]
                cancel_reason = existing_order["cancel_reason"]

                # ------------------------------------------------
                # ADMIN: Customer ID
                # ------------------------------------------------
                # the admin can change the customer id of an order, but it must be a valid customer id

                if role == "ADMIN" and "USERID" in body:

                    user_id = body["USERID"]

                    if (
                        isinstance(user_id, bool)
                        or not isinstance(user_id, int)
                        or user_id <= 0
                    ):
                        connection.rollback()
                        return response(
                            400,
                            {
                                "message": "CustomerID must be a positive integer"
                            }
                        )

                    cursor.execute(
                        """
                        SELECT user_id
                        FROM Customers
                        WHERE user_id = %s
                        """,
                        (user_id,)
                    )

                    if not cursor.fetchone():
                        connection.rollback()
                        return response(
                            404,
                            {
                                "message": "Customer not found"
                            }
                        )

                # ------------------------------------------------
                # ADMIN: Total amount
                # ------------------------------------------------

                if role == "ADMIN" and "TotalAmount" in body:

                    try:
                        total_amount = Decimal(str(body["TotalAmount"]))
                    except (
                        ValueError,
                        TypeError,
                        InvalidOperation
                    ):
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
                # Status
                # ------------------------------------------------

                if "Status" in body:

                    status = body["Status"]
                    print(
                        f"ORDER STATUS DEBUG: order_id={order_id}, "
                        f"old_status={old_status}, new_status={status}"
                    )

                    if status not in (
                        "PENDING",
                        "CONFIRMED",
                        "COMPLETED",
                        "CANCELLED"
                    ):
                        connection.rollback()
                        return response(
                            400,
                            {
                                "message":
                                "Status must be one of PENDING, CONFIRMED, COMPLETED, CANCELLED"
                            }
                        )

                # ------------------------------------------------
                # Cancel reason
                # ------------------------------------------------

                if "CancelReason" in body:
                    cancel_reason = body["CancelReason"]

                # ------------------------------------------------
                # ADMIN: Soft delete
                # ------------------------------------------------

                if role == "ADMIN" and "IsDeleted" in body:

                    if not isinstance(body["IsDeleted"], bool):
                        connection.rollback()
                        return response(
                            400,
                            {
                                "message": "IsDeleted must be true or false"
                            }
                        )

                    is_deleted = body["IsDeleted"]

                # ------------------------------------------------
                # Cancellation handling
                # ------------------------------------------------
                # Restore stock only on the first transition to
                # CANCELLED. Orders_Items is locked as part of the
                # same transaction.
                # ------------------------------------------------

                if (
                    status == "CANCELLED"
                    and old_status != "CANCELLED"
                ):

                    cursor.execute(
                        """
                        SELECT
                            product_id,
                            quantity
                        FROM Orders_Items
                        WHERE order_id = %s
                        FOR UPDATE
                        """,
                        (order_id,)
                    )

                    order_items = cursor.fetchall()

                    for item in order_items:
                        cursor.execute(
                            """
                            UPDATE Products
                            SET stock = stock + %s
                            WHERE product_id = %s
                            """,
                            (
                                item["quantity"],
                                item["product_id"]
                            )
                        )

                    cursor.execute(
                        """
                        UPDATE Orders
                        SET user_id = %s,
                            total_amount = %s,
                            status = %s,
                            is_deleted = %s,
                            changed_at = CURRENT_TIMESTAMP,
                            cancelled_at = CURRENT_TIMESTAMP,
                            cancel_reason = %s
                        WHERE order_id = %s
                        """,
                        (
                            user_id,
                            total_amount,
                            status,
                            is_deleted,
                            cancel_reason,
                            order_id
                        )
                    )
                elif (
                    old_status == "CANCELLED"
                    and status != "CANCELLED"
                ):
                    cursor.execute(
                        """
                        SELECT
                            product_id,
                            quantity
                        FROM Orders_Items
                        WHERE order_id = %s
                        FOR UPDATE
                        """,
                        (order_id,)
                    )

                    order_items = cursor.fetchall()

                    for item in order_items:
                        cursor.execute(
                            """
                            UPDATE Products
                            SET stock = stock - %s
                            WHERE product_id = %s
                            AND stock >= %s
                            """,
                            (
                                item["quantity"],
                                item["product_id"],
                                item["quantity"]
                            )
                        )

                        if cursor.rowcount == 0:
                            connection.rollback()
                            return response(
                                400,
                                {
                                    "message": "Insufficient stock to reactivate order",
                                    "ProductID": item["product_id"],
                                    "RequiredQuantity": item["quantity"]
                                }

                        )
                    cursor.execute(
                                """
                                UPDATE Orders
                                SET user_id = %s,
                                    total_amount = %s,
                                    status = %s,
                                    is_deleted = %s,
                                    changed_at = CURRENT_TIMESTAMP,
                                    cancel_reason = %s
                                WHERE order_id = %s
                                """,
                                (
                                    user_id,
                                    total_amount,
                                    status,
                                    is_deleted,
                                    cancel_reason,
                                    order_id
                                )
                            )

                else:

                    cursor.execute(
                        """
                        UPDATE Orders
                        SET user_id = %s,
                            total_amount = %s,
                            status = %s,
                            is_deleted = %s,
                            changed_at = CURRENT_TIMESTAMP,
                            cancel_reason = %s
                        WHERE order_id = %s
                        """,
                        (
                            user_id,
                            total_amount,
                            status,
                            is_deleted,
                            cancel_reason,
                            order_id
                        )
                    )

                # ------------------------------------------------
                # Add history snapshot
                # ------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO Orders_History
                    (
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted,
                        cancelled_at,
                        cancelled_reason
                    )
                    SELECT
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted,
                        cancelled_at,
                        cancel_reason
                    FROM Orders
                    WHERE order_id = %s
                    """,
                    (order_id,)
                )

            connection.commit()

            if old_status != status:
                publish_event(
                    "OrderStatusChanged",
                    {
                        "order_id": int(order_id),
                        "old_status": old_status,
                        "new_status": status
                    }
                )

                if status == "CONFIRMED":
                    publish_event(
                        "OrderConfirmed",
                        {
                            "order_id": int(order_id),
                            "old_status": old_status,
                            "status": "CONFIRMED"
                        }
                    )
                    publish_metric("OrdersConfirmed")
                if status == "COMPLETED":
                   publish_metric("OrdersCompleted")
                if status == "CANCELLED":
                    publish_metric("OrdersCancelled")

            return response(
                200,
                {
                    "message": "Order updated",
                    "OrderID": int(order_id)
                }
            )


        # ====================================================
        # PUT /orders/{orderId}
        # ====================================================
        # Kept for compatibility. API Gateway/RBAC currently does
        # not allow PUT, so this should not be reachable normally.
        # ====================================================

        if http_method == "PUT" and order_id:

            if not body:
                return response(
                    400,
                    {
                        "message": "Request body is required"
                    }
                )

            if role == "CUSTOMER":
                return response(
                    403,
                    {
                        "message": "Customers are not allowed to use PUT for orders"
                    }
                )

            required_fields = [
                "USERID",
                "TotalAmount",
                "Status"
            ]

            missing_fields = [
                field for field in required_fields
                if field not in body
            ]

            if missing_fields:
                return response(
                    400,
                    {
                        "message": "Missing required fields",
                        "fields": missing_fields
                    }
                )

            try:
                user_id = int(body["USERID"])
                total_amount = Decimal(str(body["TotalAmount"]))
            except (
                ValueError,
                TypeError,
                InvalidOperation
            ):
                return response(
                    400,
                    {
                        "message": "Invalid USERID or TotalAmount"
                    }
                )

            status = body["Status"]

            if user_id <= 0:
                return response(
                    400,
                    {
                        "message": "USERID must be a positive integer"
                    }
                )

            if total_amount < 0:
                return response(
                    400,
                    {
                        "message": "TotalAmount cannot be negative"
                    }
                )

            if status not in (
                "PENDING",
                "CONFIRMED",
                "COMPLETED",
                "CANCELLED"
            ):
                return response(
                    400,
                    {
                        "message": "Invalid status"
                    }
                )

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        order_id,
                        status
                    FROM Orders
                    WHERE order_id = %s
                      AND is_deleted = FALSE
                    FOR UPDATE
                    """,
                    (order_id,)
                )

                existing_order = cursor.fetchone()

                if not existing_order:
                    connection.rollback()
                    return response(
                        404,
                        {
                            "message": "Active order not found"
                        }
                    )

                old_status = existing_order["status"]

                # If PUT ever becomes enabled, cancellation must also
                # restore stock exactly once.
                if status == "CANCELLED" and old_status != "CANCELLED":

                    cursor.execute(
                        """
                        SELECT product_id, quantity
                        FROM Orders_Items
                        WHERE order_id = %s
                        FOR UPDATE
                        """,
                        (order_id,)
                    )

                    order_items = cursor.fetchall()

                    for item in order_items:
                        cursor.execute(
                            """
                            UPDATE Products
                            SET stock = stock + %s
                            WHERE product_id = %s
                            """,
                            (
                                item["quantity"],
                                item["product_id"]
                            )
                        )

                cursor.execute(
                    """
                    UPDATE Orders
                    SET user_id = %s,
                        total_amount = %s,
                        status = %s,
                        changed_at = CURRENT_TIMESTAMP,
                        cancelled_at = CASE
                            WHEN %s = 'CANCELLED'
                            THEN COALESCE(cancelled_at, CURRENT_TIMESTAMP)
                            ELSE cancelled_at
                        END,
                        cancel_reason = %s
                    WHERE order_id = %s
                    """,
                    (
                        user_id,
                        total_amount,
                        status,
                        status,
                        body.get("CancelReason"),
                        order_id
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO Orders_History
                    (
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted,
                        cancelled_at,
                        cancelled_reason
                    )
                    SELECT
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted,
                        cancelled_at,
                        cancel_reason
                    FROM Orders
                    WHERE order_id = %s
                    """,
                    (order_id,)
                )

            connection.commit()

            if old_status != status:
                publish_event(
                    "OrderStatusChanged",
                    {
                        "order_id": int(order_id),
                        "old_status": old_status,
                        "new_status": status
                    }
                )

            return response(
                200,
                {
                    "message": "Order updated",
                    "OrderID": int(order_id)
                }
            )


        # ====================================================
        # DELETE /orders/{orderId}
        # ====================================================
        # Admin-only through RBAC. Soft delete through is_deleted.
        # ====================================================

        if http_method == "DELETE" and order_id:

            if role != "ADMIN":
                return response(
                    403,
                    {
                        "message": "Only admins can delete orders"
                    }
                )

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted,
                        cancelled_at,
                        cancel_reason
                    FROM Orders
                    WHERE order_id = %s
                      AND is_deleted = FALSE
                    FOR UPDATE
                    """,
                    (order_id,)
                )

                existing_order = cursor.fetchone()

                if not existing_order:
                    connection.rollback()
                    return response(
                        404,
                        {
                            "message": "Active order not found"
                        }
                    )
                # Restore stock when deleting an order that was not already cancelled
                if existing_order["status"] != "CANCELLED":

                    cursor.execute(
                        """
                        SELECT product_id, quantity
                        FROM Orders_Items
                        WHERE order_id = %s
                        FOR UPDATE
                        """,
                        (order_id,)
                    )

                    order_items = cursor.fetchall()

                    for item in order_items:
                        cursor.execute(
                            """
                            UPDATE Products
                            SET stock = stock + %s
                            WHERE product_id = %s
                            """,
                            (
                                item["quantity"],
                                item["product_id"]
                            )
                        )

                cursor.execute(
                    """
                    UPDATE Orders
                    SET is_deleted = TRUE,
                        changed_at = CURRENT_TIMESTAMP
                    WHERE order_id = %s
                    """,
                    (order_id,)
                )

                cursor.execute(
                    """
                    INSERT INTO Orders_History
                    (
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted,
                        cancelled_at,
                        cancelled_reason
                    )
                    SELECT
                        order_id,
                        user_id,
                        total_amount,
                        status,
                        is_deleted,
                        cancelled_at,
                        cancel_reason
                    FROM Orders
                    WHERE order_id = %s
                    """,
                    (order_id,)
                )

            connection.commit()

            return response(
                200,
                {
                    "message": "Order soft deleted",
                    "OrderID": int(order_id)
                }
            )


        connection.rollback()

        return response(
            400,
            {
                "message": "Unsupported operation"
            }
        )


    except json.JSONDecodeError:

        if connection:
            connection.rollback()

        return response(
            400,
            {
                "message": "Invalid JSON request body"
            }
        )


    except pymysql.err.IntegrityError as e:

        if connection:
            connection.rollback()

        print(f"Database integrity error: {str(e)}")

        return response(
            400,
            {
                "message": "Database constraint violation"
            }
        )


    except pymysql.MySQLError as e:

        if connection:
            connection.rollback()

        print(f"Database error: {str(e)}")

        return response(
            500,
            {
                "message": "Database error"
            }
        )


    except Exception as e:

        if connection:
            connection.rollback()

        print(f"Unexpected error: {str(e)}")

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
# another comment

def response(status_code, body):

    return {
        "statusCode": status_code,

        "headers": {
            "Content-Type":
            "application/json"
        },

        "body": json.dumps(
            body,
            default=str
        )
    }
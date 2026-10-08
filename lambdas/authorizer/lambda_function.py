
import os
import re
import boto3
import pymysql


# ============================================================
# SSM Configuration
# ============================================================

DB_HOST_PARAMETER = os.environ["DB_HOST_PARAMETER"]
DB_PORT_PARAMETER = os.environ["DB_PORT_PARAMETER"]
DB_NAME_PARAMETER = os.environ["DB_NAME_PARAMETER"]
DB_USER_PARAMETER = os.environ["DB_USER_PARAMETER"]
DB_PASSWORD_PARAMETER = os.environ["DB_PASSWORD_PARAMETER"]

ssm = boto3.client("ssm")


# ============================================================
# Role-Based Permissions
# ============================================================

PERMISSIONS = {

    "CUSTOMER": {

        "GET": [
            "/products",
            "/products/{id}",
            "/orders/{id}",
            "/orders"
        ],

        "POST": [
            "/orders"
        ],

        "PATCH": [
            "/orders/{id}"
        ]
    },


    "ADMIN": {

        "GET": [
            "/products",
            "/products/{id}",
            "/orders",
            "/orders/{id}"
        ],

        "POST": [
            "/products",
            "/orders"
        ],

        "PATCH": [
            "/products/{id}",
            "/orders/{id}"
        ],

        "DELETE": [
            "/products/{id}"
        ]
    }
}


# ============================================================
# Get SSM Parameter
# ============================================================

def get_ssm_parameter(parameter_name):

    response = ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]
# ============================================================
# Cached Database Configuration
# ============================================================

_db_config = None


def get_db_config():

    global _db_config

    if _db_config is None:

        _db_config = {
            "host": get_ssm_parameter(DB_HOST_PARAMETER),
            "port": int(
                get_ssm_parameter(DB_PORT_PARAMETER)
            ),
            "database": get_ssm_parameter(
                DB_NAME_PARAMETER
            ),
            "user": get_ssm_parameter(
                DB_USER_PARAMETER
            ),
            "password": get_ssm_parameter(
                DB_PASSWORD_PARAMETER
            )
        }

        print("Database configuration loaded from SSM")

    return _db_config


# ============================================================
# Database Connection
# ============================================================

def get_connection():

    config = get_db_config()

    return pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


# ============================================================
# Get Method ARN
# ============================================================

def get_method_arn(event):

    # --------------------------------------------------------
    # REST API / REQUEST Authorizer
    # --------------------------------------------------------

    method_arn = event.get("methodArn")

    if method_arn:
        return method_arn


    # --------------------------------------------------------
    # HTTP API / REQUEST Authorizer
    # --------------------------------------------------------

    route_arn = event.get("routeArn")

    if route_arn:
        return route_arn


    # --------------------------------------------------------
    # Build ARN if methodArn/routeArn is not directly provided
    # --------------------------------------------------------
    # these are fall back mechanism
    # what if the API gateway does not provide 

    request_context = event.get(
        "requestContext"
    ) or {}

    api_id = request_context.get(
        "apiId"
    )

    account_id = request_context.get(
        "accountId"
    )

    stage = request_context.get(
        "stage"
    )

    region = os.environ.get(
        "AWS_REGION",
        "ap-south-1"
    )


    # HTTP API format
    http_context = request_context.get(
        "http"
    ) or {}

    http_method = (
        event.get("httpMethod")
        or http_context.get("method")
    )

    path = (
        event.get("path")
        or event.get("rawPath")
        or http_context.get("path")
        or "/"
    )


    # REST API requestContext can contain httpMethod
    if not http_method:

        http_method = request_context.get(
            "httpMethod"
        )


    if api_id and account_id and stage and http_method:

        return (
            f"arn:aws:execute-api:"
            f"{region}:"
            f"{account_id}:"
            f"{api_id}/"
            f"{stage}/"
            f"{http_method}"
            f"{path}"
        )


    print(
        "Unable to construct method ARN"
    )

    return None


# ============================================================
# Lambda Handler
# ============================================================
def is_public_product_route(method, path):
    if method != "GET":
        return False

    if path == "/products":
        return True

    if re.match(r"^/products/[^/]+$", path):
        return True

    return False

def lambda_handler(event, context):

    print("Authorizer Lambda invoked")
    print("Event:", event)


    try:

        # ----------------------------------------------------
        # 1. Get Method ARN
        # ----------------------------------------------------

        method_arn = get_method_arn(
            event
        )
        # ----------------------------------------------------
        # Get HTTP Method and API Path
        # ----------------------------------------------------

        method = get_http_method(method_arn)

        path = get_path(method_arn)

        if not path or path == "/":
            event_path = (
                event.get("path")
                or event.get("rawPath")
            )

            if event_path:
                path = event_path

        print(f"Method: {method}")
        print(f"Path: {path}")
        # ----------------------------------------------------
# Public Product GET Requests
# ----------------------------------------------------

        if is_public_product_route(method, path):

            print("Public product GET request")
            print("Authentication not required")

            return generate_policy(
                "Allow",
                method_arn,
                principal_id="public-user"
            )


        if not method_arn:

            print(
                "Missing methodArn/routeArn"
            )

            return generate_policy(
                "Deny",
                "*"
            )


        print(
            f"Method ARN: {method_arn}"
        )


        # ----------------------------------------------------
        # 2. Get Authorization Header
        # ----------------------------------------------------

        headers = event.get(
            "headers"
        ) or {}


        authorization = (
            headers.get("Authorization")
            or headers.get("authorization")
        )


        if not authorization:

            print(
                "No Authorization header"
            )

            return generate_policy(
                "Deny",
                method_arn
            )


        # ----------------------------------------------------
        # 3. Validate Bearer Token
        # ----------------------------------------------------

        if not authorization.startswith(
            "Bearer "
        ):

            print(
                "Invalid Authorization format"
            )

            return generate_policy(
                "Deny",
                method_arn
            )


        token = authorization[
            7:
        ].strip()


        if not token:

            print(
                "Empty token"
            )

            return generate_policy(
                "Deny",
                method_arn
            )


        print(
            "Authorization token received"
        )


        # ----------------------------------------------------
        # 4. Get user_id From Header
        # ----------------------------------------------------

        user_id_header = (

            headers.get("user_id")

            or headers.get("User-Id")

            or headers.get("user-id")

            or headers.get("X-User-Id")

            or headers.get("x-user-id")
        )


        if not user_id_header:

            print(
                "No user_id header"
            )

            return generate_policy(
                "Deny",
                method_arn
            )


        print(
            f"Requested User ID: {user_id_header}"
        )


        # ----------------------------------------------------
        # 5. Validate user_id
        # ----------------------------------------------------

        try:

            requested_user_id = int(
                user_id_header
            )

        except (
            ValueError,
            TypeError
        ):

            print(
                "Invalid user_id"
            )

            return generate_policy(
                "Deny",
                method_arn
            )


        if requested_user_id <= 0:

            print(
                "Invalid user_id value"
            )

            return generate_policy(
                "Deny",
                method_arn
            )


        print(
            f"Validated Requested User ID: "
            f"{requested_user_id}"
        )


        # ----------------------------------------------------
        # 6. Connect to Database
        # ----------------------------------------------------

        connection = get_connection()


        # ----------------------------------------------------
        # 7. Validate Token + user_id
        # ----------------------------------------------------

        try:

            with connection.cursor() as cursor:

                sql = """
                    SELECT user_id, role
                    FROM Customers
                    WHERE Token = %s
                      AND user_id = %s
                    LIMIT 1
                """


                cursor.execute(
                    sql,
                    (
                        token,
                        requested_user_id
                    )
                )


                user = cursor.fetchone()


        finally:

            connection.close()


        # ----------------------------------------------------
        # 8. Validate User
        # ----------------------------------------------------

        if not user:

            print(
                "Invalid token or user_id"
            )

            return generate_policy(
                "Deny",
                method_arn
            )


        # ----------------------------------------------------
        # 9. Get Authenticated User Information
        # ----------------------------------------------------

        user_id = user[
            "user_id"
        ]

        role = user[
            "role"
        ]


        print(
            f"Authenticated User: {user_id}"
        )

        print(
            f"Role: {role}"
        )


        # ----------------------------------------------------
        # 10. Validate Role
        # ----------------------------------------------------

        role = str(
            role
        ).upper()


        if role not in PERMISSIONS:

            print(
                f"Unknown role: {role}"
            )

            return generate_policy(
                "Deny",
                method_arn,
                principal_id=str(
                    user_id
                )
            )


        # ----------------------------------------------------
        # 11. Get HTTP Method
        # ----------------------------------------------------

        method = get_http_method(
            method_arn
        )


        # ----------------------------------------------------
        # 12. Get API Path
        # ----------------------------------------------------

        path = get_path(
            method_arn
        )


        # ----------------------------------------------------
        # 13. Fallback to Event Path
        # ----------------------------------------------------

        if not path or path == "/":

            event_path = (
                event.get("path")
                or event.get("rawPath")
            )

            if event_path:

                path = event_path


        print(
            f"Method: {method}"
        )

        print(
            f"Path: {path}"
        )


        # ----------------------------------------------------
        # 14. Check Role Permissions
        # ----------------------------------------------------

        if is_allowed(
            role,
            method,
            path
        ):

            print(
                "Authorization successful"
            )


            return generate_policy(

                "Allow",

                method_arn,

                principal_id=str(
                    user_id
                ),

                context={

                    "user_id": str(
                        user_id
                    ),

                    "role": role
                }
            )


        # ----------------------------------------------------
        # 15. Permission Denied
        # ----------------------------------------------------

        print(
            "Authorization denied"
        )


        return generate_policy(

            "Deny",

            method_arn,

            principal_id=str(
                user_id
            )
        )


    # ========================================================
    # Error Handling
    # ========================================================

    except Exception as e:

        print(
            f"Authorization error: {str(e)}"
        )


        method_arn = get_method_arn(
            event
        )


        return generate_policy(

            "Deny",

            method_arn or "*"
        )


# ============================================================
# Get HTTP Method
# ============================================================

def get_http_method(method_arn):

    if not method_arn:

        return ""


    parts = method_arn.split(
        "/"
    )


    if len(parts) < 3:

        return ""


    return parts[2].upper()


# ============================================================
# Get API Path
# ============================================================

def get_path(method_arn):

    if not method_arn:

        return "/"


    parts = method_arn.split(
        "/"
    )


    if len(parts) <= 3:

        return "/"


    path_parts = parts[3:]


    if not path_parts:

        return "/"


    return "/" + "/".join(
        path_parts
    )


# ============================================================
# Check Permission
# ============================================================

def is_allowed(
    role,
    method,
    actual_path
):

    allowed_paths = (
        PERMISSIONS
        .get(role, {})
        .get(method, [])
    )


    for allowed_path in allowed_paths:

        # ----------------------------------------------------
        # Convert:
        #
        # /products/{id}
        #
        # Into:
        #
        # /products/[^/]+
        # ----------------------------------------------------

        pattern = re.sub(

            r"\{[^}]+\}",

            r"[^/]+",

            allowed_path
        )


        pattern = (
            "^"
            + pattern
            + "$"
        )


        if re.match(
            pattern,
            actual_path
        ):

            return True


    return False


# ============================================================
# Generate IAM Policy
# ============================================================

def generate_policy(

    effect,

    resource,

    principal_id="cloudmart-user",

    context=None

):

    policy = {

        "principalId": principal_id,

        "policyDocument": {

            "Version": "2012-10-17",

            "Statement": [

                {

                    "Action":
                        "execute-api:Invoke",

                    "Effect":
                        effect,

                    "Resource":
                        resource
                }
            ]
        }
    }


    # --------------------------------------------------------
    # Add user information to authorizer context
    # --------------------------------------------------------

    if context:

        policy[
            "context"
        ] = context


    return policy


# import os
# import boto3

# ssm = boto3.client("ssm")

# PARAMETER_NAME = os.environ["AUTH_TOKEN_PARAMETER"]


# def lambda_handler(event, context):

#     print("Authorizer Lambda invoked")

#     headers = event.get("headers", {})

#     provided_token = (
#         headers.get("Authorization")
#         or headers.get("authorization")
#     )

#     if not provided_token:
#         print("No authentication token provided")
#         return generate_policy("Deny", event["methodArn"])

#     response = ssm.get_parameter(
#         Name=PARAMETER_NAME,
#         WithDecryption=True
#     )

#     expected_token = response["Parameter"]["Value"]

#     if provided_token == expected_token:
#         print("Authentication successful")

#         method_arn = event["methodArn"]

#         tmp = method_arn.split(":")
#         api_gateway_arn = tmp[5].split("/")

#         wildcard_resource = (
#             f"{tmp[0]}:{tmp[1]}:{tmp[2]}:{tmp[3]}:{tmp[4]}:"
#             f"{api_gateway_arn[0]}/{api_gateway_arn[1]}/*/*"
#         )

#         return generate_policy("Allow", wildcard_resource)

#     print("Authentication failed")
#     return generate_policy("Deny", event["methodArn"])

# def generate_policy(effect, resource):

#     return {
#         "principalId": "cloudmart-user",
#         "policyDocument": {
#             "Version": "2012-10-17",
#             "Statement": [
#                 {
#                     "Action": "execute-api:Invoke",
#                     "Effect": effect,
#                     "Resource": resource
#                 }
#             ]
#         }
#     }
import os
import re
import jwt
from jwt import PyJWKClient


# Cognito configuration
AWS_REGION = os.environ["AWS_REGION"]
USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]

ISSUER = (
    f"https://cognito-idp.{AWS_REGION}.amazonaws.com/"
    f"{USER_POOL_ID}"
)

JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

# Reused between Lambda invocations
jwks_client = PyJWKClient(JWKS_URL)


# Role-based permissions
PERMISSIONS = {
    "CUSTOMER": {
        "GET": [
            "/products",
            "/products/{id}",
            "/orders",
            "/orders/{id}"
        ],
        "POST": [
            "/orders"
        ]
    },

    "ADMIN": {
        "GET": [
            "/products",
            "/products/{id}",
            "/orders",
            "/orders/{id}",
            "/users"
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


def lambda_handler(event, context):

    print("Authorizer Lambda invoked")

    headers = event.get("headers") or {}

    authorization = (
        headers.get("Authorization")
        or headers.get("authorization")
    )

    if not authorization:
        print("No Authorization header")
        return generate_policy(
            "Deny",
            event["methodArn"]
        )

    # Expected format:
    # Authorization: Bearer <token>
    if not authorization.startswith("Bearer "):
        print("Invalid Authorization format")
        return generate_policy(
            "Deny",
            event["methodArn"]
        )

    token = authorization[7:].strip()

    if not token:
        print("Empty token")
        return generate_policy(
            "Deny",
            event["methodArn"]
        )

    try:

        # Get Cognito public key
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Verify JWT
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=ISSUER,
            options={
                "verify_aud": False
            }
        )

        # Access token must be used
        if claims.get("token_use") != "access":
            print("Token is not an access token")
            return generate_policy(
                "Deny",
                event["methodArn"]
            )

        # Verify Cognito app client
        if claims.get("client_id") != CLIENT_ID:
            print("Invalid client_id")
            return generate_policy(
                "Deny",
                event["methodArn"]
            )

        # Get user role
        groups = claims.get("cognito:groups", [])

        if not groups:
            print("User has no Cognito group")
            return generate_policy(
                "Deny",
                event["methodArn"]
            )

        role = groups[0]

        if role not in PERMISSIONS:
            print(f"Unknown role: {role}")
            return generate_policy(
                "Deny",
                event["methodArn"]
            )

        # Get HTTP method and path
        method = get_http_method(event["methodArn"])
        path = get_path(event["methodArn"])

        print(f"User role: {role}")
        print(f"Method: {method}")
        print(f"Path: {path}")

        # Check permission
        if is_allowed(role, method, path):

            print("Authorization successful")

            return generate_policy(
                "Allow",
                event["methodArn"],
                principal_id=claims.get("sub", "cloudmart-user"),
                context={
                    "user_id": claims.get("sub", ""),
                    "role": role
                }
            )

        print("Authorization denied")

        return generate_policy(
            "Deny",
            event["methodArn"],
            principal_id=claims.get("sub", "cloudmart-user")
        )

    except jwt.ExpiredSignatureError:
        print("Token expired")

    except jwt.InvalidIssuerError:
        print("Invalid token issuer")

    except jwt.InvalidTokenError as e:
        print(f"Invalid JWT: {str(e)}")

    except Exception as e:
        print(f"Authorization error: {str(e)}")

    return generate_policy(
        "Deny",
        event["methodArn"]
    )


def get_http_method(method_arn):

    parts = method_arn.split("/")

    # arn:aws:execute-api:region:account:api/stage/METHOD/path
    return parts[2]


def get_path(method_arn):

    parts = method_arn.split("/")

    # Everything after:
    # api/stage/METHOD
    path_parts = parts[3:]

    if not path_parts:
        return "/"

    return "/" + "/".join(path_parts)


def is_allowed(role, method, actual_path):

    allowed_paths = PERMISSIONS.get(role, {}).get(method, [])

    for allowed_path in allowed_paths:

        # Convert:
        # /products/{id}
        # into:
        # /products/[^/]+

        pattern = re.sub(
            r"\{[^}]+\}",
            r"[^/]+",
            allowed_path
        )

        pattern = f"^{pattern}$"

        if re.match(pattern, actual_path):
            return True

    return False


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
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                }
            ]
        }
    }

    if context:
        policy["context"] = context

    return policy
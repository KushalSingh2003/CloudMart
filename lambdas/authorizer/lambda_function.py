import os
import boto3

ssm = boto3.client("ssm")

PARAMETER_NAME = os.environ["AUTH_TOKEN_PARAMETER"]


def lambda_handler(event, context):

    print("Authorizer Lambda invoked")

    headers = event.get("headers", {})

    provided_token = (
        headers.get("Authorization")
        or headers.get("authorization")
    )

    if not provided_token:
        print("No authentication token provided")
        return generate_policy("Deny", event["methodArn"])

    response = ssm.get_parameter(
        Name=PARAMETER_NAME,
        WithDecryption=True
    )

    expected_token = response["Parameter"]["Value"]

    if provided_token == expected_token:
        print("Authentication successful")

        method_arn = event["methodArn"]

        tmp = method_arn.split(":")
        api_gateway_arn = tmp[5].split("/")

        wildcard_resource = (
            f"{tmp[0]}:{tmp[1]}:{tmp[2]}:{tmp[3]}:{tmp[4]}:"
            f"{api_gateway_arn[0]}/{api_gateway_arn[1]}/*/*"
        )

        return generate_policy("Allow", wildcard_resource)

    print("Authentication failed")
    return generate_policy("Deny", event["methodArn"])

def generate_policy(effect, resource):

    return {
        "principalId": "cloudmart-user",
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
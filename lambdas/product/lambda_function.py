def lambda_handler(event, context):
    print("Product Lambda invoked")

    # your product logic here

    return {
        "statusCode": 200,
        "body": "Product Lambda working"
    }
import os
import pymysql


def lambda_handler(event, context):

    connection = None

    try:
        print("Starting RDS connection test...")

        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "3306")),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            connect_timeout=10
        )

        print("Successfully connected to RDS.")

        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")

        database = cursor.fetchone()

        print(f"Connected database: {database[0]}")

        cursor.close()

        return {
            "statusCode": 200,
            "body": "Successfully connected to RDS"
        }

    except Exception as e:

        print(f"RDS connection failed: {str(e)}")

        return {
            "statusCode": 500,
            "body": f"RDS connection failed: {str(e)}"
        }

    finally:

        if connection:
            connection.close()
            print("RDS connection closed.")
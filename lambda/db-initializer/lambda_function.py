# import json
# import os
# import urllib.request
# import pymysql


# def send_response(event, context, status, data=None, reason=None):
#     """
#     Send SUCCESS/FAILED response back to CloudFormation
#     for the Custom Resource.
#     """

#     response_url = event["ResponseURL"]

#     response_body = {
#         "Status": status,
#         "Reason": reason or "See CloudWatch logs",
#         "PhysicalResourceId": (
#             event.get("PhysicalResourceId")
#             or context.log_stream_name
#         ),
#         "StackId": event["StackId"],
#         "RequestId": event["RequestId"],
#         "LogicalResourceId": event["LogicalResourceId"],
#         "Data": data or {}
#     }

#     body = json.dumps(response_body).encode("utf-8")

#     request = urllib.request.Request(
#         response_url,
#         data=body,
#         headers={
#             "content-type": "",
#             "content-length": str(len(body))
#         },
#         method="PUT"
#     )

#     with urllib.request.urlopen(request) as response:
#         print(
#             "CloudFormation response status:",
#             response.status
#         )


# def execute_schema(connection):
#     """
#     Read schema.sql and execute each SQL statement.
#     """

#     schema_path = "database/schema.sql"

#     with open(schema_path, "r", encoding="utf-8") as file:
#         schema = file.read()

#     statements = [
#         statement.strip()
#         for statement in schema.split(";")
#         if statement.strip()
#     ]

#     cursor = connection.cursor()

#     for statement in statements:
#         print("Executing SQL:")
#         print(statement)

#         cursor.execute(statement)

#     connection.commit()

#     cursor.close()


# def handler(event, context):

#     print("Received CloudFormation event:")
#     print(json.dumps(event))

#     request_type = event.get("RequestType")

#     # ------------------------------------------------------------
#     # DELETE
#     # ------------------------------------------------------------

#     if request_type == "Delete":

#         print("Delete request received.")

#         send_response(
#             event,
#             context,
#             "SUCCESS",
#             {
#                 "Message": "Database schema was not deleted."
#             }
#         )

#         return

#     connection = None

#     try:

#         # --------------------------------------------------------
#         # Connect to RDS
#         # --------------------------------------------------------

#         print("Connecting to RDS...")

#         connection = pymysql.connect(
#             host=os.environ["DB_HOST"],
#             port=int(os.environ["DB_PORT"]),
#             user=os.environ["DB_USERNAME"],
#             password=os.environ["DB_PASSWORD"],
#             database=os.environ["DB_NAME"],
#             connect_timeout=20
#         )

#         print("Connected to RDS successfully.")

#         # --------------------------------------------------------
#         # Execute schema
#         # --------------------------------------------------------

#         execute_schema(connection)

#         print("Database schema created successfully.")

#         # --------------------------------------------------------
#         # Tell CloudFormation SUCCESS
#         # --------------------------------------------------------

#         send_response(
#             event,
#             context,
#             "SUCCESS",
#             {
#                 "Message": "CloudMart database schema initialized."
#             }
#         )

#     except Exception as error:

#         print("Database initialization failed.")
#         print(str(error))

#         if connection:
#             connection.rollback()

#         send_response(
#             event,
#             context,
#             "FAILED",
#             reason=str(error)
#         )

#         raise

#     finally:

#         if connection:
#             connection.close()

#         print("Database connection closed.")

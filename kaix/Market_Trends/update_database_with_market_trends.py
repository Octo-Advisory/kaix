# import mariadb

# def commit_query_execution(query):
#     """
#     Executes a given SQL query and returns the results.
   
#     :param query: SQL query to execute
#     :return: List of tuples containing query results
#     """
#     try:
#         # Connect to MariaDB
#         connection = mariadb.connect(**config)
#         cursor = connection.cursor()
 
#         # Execute the query
#         cursor.execute(query)
 
#         connection.commit()
 
#         # # Fetch and return results
#         # results = cursor.fetchall()
#         # return results
 
#     except mariadb.Error as err:
#         print(f"Database error: {err}")
#         return None
 
#     finally:
#         # Ensure resources are closed
#         if 'cursor' in locals():
#             cursor.close()
#         if 'connection' in locals() and connection:
#             connection.close()
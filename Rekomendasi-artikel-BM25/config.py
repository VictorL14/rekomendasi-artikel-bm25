import mysql.connector
from mysql.connector import Error

def create_connection():
    """ Create a database connection to a MySQL database """
    try:
        connection = mysql.connector.connect(
            host='localhost',          # e.g., 'localhost'
            database='rekomendasi_bm25',  # e.g., 'test_db'
            user='root',      # e.g., 'root'
            password=''   # e.g., 'password'
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: '{e}'")
        return None

def close_connection(connection):
    """ Close the database connection """
    if connection.is_connected():
        connection.close()
        print("MySQL connection is closed")

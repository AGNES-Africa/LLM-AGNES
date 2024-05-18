"""
This code gets credentials from environment variables. 
These credentials are then used to create a connection string for access to the 
postgres database
"""
import os
from dotenv import load_dotenv

load_dotenv()

def get_uri(use_sqlalchemy=False):
    username = os.getenv('USER_NAME')
    password = os.getenv('PASSWORD')
    host = os.getenv('HOST_NAME')
    dbname = os.getenv('DB_NAME')

    if use_sqlalchemy:
        # SQLAlchemy connection string format
        conn_string = f"postgresql+psycopg://{username}:{password}@{host}:5432/{dbname}"
    else:
        # psycopg2 connection string format
        conn_string = f"host={host} dbname={dbname} user={username} password={password}"

    return conn_string

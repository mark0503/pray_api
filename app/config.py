import os


DB_NAME = os.environ.get('db_name')
DB_USER = os.environ.get('user')
DB_PASSWORD = os.environ.get('password')
DB_HOST = os.environ.get('host')
DB_PORT = os.environ.get('port')


SECRET_KEY = os.environ.get('hash_password')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

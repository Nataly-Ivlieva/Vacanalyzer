from peewee import SqliteDatabase
import os
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv("DB_PATH")
db = SqliteDatabase(db_path)
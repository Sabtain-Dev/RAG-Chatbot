# scripts/explore_db.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"])

db = client["Lume_Luxe"]
print("Collections in 'Lume_Luxe':", db.list_collection_names())

for name in db.list_collection_names():
    sample = db[name].find_one()
    if sample:
        print(f"\n--- Sample document from '{name}' ---")
        print(sample)
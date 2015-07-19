import pymongo
from pymongo import MongoClient

client = MongoClient("localhost", 12321)

db = client["jjaguar_database"]

users = db["user"]

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['task_management']
print('connected succesfully')

tasks = db["tasks"]
teams = db["teams"]
users = db["users"]

print(tasks.find_one())

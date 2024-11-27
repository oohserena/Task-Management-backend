from pymongo import MongoClient
from flask import Flask, request, jsonify
from bson import ObjectId
import ssl

app = Flask(__name__)

client = MongoClient('', 
                     tls=True,
                     tlsAllowInvalidCertificates=True
                     ) # add connection string here
db = client['task_management']
print('connected succesfully')

tasks = db["tasks"]
teams = db["teams"]
users = db["users"]

print(users)

@app.route('/users/<user_id>/tasks', methods = ['GET'])
def get_user_tasks(user_id):
    try: 
        user = users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        tasks = user.get("task_ids", [])
        
        if not tasks:
            return jsonify([]), 200
        
        for task in tasks:
            task['_id'] = str(task['_id'])
            
        return jsonify(tasks), 200
     
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# if __name__ == '__main__':
#     app.run(debug=True)
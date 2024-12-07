from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
import ssl
from pymongo.errors import PyMongoError
from datetime import datetime
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB client connection
client = MongoClient(
    'mongodb://localhost:27017/'
)

db = client['task_management']
tasks = db["tasks"]
users = db["users"]
teams = db["teams"]

print('Connected to MongoDB successfully!')

# Get all tasks for a user (using Auth0 user_id as _id)
@app.route('/users/<user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    try:
        user = users.find_one({"_id": user_id})
        if not user:
            now = datetime.utcnow()
            user = {
                "_id": user_id,
                "user_name": "",
                "task_ids": [],
                "created_time": now,
                "updated_time": now
            }
            users.insert_one(user)
        
        task_ids = user.get("task_ids", [])
        user_tasks = tasks.find({"_id": {"$in": [ObjectId(tid) for tid in task_ids]}})
        response = []
        for task in user_tasks:
            task['_id'] = str(task['_id'])
            response.append(task)
            
        return jsonify(response), 200
    except PyMongoError as e:
        return jsonify({"error": f"MongoDB error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 400

@app.route('/users/<user_id>/tasks', methods=['POST'])
def add_task(user_id):
    try:
        task_data = request.json
        print(task_data)
        new_task = {
            "name": task_data.get("name"),
            "priority": task_data.get("priority"),
            "status": task_data.get("status"),
            "assignee": task_data.get("assignee"),
            
        }
        result = tasks.insert_one(new_task)
        task_id = result.inserted_id
        
        new_task["_id"] = str(task_id)
        
        user = users.find_one({"_id": user_id})
        if not user:
            now = datetime.utcnow()
            user = {
                "_id": user_id,
                "user_name": "",
                "task_ids": [],
                "created_time": now,
                "updated_time": now
            }
            users.insert_one(user)
        
        users.update_one(
            {"_id": user_id},  # Use Auth0 user_id here
            {
                "$push": {"task_ids": str(task_id)}, 
                "$set": {"updated_time": datetime.utcnow()}  
            }
        )
        socketio.emit('task_added', new_task, room=None)


        return task_data, 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Update a task
@app.route('/users/<user_id>/tasks/<task_id>', methods=['PUT'])
def update_task(user_id, task_id):
    try:
        task_data = request.json
        updated_task = {
            "name": task_data.get("name"),
            "priority": task_data.get("priority"),
            "assignee": task_data.get("assignee"),
        }
        result = tasks.update_one({"_id": ObjectId(task_id)}, {"$set": updated_task})
        
        if result.matched_count == 0:
            return jsonify({"error": "Task not found"}), 404
        
        # Emit a real-time event for task update
        emit('task_updated', {"user_id": user_id, "task_id": task_id, "updated_task": updated_task}, broadcast=True)
        
        return jsonify({"message": "Task updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Delete a task
@app.route('/users/<user_id>/tasks/<task_id>', methods=['DELETE'])
def delete_task(user_id, task_id):
    try:
        result = tasks.delete_one({"_id": ObjectId(task_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Task not found"}), 404
        
        # Remove task_id from user's task_ids and update the timestamp
        users.update_one(
            {"_id": user_id},  # Use Auth0 user_id here
            {
                "$pull": {"task_ids": task_id},  # Pull the task_id from the task_ids list
                "$set": {"updated_time": datetime.utcnow()}  # Update the updated_time field
            }
        )
        socketio.emit('task_deleted', task_id, room=None)
        return jsonify({"message": "Task deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

##### Teams

@app.route('/teams/<user_id>', methods=['GET'])
def get_team_info(user_id):
    try:
        # Query the user from the users collection
        user = users.find_one({"_id": user_id})  # Fetch user by user_id
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Ensure 'team_ids' exists in the user document and is a string
        team_id = user.get('team_ids')
        if not team_id:
            return jsonify({"error": "No team found for the user"}), 404
        
        # Fetch the team using the team_id (since it's a string now)
        user_team = teams.find_one({"_id": team_id})
        if not user_team:
            return jsonify({"error": "Team not found"}), 404
        
        names = []
        team_members = user_team.get("members")
        for member_id in team_members:
            cur_user = users.find_one({"_id": member_id})
            names.append(cur_user.get("user_name"))
        # Return the team information as JSON response
        return names, 200

    except Exception as e:
        # Handle any errors and return them
        return jsonify({"error": str(e)}), 400
    
# # Real-time events for teams
# @socketio.on('join_team')
# def handle_join_team(data):
#     team_id = data['team_id']
#     join_room(team_id)
#     emit('user_joined', {'message': f"User joined team {team_id}"}, to=team_id)

# @socketio.on('leave_team')
# def handle_leave_team(data):
#     team_id = data['team_id']
#     leave_room(team_id)
#     emit('user_left', {'message': f"User left team {team_id}"}, to=team_id)

# @socketio.on('update_team')
# def handle_update_team(data):
#     team_id = data['team_id']
#     update_info = data['update']
#     emit('team_updated', {'update': update_info}, to=team_id)

connected_clients = []
@socketio.on('connect')
def handle_connect():
    print('A user has connected')
    connected_clients.append(request.sid)
    print(f'Client connected: {request.sid}')
    print(f'Active connections: {len(connected_clients)}')

@socketio.on('disconnect')
def handle_disconnect():
    connected_clients.append(request.sid)
    print('A user has disconnected')
    print(f'Client disconnected: {request.sid}')
    print(f'Active connections: {len(connected_clients)}')
    
@socketio.on('test_event')
def handle_test_event(data):
    try:
        emit('test_response', {'message': 'Test successful'}, broadcast=True)
    except Exception as e:
        emit('error', {'message': str(e)})

    
@socketio.on('test_broadcast')
def handle_broadcast():
    emit('broadcast_response', {'message': 'This is a broadcast test!'}, broadcast=True)


    
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
    # app.run(debug=True)
    
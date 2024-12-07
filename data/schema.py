from mongoengine import connect, Document, StringField, ListField, DateTimeField
import datetime

# Connect to MongoDB database
connect(db='task_management', host='mongodb://localhost:27017/')

# Define the Team Schema
class Team(Document):
    _id = StringField(primary_key=True)  # Unique Team ID
    name = StringField(required=True)
    members = ListField(StringField())  # List of user IDs (could link to the User collection)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'teams'}

# Define the Task Schema
class Task(Document):
    _id = StringField(primary_key=True)  # Unique Task ID
    name = StringField(required=True)
    assignees = ListField(StringField())  # List of user IDs assigned to the task
    status = StringField(default="To Do")  # Task status (e.g., To Do, In Progress, Done)
    priority = StringField() 
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    team_id = StringField()  # Reference to the team associated with the task

    meta = {'collection': 'tasks'}

# Define the User Schema
class User(Document):
    _id = StringField(primary_key=True)  # Unique Auth0 user ID
    user_name = StringField(required=True)
    task_ids = ListField(StringField()) 
    team_ids = ListField(StringField())# List of Task IDs the user is assigned to
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'users'}

# Insert Dummy Teams
team1 = Team(
    _id="team1",
    name="Development Team",
    members=["auth0|12345", "auth0|67890", "auth0|54321"]
)
team2 = Team(
    _id="team2",
    name="Marketing Team",
    members=["auth0|12345", "auth0|67890"]
)

# Save teams
team1.save()
team2.save()

# Insert Dummy Tasks
task1 = Task(
    _id="67467659e0ad797ff56f6cdd",
    name="Install Flask",
    assignees=["auth0|12345"],
    status="To Do",
    priority="High",
    team_id="team1"
)

task2 = Task(
    _id="67467659e0ad797ff56f6cdc",
    name="Write Docs",
    assignees=["auth0|67890", "auth0|54321"],
    status="In Progress",
    priority="Medium",
    team_id="team1"
)

task3 = Task(
    _id="67467659e0ad797ff56f6cde",
    name="Marketing Research",
    assignees=["auth0|54321"],
    status="Done",
    priority="Low",
    team_id="team2"
)

# Save tasks
task1.save()
task2.save()
task3.save()

# Insert Dummy Users
user1 = User(
    _id="auth0|12345",  # Sample Auth0 user ID
    user_name="Alice",
    task_ids=["67467659e0ad797ff56f6cdd", "67467659e0ad797ff56f6cdc"]
)

user2 = User(
    _id="auth0|67890",  # Sample Auth0 user ID
    user_name="Bob",
    task_ids=["67467659e0ad797ff56f6cdc"]
)

user3 = User(
    _id="auth0|54321",  # Sample Auth0 user ID
    user_name="Charlie",
    task_ids=["67467659e0ad797ff56f6cde"]
)

# Save users to the database
user1.save()
user2.save()
user3.save()

# Print confirmation
print("Dummy teams, tasks, and users inserted successfully!")

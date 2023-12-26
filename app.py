from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort,current_app
from pymongo import MongoClient
from bson import ObjectId
from authlib.integrations.flask_client import OAuth
import requests

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['task_manager']  
tasks_collection = db['tasks']  

@app.route('/')
def home():
    return render_template("home.html")

status_mapping = {
    0: 'To-Do',
    1: 'In-Progress',
    2: 'Completed',
}

appConf = {
    "OAUTH2_CLIENT_ID": "155193801246-fp4q9e2kjlh6mdk6e7t5ha198rfa7m11.apps.googleusercontent.com",
    "OAUTH2_CLIENT_SECRET": "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",
    "OAUTH2_META_URL": "https://accounts.google.com/.well-known/openid-configuration",
    "FLASK_SECRET": "47c79391-d81d-4114-b725-aed8988960b5"
}

app.secret_key = appConf.get("FLASK_SECRET")
oauth = OAuth(app)

oauth.register(
    "myApp",
    client_id=appConf.get("OAUTH2_CLIENT_ID"),
    client_secret=appConf.get("OAUTH2_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'{appConf.get("OAUTH2_META_URL")}',
)

@app.route('/index')
def index():
    tasks = tasks_collection.find()
    user_data = session.get("user", {})
    print("Session Data:", user_data)
    name = user_data.get("name")
    return render_template('index.html', tasks=tasks, status_mapping=status_mapping, name=name)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/signin-google")
def googleCallback():
    token = oauth.myApp.authorize_access_token()
    personDataUrl = "https://people.googleapis.com/v1/people/me?personFields=names"
    personData = requests.get(personDataUrl, headers={
        "Authorization": f"Bearer {token['access_token']}"
    }).json()
    token["personData"] = personData
    session["user"] = token
    return redirect(url_for("index")) 

@app.route("/google-login")
def googleLogin():
    if "user" in session:
        abort(404)
    return oauth.myApp.authorize_redirect(redirect_uri=url_for("googleCallback", _external=True))

@app.route('/add_task', methods=['POST'])
def add_task():

    new_task = {
        'name': request.form.get('name'),
        'description' : request.form.get('description'),
        'deadline': request.form.get('deadline'),
        'status': int(request.form.get('status')),
        }

    tasks_collection.insert_one(new_task)
    return redirect(url_for('index'))

@app.route('/delete_task/<string:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:

        task_id = ObjectId(task_id)

        result = tasks_collection.delete_one({'_id': task_id})
        if result.deleted_count == 1:
            return jsonify({'message': 'Task deleted successfully'})
        else:
            return jsonify({'error': 'Task not found'})
    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'An error occurred while deleting the task.'})

@app.route('/update_status/<string:task_id>', methods=['PUT'])
def update_status(task_id):
    try:
        task_id = ObjectId(task_id)
        new_status = int(request.json.get('status'))
        result = tasks_collection.update_one({'_id': task_id}, {'$set': {'status': new_status}})
        if result.modified_count == 1:
            return jsonify({'message': 'Task status updated successfully'})
        else:
            return jsonify({'error': 'Task not found'})
    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'An error occurred while updating the task status.'})

@app.route("/logout")
def logout():
    print("Logging out user...")
    session.clear()
    current_app.logger.info("User logged out")
    return redirect(url_for("home"))

if __name__ == '__main__':
   app.run(debug=True)

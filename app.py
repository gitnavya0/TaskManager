from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from pymongo import MongoClient
from bson import ObjectId

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

@app.route('/index')
def index():
    tasks = tasks_collection.find()
    return render_template('index.html', tasks=tasks, status_mapping=status_mapping)
   
@app.route('/add_task', methods=['POST'])
def add_task():

    new_task = {
        'name': request.form.get('name'),
        'description' : request.form.get('description'),
        'deadline': request.form.get('deadline'),
        'status': int(request.form.get('status')),
        }

    # Insert the new task into MongoDB
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
        # Convert the string to ObjectId
        task_id = ObjectId(task_id)

        # Get the new status from the request data
        new_status = int(request.json.get('status'))

        # Update the task status in MongoDB
        result = tasks_collection.update_one({'_id': task_id}, {'$set': {'status': new_status}})
        if result.modified_count == 1:
            return jsonify({'message': 'Task status updated successfully'})
        else:
            return jsonify({'error': 'Task not found'})
    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'An error occurred while updating the task status.'})
    
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    due_date = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email aur password sab zaroori hain'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Ye email pehle se registered hai'}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User successfully register ho gaya'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Email ya password ghalat hai'}), 401

    return jsonify({'message': 'Login successful', 'user_id': user.id}), 200

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    due_date = data.get('due_date')
    user_id = data.get('user_id')

    if not title or not user_id:
        return jsonify({'error': 'Title aur user_id zaroori hain'}), 400

    new_task = Task(title=title, description=description, due_date=due_date, user_id=user_id)
    db.session.add(new_task)
    db.session.commit()

    return jsonify({'message': 'Task successfully ban gaya', 'task_id': new_task.id}), 201


@app.route('/tasks/<int:user_id>', methods=['GET'])
def get_tasks(user_id):
    status_filter = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 5, type=int)

    query = Task.query.filter_by(user_id=user_id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    result = []
    for task in paginated.items:
        result.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'due_date': task.due_date
        })

    return jsonify({
        'tasks': result,
        'total_tasks': paginated.total,
        'current_page': page,
        'total_pages': paginated.pages
    }), 200


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({'error': 'Task nahi mila'}), 404

    data = request.get_json()
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.status = data.get('status', task.status)
    task.due_date = data.get('due_date', task.due_date)

    db.session.commit()

    return jsonify({'message': 'Task update ho gaya'}), 200


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({'error': 'Task nahi mila'}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({'message': 'Task delete ho gaya'}), 200


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
import dotenv
import asyncio
from src.agent import process_query
from src.permissions import get_permit_users, update_user_role
from src.constants import USERS

dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username in USERS and USERS[username]['password'] == password:
        return jsonify({
            'success': True,
            'user': {
                'username': username,
                'name': USERS[username]['name'],
                'email': USERS[username]['email'],
                'role': USERS[username]['role']
            }
        })
    
    return jsonify({
        'success': False,
        'error': 'Invalid username or password'
    }), 401

@app.route('/api/agent', methods=['POST'])
def handle_agent_request():
    data = request.json
    if not data or 'query' not in data or 'username' not in data:
        return jsonify({'error': 'Missing query or username in request'}), 400
        
    username = data['username']
    if username not in USERS:
        return jsonify({'error': 'Invalid username'}), 401
        
    query = data['query']
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(process_query(username, query))
    loop.close()
    
    return jsonify(result)

@app.route('/api/permit/users', methods=['GET'])
async def get_users():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No authorization token provided"}), 401
        
    try:
        users = await get_permit_users()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/roles/<action>', methods=['POST'])
async def manage_role(action):
    if action not in ['add', 'remove']:
        return jsonify({"error": "Invalid action"}), 400
        
    data = request.json
    if not data or 'userId' not in data or 'role' not in data:
        return jsonify({"error": "User ID and role are required"}), 400
        
    try:
        result = await update_user_role(data['userId'], data['role'], action)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True) 
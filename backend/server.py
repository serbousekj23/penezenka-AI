from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

# MongoDB connection string from environment variable
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['crypto_db']
users_col = db['users']
holdings_col = db['holdings']

@app.route('/api/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    if users_col.find_one({'username': username}):
        return jsonify({'error': 'User exists'}), 409
    user = {'username': username}
    result = users_col.insert_one(user)
    return jsonify({'id': str(result.inserted_id), 'username': username})

@app.route('/api/holdings/<username>', methods=['GET'])
def get_holdings(username):
    user = users_col.find_one({'username': username})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    holdings = list(holdings_col.find({'username': username}, {'_id': 0}))
    return jsonify({'username': username, 'holdings': holdings})

@app.route('/api/holdings/<username>', methods=['POST'])
def add_holding(username):
    data = request.json
    crypto = data.get('crypto')
    amount = data.get('amount')
    price = data.get('price')
    if not all([crypto, amount, price]):
        return jsonify({'error': 'Missing data'}), 400
    user = users_col.find_one({'username': username})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    holding = {'username': username, 'crypto': crypto, 'amount': amount, 'price': price}
    holdings_col.insert_one(holding)
    return jsonify({'message': 'Holding added'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render poskytuje port dynamicky
    app.run(host='0.0.0.0', port=port, debug=False)  # 0.0.0.0 = dostupné z Renderu
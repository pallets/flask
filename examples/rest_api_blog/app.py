from flask import Flask, request, jsonify, abort

app = Flask(__name__)

posts = []
current_id = 1

def find_post(post_id):
    return next((post for post in posts if post['id'] == post_id), None)

@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts), 200

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = find_post(post_id)
    if not post:
        abort(404, description="Post not found")
    return jsonify(post), 200

@app.route('/api/posts', methods=['POST'])
def create_post():
    global current_id
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        abort(400, description="Missing title or content")
    post = {
        'id': current_id,
        'title': data['title'],
        'content': data['content']
    }
    posts.append(post)
    current_id += 1
    return jsonify(post), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = find_post(post_id)
    if not post:
        abort(404, description="Post not found")
    data = request.get_json()
    if not data:
        abort(400, description="Missing data")
    post['title'] = data.get('title', post['title'])
    post['content'] = data.get('content', post['content'])
    return jsonify(post), 200

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = find_post(post_id)
    if not post:
        abort(404, description="Post not found")
    posts.remove(post)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("firebase-secret.json")  # Ensure this path is correct
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mytube-f46cc-default-rtdb.firebaseio.com/'
})



app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'videos')  # ✅ FULL PATH

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# In-memory list to store video metadata

@app.route('/api/upload', methods=['POST'])
def upload_video():
    video = request.files.get('video')
    title = request.form.get('title')

    if not video or not title:
        return jsonify({'error': 'Missing title or video'}), 400

    filename = secure_filename(video.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    video.save(path)

    video_data = {
        'title': title,
        'filename': filename,
        'likes': 0,
        'comments': []
    }

    ref = db.reference('/videos')
    ref.push(video_data)

    return jsonify({'message': 'Video uploaded successfully'}), 200


@app.route('/api/videos', methods=['GET'])
def get_videos():
    ref = db.reference('/videos')
    all_videos = ref.get() or {}
    return jsonify(list(all_videos.values())), 200


@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/like', methods=['POST'])
def like_video():
    filename = request.json.get('filename')
    ref = db.reference('/videos')
    all_videos = ref.get() or {}

    for key, video in all_videos.items():
        if video['filename'] == filename:
            video['likes'] += 1
            ref.child(key).update({'likes': video['likes']})
            return jsonify({'message': 'Like added'}), 200

    return jsonify({'error': 'Video not found'}), 404


@app.route('/api/comment', methods=['POST'])
def comment_video():
    filename = request.json.get('filename')
    comment = request.json.get('comment')
    ref = db.reference('/videos')
    all_videos = ref.get() or {}

    for key, video in all_videos.items():
        if video['filename'] == filename:
            comments = video.get('comments', [])
            comments.append(comment)
            ref.child(key).update({'comments': comments})
            return jsonify({'message': 'Comment added'}), 200

    return jsonify({'error': 'Video not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5052)

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from deepface import DeepFace
import cv2
import numpy as np
import logging
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

# Set up file upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Analyze Sentiment for Text
@app.route('/api/sentiment', methods=['POST'])
def analyze_sentiment():
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    data = request.get_json()
    text = data.get('text')
    if text:
        try:
            analyzer = SentimentIntensityAnalyzer()
            sentiment = analyzer.polarity_scores(text)
            logging.debug(f"Text Sentiment Analysis: {sentiment}")
            return jsonify({'sentiment': sentiment})
        except Exception as e:
            logging.error(f"Error analyzing sentiment: {e}")
            return jsonify({"error": str(e)}), 500
    logging.warning("No text provided in request")
    return jsonify({'error': 'No text provided'}), 400

# Analyze Facial Expression in Image
@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    if 'file' not in request.files:
        logging.warning("No file part in the request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logging.warning("No file selected in the request")
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        logging.info(f"File saved at: {filename}")
        
        try:
            # Analyze image using DeepFace for emotion detection
            expression_result = analyze_image_with_model(filename)
            logging.debug(f"Image Emotion Analysis: {expression_result}")
            return jsonify({'expression': expression_result, 'message': 'Image analyzed successfully'})
        except Exception as e:
            logging.error(f"Error during image analysis: {e}", exc_info=True)
            return jsonify({'error': 'Image processing failed', 'details': str(e)}), 500
    
    logging.warning("Invalid file type uploaded")
    return jsonify({'error': 'Invalid file type'}), 400

# Analyze Facial Expressions in Video
@app.route('/api/analyze-video', methods=['POST'])
def analyze_video():
    if 'file' not in request.files:
        logging.warning("No file part in the request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logging.warning("No file selected in the request")
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        logging.info(f"Video file saved at: {filename}")
        
        try:
            # Analyze video by processing frames
            frames_analysis = analyze_video_with_model(filename)
            logging.debug(f"Video Frame Expressions: {frames_analysis}")
            return jsonify({'frames': frames_analysis, 'message': 'Video analyzed successfully'})
        except Exception as e:
            logging.error(f"Error during video analysis: {e}", exc_info=True)
            return jsonify({'error': 'Video processing failed', 'details': str(e)}), 500
    
    logging.warning("Invalid file type uploaded")
    return jsonify({'error': 'Invalid file type'}), 400

# Home route to render index.html
@app.route('/')
def home():
    return render_template('index.html')

# Helper function to analyze image using DeepFace
def analyze_image_with_model(img_path):
    try:
        # Analyze emotions from the image
        analysis = DeepFace.analyze(img_path, actions=['emotion'])
        return analysis[0]['dominant_emotion']
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise Exception(f"Error processing image: {e}")

# Helper function to analyze video frame-by-frame using DeepFace
def analyze_video_with_model(video_path):
    logging.debug(f"Processing video at path: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    frames_expressions = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Save every 10th frame for analysis to optimize speed
        if frame_count % 10 == 0:
            try:
                # Convert frame to image and analyze with DeepFace
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], f"frame_{frame_count}.jpg")
                img.save(img_path)
                expression = analyze_image_with_model(img_path)
                frames_expressions.append({'frame': frame_count, 'expression': expression})
            except Exception as e:
                logging.error(f"Error analyzing frame {frame_count}: {e}")
        
        frame_count += 1

    cap.release()
    logging.debug(f"Processed {frame_count} frames from video")
    return frames_expressions  # Return expressions for selected frames

if __name__ == '__main__':
    app.run(debug=False, port=8000) 
 

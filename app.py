import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from deepface import DeepFace
import cv2
from PIL import Image
import nltk
from langdetect import detect, DetectorFactory
from googletrans import Translator
import langcodes

# Download necessary NLTK data
nltk.download('vader_lexicon')

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

# Set up file upload folder
UPLOAD_FOLDER = '/tmp/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {
    'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

# Helper function to check allowed file extensions


def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Function to detect language of text
DetectorFactory.seed = 0  # Ensures consistent results


def detect_language(text):
  try:
    lang = detect(text)
    return lang
  except Exception as e:
    logging.error(f"Language detection error: {str(e)}")
    return "en"  # Default to English if detection fails


# Function to translate text to English
translator = Translator()


def translate_to_english(text):
  try:
    translated = translator.translate(text, src='auto', dest='en')
    return translated.text
  except Exception as e:
    logging.error(f"Translation error: {str(e)}")
    return text

# Function to get full language name


def get_full_language_name(language_code):
  try:
    language = langcodes.Language.make(language_code)
    return language.display_name()  # Get the full language name
  except Exception as e:
    logging.error(f"Error getting full language name: {str(e)}")
    return language_code

# Route to analyze sentiment for text


@app.route('/api/sentiment', methods=['POST'])
def analyze_sentiment():
  from nltk.sentiment.vader import SentimentIntensityAnalyzer

  data = request.get_json()
  text = data.get('text')

  if text:
    try:
      detected_lang = detect_language(text)
      language = get_full_language_name(detected_lang)

      # Translate only if necessary
      translated_text = translate_to_english(text)

      analyzer = SentimentIntensityAnalyzer()
      sentiment = analyzer.polarity_scores(translated_text)

      logging.debug(f"Detected Language: {language}")
      logging.debug(f"Translated Text: {translated_text}")
      logging.debug(f"Sentiment Scores: {sentiment}")

      return jsonify({
          "language": language,
          "translatedText": translated_text,
          "sentiment": sentiment
      })

    except Exception as e:
      logging.error(f"Error analyzing sentiment: {e}")
      return jsonify({"error": str(e)}), 500

  logging.warning("No text provided in request")
  return jsonify({'error': 'No text provided'}), 400

# Route to analyze facial expression in image


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
    return jsonify({'error': 'No file part'}), 400

  file = request.files['file']
  if file.filename == '':
    return jsonify({'error': 'No selected file'}), 400

  if file and allowed_file(file.filename):
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)

    try:
      # Analyze the video for emotions
      video_result = analyze_video_with_model(filename)
      return jsonify({'analysis': video_result})
    except Exception as e:
      return jsonify({'error': 'Video processing failed', 'details': str(e)}), 500

  return jsonify({'error': 'Invalid file type'}), 400


def analyze_video_with_model(video_path):
  # Use OpenCV to read the video and DeepFace for each frame analysis
  video_capture = cv2.VideoCapture(video_path)
  frame_results = []

  while True:
    ret, frame = video_capture.read()
    if not ret:
      break

    # Perform emotion analysis on each frame
    try:
      result = DeepFace.analyze(
          frame, actions=['emotion'], enforce_detection=False)
      # Store the dominant emotion for each frame
      frame_results.append(result[0]['dominant_emotion'])
    except Exception as e:
      print(f"Error analyzing frame: {e}")

  video_capture.release()

  # If needed, return some aggregated result, like the most common emotion in the video
  most_common_emotion = max(
      set(frame_results), key=frame_results.count)  # Simple majority vote
  return most_common_emotion

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
        img_path = os.path.join(
            app.config['UPLOAD_FOLDER'], f"frame_{frame_count}.jpg")
        img.save(img_path)
        expression = analyze_image_with_model(img_path)
        frames_expressions.append(
            {'frame': frame_count, 'expression': expression})
      except Exception as e:
        logging.error(f"Error analyzing frame {frame_count}: {e}")

    frame_count += 1

  cap.release()
  logging.debug(f"Processed {frame_count} frames from video")
  return frames_expressions  # Return expressions for selected frames


# if __name__ == '__main__':
#   app.run(debug=False, port=8000)

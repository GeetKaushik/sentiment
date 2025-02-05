// Event listener for analyzing the text input
document.getElementById('translate-and-analyze-btn').addEventListener('click', async () => {
  const textInput = document.getElementById('text-input').value;

  if (!textInput.trim()) {
      alert('Please enter some text for analysis.');
      return;
  }

  console.log("Sending text for sentiment analysis...");
  const sentimentData = await analyzeText(textInput);

  if (sentimentData) {
      console.log("Received sentiment data:", sentimentData.sentiment);

      document.getElementById('text-result-container').style.display = 'block';
      document.getElementById('detected-language').innerText = sentimentData.language;
      document.getElementById('translated-text').innerText = sentimentData.translatedText;

      document.getElementById('text-analysis-result').innerText = 
          `Compound: ${sentimentData.sentiment.compound}, 
          Negative: ${sentimentData.sentiment.neg}, 
          Neutral: ${sentimentData.sentiment.neu}, 
          Positive: ${sentimentData.sentiment.pos}`;
  } else {
      console.error("No sentiment data received.");
      alert('There was an issue analyzing the text. Please try again.');
  }
});

// Event listener for analyzing the image upload
document.getElementById('analyze-image-btn').addEventListener('click', async () => {
  const fileInput = document.getElementById("image-upload");
  const resultContainer = document.getElementById("image-result-container");
  const resultText = document.getElementById("image-analysis-result");
  const loadingIndicator = document.getElementById("loading-indicator");

  if (fileInput.files.length === 0) {
      alert("Please upload an image first.");
      return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  resultContainer.style.display = "none";  
  loadingIndicator.style.display = "block"; 

  try {
      const response = await fetch("http://127.0.0.1:8000/api/analyze-image", {
          method: "POST",
          body: formData
      });

      if (!response.ok) {
          throw new Error("Server error: " + response.status);
      }

      const data = await response.json();
      loadingIndicator.style.display = "none"; 
      resultText.textContent = "Emotion detected: " + data.emotion; 
      resultContainer.style.display = "block"; 
  } catch (error) {
      loadingIndicator.style.display = "none"; 
      alert("Error analyzing image: " + error.message);
      console.error("Error:", error);
  }
});

// Event listener for analyzing the video upload
document.getElementById('analyze-video-btn').addEventListener('click', async () => {
  const videoInput = document.getElementById('video-upload').files[0];

  if (!videoInput) {
      alert('Please upload a video for analysis.');
      return;
  }

  document.getElementById('video-result-container').style.display = 'none';
  document.getElementById('loading-indicator').style.display = 'block';

  console.log("Sending video for analysis...");
  const analysisResult = await analyzeVideo(videoInput);

  document.getElementById('loading-indicator').style.display = 'none'; 
  document.getElementById('video-result-container').style.display = 'block';

  if (analysisResult) {
      console.log("Received video analysis result:", analysisResult);
      document.getElementById('video-analysis-result').innerText = `Analysis: ${analysisResult}`;
  } else {
      console.error("Error analyzing video.");
      alert('There was an issue analyzing the video. Please try again.');
  }
});

// ✅ NEW: Event listener for analyzing file upload via form submission
document.getElementById("uploadForm").addEventListener("submit", function (event) {
  event.preventDefault();
  
  let fileInput = document.getElementById("fileInput");
  let file = fileInput.files[0];

  if (!file) {
      alert("Please select a file!");
      return;
  }

  let formData = new FormData();
  formData.append("file", file);

  fetch("http://127.0.0.1:8000/api/analyze-image", {
      method: "POST",
      body: formData, 
      headers: {
          "Accept": "application/json"
      }
  })
  .then(response => {
      if (!response.ok) {
          throw new Error("Network response was not ok");
      }
      return response.json();
  })
  .then(data => {
      console.log("Success:", data);
      document.getElementById("result").innerText = `Expression: ${data.expression}`;
  })
  .catch(error => {
      console.error("Error analyzing image:", error);
      alert("Failed to analyze image. Check the console for details.");
  });
});

// Function to analyze text for sentiment
async function analyzeText(text) {
  console.log("Making API request for sentiment analysis...");
  try {
      const response = await fetch("http://127.0.0.1:8000/api/sentiment", {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({ text: text })
      });

      const data = await response.json();
      console.log("Received sentiment response:", data);

      if (response.ok && data.sentiment) {
          return {
              language: data.language,
              translatedText: data.translatedText,
              sentiment: data.sentiment
          };
      } else {
          console.error('Error analyzing text:', data.error || 'No sentiment data found.');
          return null;
      }
  } catch (error) {
      console.error('Error:', error);
      return null;
  }
}

// Function to analyze image for facial expressions
async function analyzeImage(image) {
  console.log("Making API request for image analysis...");
  const formData = new FormData();
  formData.append('file', image);

  try {
      const response = await fetch("http://127.0.0.1:8000/api/analyze-image", {
          method: 'POST',
          body: formData
      });

      const data = await response.json();
      console.log("Received image analysis response:", data);

      if (response.ok && data.expression) {
          return data.expression;
      } else {
          console.error('Error analyzing image:', data.error);
          return null;
      }
  } catch (error) {
      console.error('Error:', error);
      return null;
  }
}

// Function to analyze video for expressions
async function analyzeVideo(video) {
  console.log("Making API request for video analysis...");
  const formData = new FormData();
  formData.append('file', video);

  try {
      const response = await fetch("http://127.0.0.1:8000/api/analyze-video", {
          method: 'POST',
          body: formData
      });

      const data = await response.json();
      console.log("Received video analysis response:", data);

      if (response.ok && data.analysis) {
          return data.analysis;
      } else {
          console.error('Error analyzing video:', data.error || 'No analysis result found.');
          return null;
      }
  } catch (error) {
      console.error('Error:', error);
      return null;
  }
}

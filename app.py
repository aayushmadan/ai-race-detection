from flask import Flask, render_template, Response
import cv2
import numpy as np
from deepface import DeepFace
import time
import os

app = Flask(__name__)

# Create directories for templates and static if they don't exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/css', exist_ok=True)

def detect_ethnicity(frame):
    try:
        # Analyze the frame using DeepFace
        result = DeepFace.analyze(img_path=frame, 
                                 actions=['race'],
                                 detector_backend='opencv',
                                 enforce_detection=False)
        
        if isinstance(result, list):
            result = result[0]
        
        # Get face location
        if 'region' in result:
            face_region = result['region']
            x, y, w, h = face_region['x'], face_region['y'], face_region['w'], face_region['h']
            
            # Get top ethnicity
            race_results = result['race']
            top_ethnicity = max(race_results.items(), key=lambda x: x[1])
            ethnicity_label = f"{top_ethnicity[0]}: {top_ethnicity[1]:.2f}%"
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Display ethnicity above the rectangle
            cv2.putText(frame, ethnicity_label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        return frame
        
    except Exception as e:
        # Print error but continue
        print(f"Error in ethnicity detection: {e}")
        return frame

def generate_frames():
    camera = cv2.VideoCapture(0)  # 0 for default camera
    
    # Processing every frame would be too CPU intensive, so we'll process every few frames
    process_every_n_frames = 15
    frame_count = 0
    last_processed_frame = None
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        frame_count += 1
        
        # Process every Nth frame for ethnicity detection
        if frame_count % process_every_n_frames == 0:
            processed_frame = detect_ethnicity(frame)
            last_processed_frame = processed_frame
        else:
            # If we have a previously processed frame, use its detection boxes
            if last_processed_frame is not None:
                # Just display the original frame with the previous detection results
                frame = last_processed_frame
        
        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # Yield the frame in byte format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        # Small delay to reduce CPU usage
        time.sleep(0.01)
    
    camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Create the HTML template
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Live Face Ethnicity Detection</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Live Face Ethnicity Detection</h1>
        <div class="camera-container">
            <img src="{{ url_for('video_feed') }}" width="100%" height="auto">
        </div>
        <button id="switchCamera" class="camera-switch">Switch Camera</button>
    </div>
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
''')

# Create the CSS file
with open('static/css/style.css', 'w') as f:
    f.write('''
body {
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    text-align: center;
}

h1 {
    color: #333;
}

.camera-container {
    position: relative;
    width: 100%;
    max-width: 640px;
    margin: 0 auto;
    border: 2px solid #333;
    border-radius: 8px;
    overflow: hidden;
}

.camera-switch {
    margin-top: 20px;
    padding: 10px 20px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

/* Hide switch camera button on desktop */
@media (min-width: 1024px) {
    .camera-switch {
        display: none;
    }
}
''')

# Create the JavaScript file
with open('static/js/script.js', 'w') as f:
    f.write('''
document.addEventListener('DOMContentLoaded', function() {
    const switchCameraButton = document.getElementById('switchCamera');
    let usingFrontCamera = true;
    
    // Check if running on mobile or tablet
    const isMobileOrTablet = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (!isMobileOrTablet) {
        // Hide the button on desktop regardless of CSS
        switchCameraButton.style.display = 'none';
    } else {
        // For mobile/tablet, add click event to switch cameras
        switchCameraButton.addEventListener('click', function() {
            const videoFeed = document.querySelector('img[src*="video_feed"]');
            
            // Add a parameter to the URL to indicate camera change
            // The actual implementation would require server-side changes to handle this
            // This is a simplified version for demonstration
            
            // For a real implementation, we would make an AJAX call to change the camera
            // For now, we'll just reload the page with a parameter
            
            if (usingFrontCamera) {
                // Switch to back camera (camera with index 1)
                fetch('/switch_camera?camera=1')
                    .then(() => {
                        usingFrontCamera = false;
                        videoFeed.src = '{{ url_for("video_feed") }}?camera=1&t=' + new Date().getTime();
                        switchCameraButton.textContent = 'Switch to Front Camera';
                    });
            } else {
                // Switch to front camera (camera with index 0)
                fetch('/switch_camera?camera=0')
                    .then(() => {
                        usingFrontCamera = true;
                        videoFeed.src = '{{ url_for("video_feed") }}?camera=0&t=' + new Date().getTime();
                        switchCameraButton.textContent = 'Switch to Back Camera';
                    });
            }
        });
    }
});
''')

# Add the route to switch cameras
@app.route('/switch_camera')
def switch_camera():
    from flask import request
    global camera_id
    camera_id = int(request.args.get('camera', 0))
    return {'success': True}

if __name__ == '__main__':
    # Global variable for camera ID
    camera_id = 0
    
    # Modify the generate_frames function to use the correct camera
    def generate_frames():
        global camera_id
        camera = cv2.VideoCapture(camera_id)
        
        # Processing every frame would be too CPU intensive, so we'll process every few frames
        process_every_n_frames = 15
        frame_count = 0
        last_processed_frame = None
        
        while True:
            success, frame = camera.read()
            if not success:
                break
            
            frame_count += 1
            
            # Process every Nth frame for ethnicity detection
            if frame_count % process_every_n_frames == 0:
                processed_frame = detect_ethnicity(frame)
                last_processed_frame = processed_frame
            else:
                # If we have a previously processed frame, use its detection boxes
                if last_processed_frame is not None:
                    # Just display the original frame with the previous detection results
                    frame = last_processed_frame
            
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            # Yield the frame in byte format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            # Small delay to reduce CPU usage
            time.sleep(0.01)
        
        camera.release()
    
    app.run(debug=True, host='0.0.0.0')
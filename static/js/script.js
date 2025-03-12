
document.addEventListener('DOMContentLoaded', function() {
    const switchCameraButton = document.getElementById('switchCamera');
    const fpsValue = document.getElementById('fpsValue');
    let usingFrontCamera = true;
    
    // FPS counter
    let frameCount = 0;
    let lastTime = Date.now();
    const fpsUpdateInterval = 1000; // Update FPS every second
    
    // Count frames for FPS calculation
    const videoFeed = document.querySelector('img[src*="video_feed"]');
    videoFeed.onload = function() {
        frameCount++;
        const now = Date.now();
        const elapsed = now - lastTime;
        
        if (elapsed >= fpsUpdateInterval) {
            const fps = Math.round((frameCount * 1000) / elapsed);
            fpsValue.textContent = fps;
            frameCount = 0;
            lastTime = now;
        }
    };
    
    // Check if running on mobile or tablet
    const isMobileOrTablet = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (!isMobileOrTablet) {
        // Hide the button on desktop regardless of CSS
        switchCameraButton.style.display = 'none';
    } else {
        // For mobile/tablet, add click event to switch cameras
        switchCameraButton.addEventListener('click', function() {
            const videoFeed = document.querySelector('img[src*="video_feed"]');
            
            if (usingFrontCamera) {
                // Switch to back camera (camera with index 1)
                fetch('/switch_camera?camera=1')
                    .then(() => {
                        usingFrontCamera = false;
                        // Force reload the video feed by adding a timestamp
                        videoFeed.src = '{{ url_for("video_feed") }}?camera=1&t=' + new Date().getTime();
                        switchCameraButton.textContent = 'Switch to Front Camera';
                    });
            } else {
                // Switch to front camera (camera with index 0)
                fetch('/switch_camera?camera=0')
                    .then(() => {
                        usingFrontCamera = true;
                        // Force reload the video feed by adding a timestamp
                        videoFeed.src = '{{ url_for("video_feed") }}?camera=0&t=' + new Date().getTime();
                        switchCameraButton.textContent = 'Switch to Back Camera';
                    });
            }
        });
    }
});

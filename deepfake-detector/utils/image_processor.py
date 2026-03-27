"""
Image processing utilities
"""

import cv2
import numpy as np
from PIL import Image
import io


def validate_image(image_bytes):
    """Validate image file"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        return True, "Valid image"
    except Exception as e:
        return False, f"Invalid image: {str(e)}"


def get_image_info(image_path):
    """Get image information"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        height, width = img.shape[:2]
        channels = img.shape[2] if len(img.shape) > 2 else 1
        
        return {
            'width': width,
            'height': height,
            'channels': channels,
            'size_mb': round(img.nbytes / (1024 * 1024), 2)
        }
    except Exception as e:
        return None


def preprocess_face(image):
    """Extract and preprocess face from image"""
    try:
        # Load face cascade
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        
        # Extract face
        face = image[y:y+h, x:x+w]
        
        # Resize
        face = cv2.resize(face, (224, 224))
        
        return face
        
    except Exception as e:
        print(f"Face preprocessing error: {e}")
        return None
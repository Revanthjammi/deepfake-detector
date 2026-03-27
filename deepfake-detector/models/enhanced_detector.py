"""
Enhanced detector with better fake detection
"""

import sys
import os
import numpy as np
import cv2
from PIL import Image
import torch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DETECTION_THRESHOLD, BIAS_CORRECTION


class EnhancedDeepfakeDetector:
    """Enhanced detector specifically tuned to detect fakes"""
    
    def __init__(self, base_detector):
        self.base_detector = base_detector
        self.model_manager = base_detector.model_manager
        
    def detect_image(self, image_path):
        """
        Enhanced detection with fake image sensitivity
        """
        # Get base prediction
        result = self.base_detector.basic_detection(image_path)
        
        # Extract detailed features for better fake detection
        detailed_features = self.extract_deep_features(image_path)
        
        # Combine with model predictions
        enhanced_probability = self.combine_predictions(result, detailed_features)
        
        # Apply bias correction if needed
        enhanced_probability = np.clip(enhanced_probability + BIAS_CORRECTION, 0.01, 0.99)
        
        # Final decision
        is_fake = enhanced_probability > DETECTION_THRESHOLD
        
        # Calculate confidence
        confidence = enhanced_probability if is_fake else 1 - enhanced_probability
        
        # Update result
        result['probability'] = float(enhanced_probability)
        result['is_fake'] = bool(is_fake)
        result['confidence'] = float(confidence)
        result['detailed_features'] = detailed_features
        
        # Add detection reasoning
        result['reasoning'] = self.generate_reasoning(detailed_features, enhanced_probability)
        
        return result
    
    def extract_deep_features(self, image_path):
        """
        Extract deep features that indicate fakes
        """
        img = cv2.imread(image_path)
        if img is None:
            return {}
        
        features = {}
        
        # 1. Face detection and analysis
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        features['face_count'] = len(faces)
        
        if len(faces) > 0:
            # Get largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            face = img[y:y+h, x:x+w]
            
            # 2. Analyze skin texture (fakes often have smooth skin)
            face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(face_gray, cv2.CV_64F).var()
            features['texture_variance'] = float(laplacian_var)
            
            # Smooth skin (low texture) indicates possible fake
            features['fake_texture_score'] = float(1.0 - min(1.0, laplacian_var / 200))
            
            # 3. Edge analysis
            edges = cv2.Canny(face_gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            features['edge_density'] = float(edge_density)
            
            # Low edge density indicates possible fake
            features['fake_edge_score'] = float(1.0 - min(1.0, edge_density * 10))
            
        else:
            # No face detected - analyze whole image
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            features['texture_variance'] = float(laplacian_var)
            features['fake_texture_score'] = float(1.0 - min(1.0, laplacian_var / 200))
            features['face_count'] = 0
            features['fake_edge_score'] = 0.5
        
        # 4. Noise pattern analysis
        noise = self.extract_noise_pattern(img)
        features['noise_level'] = float(noise)
        features['fake_noise_score'] = float(min(1.0, noise / 30))
        
        # 5. Compression artifacts
        compression_score = self.detect_compression_artifacts(img)
        features['compression_score'] = float(compression_score)
        
        # 6. Color analysis
        color_score = self.analyze_color_distribution(img)
        features['color_score'] = float(color_score)
        
        # 7. Combined fake score from features
        feature_scores = [
            features.get('fake_texture_score', 0.5),
            features.get('fake_edge_score', 0.5),
            features.get('fake_noise_score', 0.5),
            compression_score,
            color_score
        ]
        
        # Remove any None values
        feature_scores = [s for s in feature_scores if s is not None]
        
        if feature_scores:
            features['combined_feature_score'] = float(np.mean(feature_scores))
        else:
            features['combined_feature_score'] = 0.5
        
        return features
    
    def extract_noise_pattern(self, image):
        """Extract noise pattern from image"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply high-pass filter to isolate noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = gray - blurred
        
        return float(np.std(noise))
    
    def detect_compression_artifacts(self, image):
        """Detect JPEG compression artifacts"""
        try:
            # Simulate JPEG compression at different qualities
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, encoded = cv2.imencode('.jpg', image, encode_param)
            decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
            
            # Calculate difference
            diff = cv2.absdiff(image, decoded)
            
            # Block artifacts (8x8 blocks typical in JPEG)
            h, w = image.shape[:2]
            block_diff = 0
            blocks = 0
            
            for i in range(0, h-8, 8):
                for j in range(0, w-8, 8):
                    block = diff[i:i+8, j:j+8]
                    block_diff += np.mean(block)
                    blocks += 1
            
            if blocks > 0:
                block_diff /= blocks
            
            # Higher block diff = more compression artifacts = possible fake
            return float(min(1.0, block_diff / 50))
        except:
            return 0.5
    
    def analyze_color_distribution(self, image):
        """Analyze color distribution for unnatural patterns"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Check saturation distribution
            saturation = hsv[:, :, 1]
            sat_std = np.std(saturation)
            
            # Unnatural saturation patterns
            if sat_std < 20:
                return 0.7  # Unnatural - possible fake
            elif sat_std > 60:
                return 0.3  # Natural variation
            else:
                return 0.5
        except:
            return 0.5
    
    def combine_predictions(self, model_result, features):
        """
        Combine model predictions with feature analysis
        """
        # Get model probability
        model_prob = model_result.get('probability', 0.5)
        
        # Get feature-based probability
        feature_prob = features.get('combined_feature_score', 0.5)
        
        # Weighted combination based on feature strength
        if feature_prob > 0.6:
            # Features strongly indicate fake, increase weight
            combined = (model_prob * 0.4) + (feature_prob * 0.6)
        elif feature_prob < 0.4:
            # Features strongly indicate real, decrease weight
            combined = (model_prob * 0.7) + (feature_prob * 0.3)
        else:
            # Features are ambiguous, trust model more
            combined = (model_prob * 0.8) + (feature_prob * 0.2)
        
        return combined
    
    def generate_reasoning(self, features, probability):
        """
        Generate human-readable reasoning for detection
        """
        reasons = []
        
        if probability > 0.7:
            reasons.append("Strong indicators of AI generation detected")
        elif probability > 0.6:
            reasons.append("Moderate indicators of AI generation")
        
        # Texture analysis
        texture_score = features.get('fake_texture_score', 0.5)
        if texture_score > 0.7:
            reasons.append("Unusually smooth skin texture detected (common in deepfakes)")
        elif texture_score > 0.5:
            reasons.append("Slightly abnormal texture patterns")
        
        # Edge analysis
        edge_score = features.get('fake_edge_score', 0.5)
        if edge_score > 0.7:
            reasons.append("Inconsistent edge patterns around facial features")
        
        # Noise analysis
        noise_score = features.get('fake_noise_score', 0.5)
        if noise_score > 0.7:
            reasons.append("Unnatural noise patterns in image")
        
        # Compression artifacts
        compression = features.get('compression_score', 0.5)
        if compression > 0.7:
            reasons.append("Heavy compression artifacts detected")
        
        # Face detection
        face_count = features.get('face_count', 0)
        if face_count == 0:
            reasons.append("No clear face detected in image")
        elif face_count > 1:
            reasons.append(f"Multiple faces ({face_count}) detected in image")
        
        if not reasons:
            reasons.append("Image appears authentic")
        
        return " | ".join(reasons[:3])  # Limit to top 3 reasons
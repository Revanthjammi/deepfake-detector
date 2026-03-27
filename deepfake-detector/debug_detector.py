# debug_detection.py
import sys
sys.path.append('F:/deepfake-detector')

from models.detector import detector
import cv2
import numpy as np

def analyze_image_detailed(image_path):
    """Detailed analysis of why an image is being flagged"""
    
    print("="*70)
    print(f"🔍 DETAILED ANALYSIS: {image_path}")
    print("="*70)
    
    # Get detection result
    result = detector.detect_image(image_path)
    
    print(f"\n📊 DETECTION RESULT:")
    print(f"   Predicted: {'FAKE' if result['is_fake'] else 'REAL'}")
    print(f"   Probability: {result['probability']*100:.2f}%")
    print(f"   Confidence: {result['confidence']*100:.2f}%")
    
    # Show model scores
    if result.get('scores'):
        print(f"\n🤖 MODEL SCORES:")
        for model, score in result['scores'].items():
            fake_percent = score * 100
            status = "⚠️ FAKE" if score > 0.5 else "✅ REAL"
            print(f"   {model}: {fake_percent:.1f}% -> {status}")
    
    # Show feature scores
    if result.get('detailed_features'):
        print(f"\n🔬 FEATURE ANALYSIS:")
        features = result['detailed_features']
        
        if 'fake_texture_score' in features:
            texture = features['fake_texture_score'] * 100
            print(f"   Texture Score: {texture:.1f}% (higher = more fake)")
        
        if 'fake_edge_score' in features:
            edges = features['fake_edge_score'] * 100
            print(f"   Edge Score: {edges:.1f}% (higher = more fake)")
        
        if 'fake_noise_score' in features:
            noise = features['fake_noise_score'] * 100
            print(f"   Noise Score: {noise:.1f}% (higher = more fake)")
        
        if 'compression_score' in features:
            compression = features['compression_score'] * 100
            print(f"   Compression Score: {compression:.1f}% (higher = more fake)")
        
        if 'combined_feature_score' in features:
            combined = features['combined_feature_score'] * 100
            print(f"   Combined Feature Score: {combined:.1f}%")
    
    # Show reasoning
    if result.get('reasoning'):
        print(f"\n💡 REASONING:")
        print(f"   {result['reasoning']}")
    
    # Analyze image quality
    img = cv2.imread(image_path)
    if img is not None:
        print(f"\n📸 IMAGE QUALITY:")
        print(f"   Resolution: {img.shape[1]}x{img.shape[0]}")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Check sharpness
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:
            print(f"   ⚠️ Image may be blurry (sharpness: {laplacian_var:.0f})")
        else:
            print(f"   ✅ Image is sharp (sharpness: {laplacian_var:.0f})")
        
        # Check face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            print(f"   ✅ Face detected ({len(faces)} face(s))")
            for i, (x, y, w, h) in enumerate(faces):
                print(f"      Face {i+1}: {w}x{h} pixels")
        else:
            print(f"   ⚠️ No face detected in image")
    
    return result

# Test your real image
image_path = input("📸 Enter path to your REAL image: ").strip().strip('"')
result = analyze_image_detailed(image_path)

print("\n" + "="*70)
print("💡 RECOMMENDATION:")
print("="*70)

if result['probability'] > 0.5:
    print("Your real image is being detected as FAKE. This usually happens because:")
    print("1. Image quality is low (blurry, compressed)")
    print("2. Unusual lighting or shadows")
    print("3. No clear face detected")
    print("4. Image has filters or editing")
    print("\nTry uploading a clearer, well-lit front-facing photo.")
else:
    print("✅ Your image is correctly identified as REAL!")
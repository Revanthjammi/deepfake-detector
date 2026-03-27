"""
FINAL DeepFake Detector (Production Ready)

Includes:
- Image detection (face + full image)
- Video detection (20 frames + temporal + variance)
- NaN bug fix
- REAL / FAKE / UNCERTAIN classification
"""

import os
from datetime import datetime
from PIL import Image
import cv2
import numpy as np

from models.model_manager import model_manager
from utils.image_processor import preprocess_face


class DeepFakeDetector:
    def __init__(self):
        self.model_manager = model_manager

        print("\n🔍 Initializing DeepFake Detector")

        if self.model_manager and self.model_manager.model:
            print("✅ Model ready")
        else:
            print("⚠️ Model not loaded")

    # ==========================================================
    # IMAGE DETECTION
    # ==========================================================
    def detect_image(self, image_path):

        print(f"\n🖼️ Analyzing image: {os.path.basename(image_path)}")

        try:
            img_cv = cv2.imread(image_path)
            if img_cv is None:
                raise ValueError("Could not read image")

            # FULL IMAGE
            full_img = Image.open(image_path).convert("RGB")
            full_prob = self.model_manager.predict(full_img)

            # FACE
            face_prob = None
            face = preprocess_face(img_cv)

            if face is not None:
                face_img = Image.fromarray(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
                face_prob = self.model_manager.predict(face_img)

            # COMBINE
            if face_prob is not None:
                probability = (full_prob + face_prob) / 2
            else:
                probability = full_prob

            # CLAMP
            probability = float(min(max(probability, 0.05), 0.95))

            # CLASSIFICATION
            if probability > 0.75:
                label = "FAKE"
                is_fake = True
            elif probability < 0.35:
                label = "REAL"
                is_fake = False
            else:
                label = "UNCERTAIN"
                is_fake = False

            # CONFIDENCE
            confidence = max(abs(probability - 0.5) * 2, 0.3)

            print(f"[IMAGE] Full: {full_prob:.3f}, Face: {face_prob}, Final: {probability:.3f}")

            return {
                'status': 'success',
                'media_type': 'image',
                'filename': os.path.basename(image_path),
                'label': label,
                'is_fake': bool(is_fake),
                'probability': probability,
                'confidence': confidence,
                'analysis_time': datetime.now().isoformat(),
                'model_used': 'Face + Full Image Model'
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            return {'status': 'error', 'error': str(e)}

    # ==========================================================
    # VIDEO DETECTION (FINAL FIXED)
    # ==========================================================
    def detect_video(self, video_path):

        print(f"\n🎥 Analyzing video: {os.path.basename(video_path)}")

        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise ValueError("Cannot open video")

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            sample_frames = []

            # 🔥 SAMPLE ~20 FRAMES
            step = max(1, frame_count // 20)

            for i in range(0, frame_count, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret and frame is not None:
                    sample_frames.append(frame)

                if len(sample_frames) >= 20:
                    break

            cap.release()

            probabilities = []

            for frame in sample_frames:
                try:
                    face = preprocess_face(frame)

                    if face is not None:
                        image = Image.fromarray(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
                    else:
                        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                    prob = self.model_manager.predict(image)

                    if prob is not None:
                        probabilities.append(float(prob))

                except:
                    continue

            # -----------------------------
            # SAFE MEAN + VARIANCE
            # -----------------------------
            if len(probabilities) == 0:
                avg_prob = 0.5
                variance = 0.0
            else:
                avg_prob = float(np.mean(probabilities))
                variance = float(np.std(probabilities))

            # -----------------------------
            # TEMPORAL ANALYSIS
            # -----------------------------
            frame_diffs = []

            for i in range(len(sample_frames) - 1):
                try:
                    diff = np.mean(cv2.absdiff(sample_frames[i], sample_frames[i + 1]))
                    frame_diffs.append(diff)
                except:
                    continue

            if len(frame_diffs) == 0:
                temporal_score = 0.0
            else:
                temporal_score = float(np.mean(frame_diffs))

            # -----------------------------
            # ADJUSTMENTS
            # -----------------------------
            if temporal_score < 3:
                avg_prob += 0.15

            if variance > 0.2:
                avg_prob += 0.1

            if 0.55 < avg_prob < 0.75:
                avg_prob += 0.1

            # CLAMP
            avg_prob = float(min(max(avg_prob, 0.05), 0.95))

            # -----------------------------
            # FINAL CLASSIFICATION
            # -----------------------------
            if avg_prob > 0.75:
                label = "FAKE"
                is_fake = True
            elif avg_prob < 0.35:
                label = "REAL"
                is_fake = False
            else:
                label = "UNCERTAIN"
                is_fake = False

            confidence = max(abs(avg_prob - 0.5) * 2, 0.3)

            print("Probabilities:", probabilities)
            print("Avg:", avg_prob)
            print("Temporal:", temporal_score)
            print("Variance:", variance)

            return {
                'status': 'success',
                'media_type': 'video',
                'filename': os.path.basename(video_path),
                'label': label,
                'is_fake': bool(is_fake),
                'probability': avg_prob,
                'confidence': confidence,
                'frames_analyzed': len(probabilities),
                'temporal_score': temporal_score,
                'variance': variance,
                'analysis_time': datetime.now().isoformat(),
                'model_used': 'Enhanced Video Detection Model'
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            return {'status': 'error', 'error': str(e)}


# GLOBAL INSTANCE
detector = DeepFakeDetector()
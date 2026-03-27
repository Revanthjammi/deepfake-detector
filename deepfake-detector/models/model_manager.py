"""
FINAL WORKING Model Manager for DeepFake Detection
Uses a stable HuggingFace model (no processor errors)
"""

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification


class RealDeepfakeModel:
    def __init__(self):
        print("\n" + "=" * 60)
        print("🚀 LOADING REAL MODEL (FIXED VERSION)")
        print("=" * 60)

        # Device setup
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device: {self.device.upper()}")

        # ✅ WORKING MODEL (stable)
        self.model_name = "dima806/deepfake_vs_real_image_detection"

        try:
            print("\n📥 Downloading / Loading model...")

            # Load processor (safe)
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)

            # Load model
            self.model = AutoModelForImageClassification.from_pretrained(self.model_name)

            self.model.to(self.device)
            self.model.eval()

            print("✅ Model loaded successfully!")

        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            print("⚠️ Falling back to safe mode...")
            self.model = None
            self.processor = None

    def predict(self, image: Image.Image):
        """
        Returns probability that image is FAKE (0 to 1)
        """

        if self.model is None or self.processor is None:
            print("⚠️ Model not available, returning neutral value")
            return 0.5

        try:
            # Ensure image format
            image = image.convert("RGB")

            # Preprocess
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Convert logits to probabilities
            probs = torch.softmax(outputs.logits, dim=1)

            # ⚠️ Class 1 = FAKE (based on model)
            fake_prob = probs[0][1].item()

            return float(fake_prob)

        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return 0.5


# ==========================================================
# MODEL MANAGER (used by your detector)
# ==========================================================

class ModelManager:
    def __init__(self):
        self.model = None

        try:
            self.model = RealDeepfakeModel()
            print("✅ ModelManager ready!")
        except Exception as e:
            print(f"⚠️ ModelManager failed: {e}")
            self.model = None

    def predict(self, image):
        """
        Wrapper for prediction
        """
        if self.model is None:
            return 0.5

        return self.model.predict(image)


# Global instance (IMPORTANT)
model_manager = ModelManager()
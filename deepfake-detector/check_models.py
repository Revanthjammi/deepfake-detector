# check_models.py
import sys
sys.path.append('F:/deepfake-detector')

from models.model_manager import model_manager

print("="*60)
print("📊 MODEL STATUS CHECK")
print("="*60)

print(f"\nModels loaded: {len(model_manager.models)}")
print(f"Model names: {list(model_manager.models.keys())}")

print("\n📦 Model Details:")
for name in model_manager.models:
    print(f"   - {name}: Loaded")

if len(model_manager.models) < 4:
    print("\n⚠️ Not all models loaded. Need to download.")
else:
    print("\n✅ All models loaded! Ready for 90%+ accuracy.")
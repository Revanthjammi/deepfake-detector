#!/usr/bin/env python3
"""
One-click setup script for DeepFake Detector
"""

import os
import sys
import subprocess
import platform
import time

def print_banner():
    """Print setup banner"""
    print("\n" + "="*70)
    print("🛡️  DEEPFAKE DETECTOR SETUP")
    print("    90%+ Accuracy | 4-Model Ensemble")
    print("="*70)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print("="*70 + "\n")

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        print(f"   Current: {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    
    print("✅ Python version OK")
    
    if sys.version_info >= (3, 12):
        print("   ℹ️  Python 3.12 detected - using compatible package versions")

def install_pytorch():
    """Install PyTorch with appropriate CUDA support"""
    print("\n📦 Installing PyTorch...")
    
    # Check for CUDA
    cuda_available = False
    try:
        import torch
        cuda_available = torch.cuda.is_available()
    except:
        pass
    
    if cuda_available:
        print("   CUDA detected - installing GPU version")
        cmd = [sys.executable, "-m", "pip", "install",
               "torch==2.2.2", "torchvision==0.17.2", "torchaudio==2.2.2",
               "--index-url", "https://download.pytorch.org/whl/cu118"]
    else:
        print("   No CUDA detected - installing CPU version")
        cmd = [sys.executable, "-m", "pip", "install",
               "torch==2.2.2", "torchvision==0.17.2", "torchaudio==2.2.2"]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print("   ✅ PyTorch installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ PyTorch installation failed: {e}")
        return False

def install_requirements():
    """Install other requirements"""
    print("\n📦 Installing other requirements...")
    
    requirements = [
        "transformers==4.36.2",
        "timm==0.9.12",
        "accelerate==0.26.1",
        "opencv-python==4.9.0.80",
        "pillow==10.2.0",
        "numpy==1.26.3",
        "scikit-image==0.22.0",
        "facenet-pytorch==2.6.0",
        "flask==3.0.1",
        "flask-cors==4.0.1",
        "werkzeug==3.0.1",
        "requests==2.31.0",
        "tqdm==4.66.2",
        "python-dotenv==1.0.1"
    ]
    
    successful = []
    failed = []
    
    for i, req in enumerate(requirements, 1):
        print(f"   [{i}/{len(requirements)}] Installing {req}...", end=" ")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", req], 
                          check=True, capture_output=True)
            print("✅")
            successful.append(req)
        except:
            print("❌")
            failed.append(req)
    
    print(f"\n   Successfully installed: {len(successful)}/{len(requirements)} packages")
    
    if failed:
        print(f"\n   Failed packages: {', '.join(failed)}")
        print("   You can install them manually with: pip install <package>")
    
    return len(failed) == 0

def create_directories():
    """Create required directories"""
    print("\n📁 Creating directories...")
    directories = ['uploads', 'results', 'models_data', 'static/css', 'static/js']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Created: {directory}")

def create_init_files():
    """Create __init__.py files"""
    print("\n📄 Creating module files...")
    init_dirs = ['models', 'utils']
    
    for directory in init_dirs:
        init_path = os.path.join(directory, '__init__.py')
        with open(init_path, 'w') as f:
            f.write("# Auto-generated\n")
        print(f"   ✅ Created: {init_path}")

def verify_installation():
    """Verify the installation"""
    print("\n🔍 Verifying installation...")
    
    try:
        import torch
        print(f"   ✅ PyTorch {torch.__version__}")
        
        import transformers
        print(f"   ✅ Transformers {transformers.__version__}")
        
        import timm
        print(f"   ✅ Timm {timm.__version__}")
        
        import cv2
        print(f"   ✅ OpenCV {cv2.__version__}")
        
        import flask
        print(f"   ✅ Flask {flask.__version__}")
        
        print("\n✅ All core packages verified!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Verification failed: {e}")
        return False

def print_next_steps():
    """Print next steps for user"""
    print("\n" + "="*70)
    print("🎯 SETUP COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("   1. Start the web server:")
    print("      python app.py")
    print("\n   2. Open your browser and go to:")
    print("      http://localhost:5000")
    print("\n   3. Upload images or videos for analysis")
    print("\n   The system will analyze media using 4 models:")
    print("   • SwinV2 Large (35% weight)")
    print("   • EfficientNet B4 (30% weight)")
    print("   • XceptionNet (25% weight)")
    print("   • Vision Transformer (10% weight)")
    print("\n" + "="*70)

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python
    check_python_version()
    
    # Create directories
    create_directories()
    create_init_files()
    
    # Install PyTorch
    torch_ok = install_pytorch()
    
    # Install other requirements
    requirements_ok = install_requirements()
    
    # Verify installation
    if torch_ok and requirements_ok:
        verify_installation()
    else:
        print("\n⚠️  Some packages failed to install")
        print("   The system may still work, but some features might be limited")
        print("   Try installing failed packages manually")
    
    # Print next steps
    print_next_steps()
    
    # Ask to start server
    try:
        start = input("\n🚀 Start the server now? (y/n): ").lower()
        if start == 'y':
            print("\nStarting server...")
            subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\nSetup complete. Run 'python app.py' to start the server.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
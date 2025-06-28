# Save this as: auto_install_playwright.py
import subprocess
import sys
import os
from pathlib import Path
import time

def install_browsers():
    """Install Playwright browsers automatically"""
    print("🔍 Checking for Playwright browsers...")
    
    # Check if browsers exist
    browser_paths = [
        Path.home() / ".cache" / "ms-playwright" / "chromium_headless_shell-1179",
        Path.home() / ".cache" / "ms-playwright" / "chromium-1179"
    ]
    
    for path in browser_paths:
        if path.exists() and any(path.rglob("*")):
            print(f"✅ Browser found at: {path}")
            return True
    
    print("❌ No browsers found. Installing...")
    
    try:
        # Install chromium browser
        print("📦 Installing Chromium browser...")
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=600)
        
        print(f"📦 Install output: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Install warnings: {result.stderr}")
        
        if result.returncode != 0:
            print(f"❌ Browser installation failed with code: {result.returncode}")
            return False
        
        # Install dependencies
        print("🔧 Installing browser dependencies...")
        dep_result = subprocess.run([
            sys.executable, "-m", "playwright", "install-deps"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
        
        print(f"🔧 Deps output: {dep_result.stdout}")
        if dep_result.stderr:
            print(f"⚠️ Deps warnings: {dep_result.stderr}")
        
        # Verify installation
        time.sleep(2)  # Wait for files to be written
        for path in browser_paths:
            if path.exists():
                print(f"✅ Installation verified: {path}")
                return True
        
        print("❌ Installation completed but browsers not found")
        return False
        
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

# Auto-execute when imported
print("🚀 Auto-installing Playwright browsers...")
install_browsers()
print("✅ Playwright setup complete")
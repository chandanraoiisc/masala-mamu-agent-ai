import subprocess
import sys
import os

def install_playwright():
    """Install playwright browsers during deployment"""
    try:
        print("Installing Playwright browsers...")
        subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], check=True, timeout=600)
        
        subprocess.run([
            sys.executable, "-m", "playwright", "install-deps"
        ], check=True, timeout=300)
        
        print("Playwright browsers installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Playwright: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_playwright()
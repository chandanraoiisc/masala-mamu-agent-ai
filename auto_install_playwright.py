# streamlit_playwright_setup.py
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

def setup_playwright_for_streamlit():
    """Setup Playwright for Streamlit Cloud environment"""
    print("🔍 Setting up Playwright for Streamlit Cloud...")
    
    try:
        # Install playwright package first
        print("📦 Installing Playwright package...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], 
                      check=True, capture_output=True, text=True)
        
        # Try to install chromium with specific flags for headless environments
        print("🌐 Installing Chromium browser...")
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium", 
            "--with-deps"  # This tries to install deps without sudo
        ], capture_output=True, text=True, timeout=600)
        
        print(f"📦 Install stdout: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Install stderr: {result.stderr}")
        
        # Alternative: Use chromium-browser package if available
        if result.returncode != 0:
            print("🔄 Trying alternative browser installation...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "chromium-browser"], 
                              check=True, capture_output=True, text=True)
                print("✅ Chromium browser package installed")
            except subprocess.CalledProcessError:
                print("❌ Alternative browser installation failed")
        
        # Set environment variables for headless operation
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(Path.home() / ".cache" / "ms-playwright")
        os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '0'
        
        print("✅ Playwright setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

def get_browser_launch_options():
    """Get browser launch options optimized for Streamlit Cloud"""
    return {
        'headless': True,
        'args': [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',
            '--disable-javascript',  # Only if you don't need JS
            '--virtual-time-budget=30000',  # Timeout for page loads
            '--single-process',  # Use single process mode
        ]
    }

def test_playwright_setup():
    """Test if Playwright is working"""
    try:
        from playwright.async_api import async_playwright
        import asyncio
        
        async def test_browser():
            async with async_playwright() as p:
                browser = await p.chromium.launch(**get_browser_launch_options())
                page = await browser.new_page()
                await page.goto('https://httpbin.org/get')
                content = await page.content()
                await browser.close()
                return "httpbin" in content.lower()
        
        result = asyncio.run(test_browser())
        print(f"🧪 Browser test result: {'✅ PASSED' if result else '❌ FAILED'}")
        return result
        
    except Exception as e:
        print(f"🧪 Browser test error: {e}")
        return False

# Auto-execute setup
if __name__ == "__main__" or True:  # Always run when imported
    print("🚀 Starting Playwright setup for Streamlit Cloud...")
    setup_success = setup_playwright_for_streamlit()
    
    if setup_success:
        print("🧪 Testing browser functionality...")
        test_playwright_setup()
    
    print("🎯 Setup complete - use get_browser_launch_options() for browser config")
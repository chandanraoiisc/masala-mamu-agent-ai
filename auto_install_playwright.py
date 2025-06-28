# streamlit_playwright_setup.py
import subprocess
import sys
import os
from pathlib import Path
import time

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
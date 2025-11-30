"""
Setup script for ScreenSense AI
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def install_requirements():
    """Install required packages"""
    logger.info("Installing requirements...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        logger.info("Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e}")
        return False


def setup_directories():
    """Create necessary directories"""
    from pathlib import Path
    
    directories = ['data', 'models', 'logs', 'modules']
    for dir_name in directories:
        path = Path(dir_name)
        path.mkdir(exist_ok=True)
        logger.info(f"Created directory: {dir_name}")


def main():
    """Main setup function"""
    logger.info("Setting up ScreenSense AI...")
    
    setup_directories()
    
    if install_requirements():
        logger.info("Setup completed successfully!")
        logger.info("You can now run: python screensense_ai.py")
    else:
        logger.error("Setup failed. Please install requirements manually.")


if __name__ == "__main__":
    main()
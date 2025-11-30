"""
Configuration file for ScreenSense AI
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Screen capture settings
CAPTURE_INTERVAL = 0.2  # seconds (200ms)
TARGET_IMAGE_SIZE = (640, 480)  # (width, height)

# CNN Model settings
MODEL_PATH = MODELS_DIR / "ui_detector.pth"
CONFIDENCE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.4

# OCR settings
OCR_LANGUAGES = ['en']  # Fixed: use 'en' instead of 'eng'
OCR_CONFIDENCE_THRESHOLD = 0.6

# UI Element classes
UI_CLASSES = [
    'button',
    'input',
    'popup',
    'ad',
    'warning',
    'checkbox',
    'dropdown',
    'link',
    'text',
    'image'
]

# Screen type detection thresholds
SCAM_KEYWORDS = [
    'urgent', 'limited time', 'click now', 'congratulations',
    'you won', 'free gift', 'act now', 'verify account'
]

# Safety settings
ASK_CONFIRMATION_ACTIONS = [
    'autofill', 'click', 'close_popup'
]
HIGH_RISK_DOMAINS = []

# Action execution settings
ACTION_DELAY = 0.5  # seconds between actions
MAX_RETRIES = 3

# Logging settings
LOG_LEVEL = "INFO"
LOG_DETECTIONS = True
LOG_DECISIONS = True
LOG_ACTIONS = True

# Learning settings
RETRAIN_THRESHOLD = 100  # number of corrections before retraining
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EPOCHS = 10
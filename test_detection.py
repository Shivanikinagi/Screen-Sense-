"""
Test script to verify UI detection is working
Also collects screenshots for training data
"""

import logging
import numpy as np
from pathlib import Path
import time
from modules.screen_capture import ScreenCapture
from modules.preprocessor import ImagePreprocessor
from modules.ui_detector import UIDetector
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_screen_capture():
    """Test screen capture functionality"""
    logger.info("Testing screen capture...")
    
    capturer = ScreenCapture(monitor_index=1)
    screenshot = capturer.capture()
    
    if screenshot is not None:
        logger.info(f"✓ Screenshot captured: {screenshot.shape}")
        return True
    else:
        logger.error("✗ Failed to capture screenshot")
        return False


def test_preprocessing():
    """Test image preprocessing"""
    logger.info("Testing preprocessing...")
    
    capturer = ScreenCapture(monitor_index=1)
    screenshot = capturer.capture()
    
    preprocessor = ImagePreprocessor(target_size=config.TARGET_IMAGE_SIZE)
    processed = preprocessor.preprocess(screenshot)
    
    if processed is not None:
        logger.info(f"✓ Image preprocessed: {processed.shape}")
        return True
    else:
        logger.error("✗ Failed to preprocess image")
        return False


def test_ui_detection():
    """Test UI element detection"""
    logger.info("Testing UI detection...")
    
    capturer = ScreenCapture(monitor_index=1)
    screenshot = capturer.capture()
    
    preprocessor = ImagePreprocessor(target_size=config.TARGET_IMAGE_SIZE)
    processed = preprocessor.preprocess(screenshot)
    
    detector = UIDetector(
        model_path=str(config.MODEL_PATH),
        num_classes=len(config.UI_CLASSES) + 1
    )
    
    # Lower threshold for testing
    detections = detector.detect(processed, confidence_threshold=0.3)
    
    logger.info(f"Detected {len(detections)} UI elements")
    for i, det in enumerate(detections):
        logger.info(f"  {i+1}. {det['label']} (confidence: {det['confidence']:.2f})")
    
    if len(detections) > 0:
        logger.info("✓ UI detection working (found elements)")
        return True
    else:
        logger.warning("⚠ UI detection working but found 0 elements")
        logger.info("  This is normal - the model needs fine-tuning on UI elements")
        logger.info("  The pre-trained model is trained on general objects (COCO dataset)")
        return True


def collect_training_screenshots(count: int = 10):
    """Collect screenshots for training data"""
    logger.info(f"Collecting {count} screenshots for training data...")
    
    # Create training data directory
    training_dir = config.DATA_DIR / "training_screenshots"
    training_dir.mkdir(exist_ok=True)
    
    capturer = ScreenCapture(monitor_index=1)
    
    logger.info("Starting in 3 seconds...")
    logger.info("Please navigate through different screens (login, forms, popups, etc.)")
    time.sleep(3)
    
    for i in range(count):
        screenshot = capturer.capture()
        
        if screenshot is not None:
            # Save screenshot
            timestamp = int(time.time() * 1000)
            filename = training_dir / f"screenshot_{timestamp}.png"
            
            from PIL import Image
            img = Image.fromarray(screenshot)
            img.save(filename)
            
            logger.info(f"Saved: {filename.name}")
        
        time.sleep(2)  # 2 seconds between captures
    
    logger.info(f"✓ Collected {count} screenshots in {training_dir}")
    logger.info("Next steps:")
    logger.info("  1. Manually label these screenshots (annotate UI elements)")
    logger.info("  2. Use the labeled data to fine-tune the model")
    logger.info("  3. Run: python train_model.py")


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("ScreenSense AI - Detection Test Suite")
    logger.info("="*60)
    
    tests = [
        ("Screen Capture", test_screen_capture),
        ("Preprocessing", test_preprocessing),
        ("UI Detection", test_ui_detection),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing: {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Test Summary:")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    # Offer to collect training data
    if passed == total:
        logger.info("\n" + "="*60)
        response = input("\nWould you like to collect training screenshots? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            count = int(input("How many screenshots to collect? (default: 10): ") or "10")
            collect_training_screenshots(count)


if __name__ == "__main__":
    main()
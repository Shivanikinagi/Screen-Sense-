"""
Check training data status
"""

import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_data():
    """Check training data and annotations"""
    
    # Check screenshots directory
    screenshots_dir = Path("data/training_screenshots")
    
    logger.info("="*60)
    logger.info("Training Data Status Check")
    logger.info("="*60)
    
    if not screenshots_dir.exists():
        logger.error(f"❌ Screenshots directory not found: {screenshots_dir}")
        logger.info("\n📝 Action needed: Collect screenshots")
        logger.info("  Run: python test_detection.py")
        return
    
    # Count screenshots
    screenshots = list(screenshots_dir.glob("*.png"))
    logger.info(f"\n📸 Screenshots:")
    logger.info(f"  Directory: {screenshots_dir}")
    logger.info(f"  Count: {len(screenshots)}")
    
    if len(screenshots) == 0:
        logger.error("  ❌ No screenshots found!")
        logger.info("\n📝 Action needed: Collect screenshots")
        logger.info("  Run: python test_detection.py")
        return
    else:
        logger.info(f"  ✅ Found {len(screenshots)} screenshots")
        # Show first few
        for i, img in enumerate(screenshots[:5]):
            logger.info(f"    - {img.name}")
        if len(screenshots) > 5:
            logger.info(f"    ... and {len(screenshots)-5} more")
    
    # Check annotations file
    annotations_file = Path("data/annotations.json")
    logger.info(f"\n📋 Annotations:")
    logger.info(f"  File: {annotations_file}")
    
    if not annotations_file.exists():
        logger.warning("  ⚠️  Annotations file not found (will be created)")
        logger.info(f"\n📝 Action needed: Label screenshots")
        logger.info("  Run: python label_tool.py")
        return
    
    # Load annotations
    try:
        with open(annotations_file, 'r', encoding='utf-8') as f:
            annotations = json.load(f)
        
        logger.info(f"  Count: {len(annotations)} annotated images")
        
        if len(annotations) == 0:
            logger.warning("  ⚠️  Annotations file is empty")
            logger.info(f"\n📝 Action needed: Label screenshots")
            logger.info("  Run: python label_tool.py")
            return
        
        # Count total bounding boxes
        total_boxes = sum(len(boxes) for boxes in annotations.values())
        logger.info(f"  Total boxes: {total_boxes}")
        
        # Show class distribution
        class_counts = {}
        for image_boxes in annotations.values():
            for box in image_boxes:
                cls = box.get('class', 'unknown')
                class_counts[cls] = class_counts.get(cls, 0) + 1
        
        logger.info(f"\n📊 Class distribution:")
        for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
            logger.info(f"    {cls}: {count}")
        
        # Check if enough data for training
        logger.info(f"\n✅ Ready for training!")
        logger.info(f"  Annotated images: {len(annotations)}")
        logger.info(f"  Total bounding boxes: {total_boxes}")
        
        if len(annotations) < 10:
            logger.warning(f"\n⚠️  Warning: Only {len(annotations)} images annotated")
            logger.info("  Recommended: At least 20-30 images for good results")
            logger.info("  Current status: Will work but may have low accuracy")
        elif len(annotations) < 20:
            logger.info(f"\n✅ Minimum data available ({len(annotations)} images)")
            logger.info("  Status: Can start training, but more data recommended")
        else:
            logger.info(f"\n✅ Good amount of data ({len(annotations)} images)")
            logger.info("  Status: Ready for training!")
        
        logger.info(f"\n🚀 Next steps:")
        if len(annotations) < 20:
            logger.info("  1. (Optional) Label more images: python label_tool.py")
            logger.info("  2. Train the model: python train_model.py --epochs 15")
        else:
            logger.info("  1. Train the model: python train_model.py --epochs 15")
        logger.info("  3. Update config.py: MODEL_PATH = 'models/ui_detector_finetuned.pth'")
        logger.info("  4. Run: python screensense_ai.py")
        
    except json.JSONDecodeError as e:
        logger.error(f"  ❌ Invalid JSON in annotations file: {e}")
        logger.info("\n📝 Action needed: Fix or delete annotations.json and relabel")
    except Exception as e:
        logger.error(f"  ❌ Error reading annotations: {e}")
    
    logger.info("\n" + "="*60)


if __name__ == "__main__":
    check_data()
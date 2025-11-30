"""
Model Training Script
Fine-tunes the UI detector on labeled data
"""

import torch
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
from pathlib import Path
import logging
from PIL import Image
import torchvision.transforms as transforms
import numpy as np
from tqdm import tqdm

from modules.ui_detector import UIDetector
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UIDataset(Dataset):
    """Dataset for UI element detection"""
    
    def __init__(self, annotations_file: str, images_dir: str, transform=None):
        """
        Initialize dataset
        
        Args:
            annotations_file: Path to JSON annotations file
            images_dir: Directory containing images
            transform: Optional transforms
        """
        self.images_dir = Path(images_dir)
        self.transform = transform
        
        # Load annotations
        with open(annotations_file, 'r', encoding='utf-8') as f:
            self.annotations = json.load(f)
        
        # Filter out images without annotations
        self.image_names = [k for k, v in self.annotations.items() if v]
        
        logger.info(f"Loaded {len(self.image_names)} annotated images")
    
    def __len__(self):
        return len(self.image_names)
    
    def __getitem__(self, idx):
        # Load image
        image_name = self.image_names[idx]
        image_path = self.images_dir / image_name
        image = Image.open(image_path).convert('RGB')
        
        # Get original size
        orig_width, orig_height = image.size
        
        # Get annotations
        annotations = self.annotations[image_name]
        
        # Convert to tensors
        boxes = []
        labels = []
        
        for ann in annotations:
            bbox = ann['bbox']
            # Ensure bbox is valid [x1, y1, x2, y2] format
            x1, y1, x2, y2 = bbox
            
            # Clamp to image bounds
            x1 = max(0, min(x1, orig_width))
            y1 = max(0, min(y1, orig_height))
            x2 = max(0, min(x2, orig_width))
            y2 = max(0, min(y2, orig_height))
            
            # Ensure x2 > x1 and y2 > y1
            if x2 <= x1:
                x2 = x1 + 1
            if y2 <= y1:
                y2 = y1 + 1
            
            boxes.append([x1, y1, x2, y2])
            
            # Convert class name to label
            class_name = ann['class']
            if class_name in config.UI_CLASSES:
                label = config.UI_CLASSES.index(class_name) + 1  # +1 for background
            else:
                label = 0  # background
            labels.append(label)
        
        # Skip if no valid boxes
        if len(boxes) == 0:
            boxes = [[0, 0, 1, 1]]  # dummy box
            labels = [0]  # background
        
        # Convert to tensors
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)
        
        # Image transformations
        if self.transform:
            image = self.transform(image)
        
        target = {
            'boxes': boxes,
            'labels': labels
        }
        
        return image, target


def collate_fn(batch):
    """Custom collate function for DataLoader"""
    return tuple(zip(*batch))


def train_one_epoch(model, optimizer, data_loader, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    num_batches = 0
    
    for images, targets in tqdm(data_loader, desc="Training"):
        try:
            # Move to device
            images = list(image.to(device) for image in images)
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            
            # Forward pass (returns loss dict in training mode)
            loss_dict = model(images, targets)
            
            # Check if loss_dict is a dict
            if isinstance(loss_dict, dict):
                losses = sum(loss for loss in loss_dict.values())
            else:
                # If it's already a tensor, use it directly
                losses = loss_dict
            
            # Backward pass
            optimizer.zero_grad()
            losses.backward()
            optimizer.step()
            
            total_loss += losses.item()
            num_batches += 1
            
        except Exception as e:
            logger.warning(f"Error in training batch: {e}")
            continue
    
    return total_loss / max(num_batches, 1)


def validate(model, data_loader, device):
    """Validate the model"""
    model.train()  # Keep in training mode to get loss
    total_loss = 0
    num_batches = 0
    
    with torch.no_grad():
        for images, targets in tqdm(data_loader, desc="Validating"):
            try:
                # Move to device
                images = list(image.to(device) for image in images)
                targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
                
                # Forward pass
                loss_dict = model(images, targets)
                
                # Check if loss_dict is a dict
                if isinstance(loss_dict, dict):
                    losses = sum(loss for loss in loss_dict.values())
                else:
                    losses = loss_dict
                
                total_loss += losses.item()
                num_batches += 1
                
            except Exception as e:
                logger.warning(f"Error in validation batch: {e}")
                continue
    
    return total_loss / max(num_batches, 1)


def test_predictions(model, data_loader, device, num_images=3):
    """Test model predictions on a few images"""
    model.eval()
    logger.info(f"\nTesting predictions on {num_images} images...")
    
    with torch.no_grad():
        for i, (images, targets) in enumerate(data_loader):
            if i >= num_images:
                break
            
            try:
                images = list(image.to(device) for image in images)
                predictions = model(images)
                
                # Show predictions for first image in batch
                if predictions and len(predictions) > 0:
                    pred = predictions[0]
                    num_detections = len(pred['boxes'])
                    logger.info(f"Image {i+1}: Detected {num_detections} elements")
                    
                    if num_detections > 0:
                        # Show top 3 predictions
                        for j in range(min(3, num_detections)):
                            score = pred['scores'][j].item()
                            label = pred['labels'][j].item()
                            if label <= len(config.UI_CLASSES):
                                class_name = config.UI_CLASSES[label - 1]
                            else:
                                class_name = "unknown"
                            logger.info(f"  - {class_name}: {score:.2f}")
            except Exception as e:
                logger.warning(f"Error testing image {i+1}: {e}")


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train UI Detector')
    parser.add_argument('--annotations', type=str,
                       default='data/annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--images', type=str,
                       default='data/training_screenshots',
                       help='Directory containing training images')
    parser.add_argument('--epochs', type=int, default=10,
                       help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=4,
                       help='Batch size for training')
    parser.add_argument('--lr', type=float, default=0.0005,
                       help='Learning rate')
    parser.add_argument('--save-path', type=str,
                       default='models/ui_detector_finetuned.pth',
                       help='Path to save trained model')
    parser.add_argument('--test-every', type=int, default=5,
                       help='Test predictions every N epochs')
    
    args = parser.parse_args()
    
    # Check if annotations exist
    if not Path(args.annotations).exists():
        logger.error(f"Annotations file not found: {args.annotations}")
        logger.info("Please run: python label_tool.py")
        return
    
    # Check if images exist
    if not Path(args.images).exists():
        logger.error(f"Images directory not found: {args.images}")
        return
    
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Create transforms
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    
    # Create dataset
    logger.info("Loading dataset...")
    try:
        dataset = UIDataset(args.annotations, args.images, transform=transform)
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return
    
    if len(dataset) == 0:
        logger.error("No annotated images found!")
        logger.info("Please label some images using: python label_tool.py")
        return
    
    if len(dataset) < 5:
        logger.warning(f"Only {len(dataset)} images - recommend at least 10 for good results")
    
    # Split into train/val
    train_size = max(1, int(0.8 * len(dataset)))
    val_size = max(1, len(dataset) - train_size)
    
    # Adjust if val_size is 0
    if val_size == 0:
        val_size = 1
        train_size = len(dataset) - 1
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    logger.info(f"Train size: {train_size}, Val size: {val_size}")
    
    # Create data loaders with smaller batch size for CPU
    actual_batch_size = min(args.batch_size, train_size)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=actual_batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0  # Windows compatibility
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=1,  # Smaller batch for validation
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0
    )
    
    # Create model
    logger.info("Initializing model...")
    detector = UIDetector(
        model_path=str(config.MODEL_PATH) if config.MODEL_PATH.exists() else None,
        num_classes=len(config.UI_CLASSES) + 1
    )
    model = detector.model.to(device)
    
    # Setup optimizer with lower learning rate
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=2, verbose=True
    )
    
    # Training loop
    logger.info("Starting training...")
    logger.info(f"Batch size: {actual_batch_size}, Learning rate: {args.lr}")
    best_val_loss = float('inf')
    
    for epoch in range(args.epochs):
        logger.info(f"\nEpoch {epoch+1}/{args.epochs}")
        
        # Train
        train_loss = train_one_epoch(model, optimizer, train_loader, device)
        logger.info(f"Train Loss: {train_loss:.4f}")
        
        # Validate
        val_loss = validate(model, val_loader, device)
        logger.info(f"Val Loss: {val_loss:.4f}")
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_path = Path(args.save_path)
            save_path.parent.mkdir(exist_ok=True)
            torch.save(model.state_dict(), save_path)
            logger.info(f"✓ Best model saved (val_loss: {val_loss:.4f})")
        
        # Test predictions periodically
        if (epoch + 1) % args.test_every == 0:
            test_predictions(model, val_loader, device)
    
    logger.info("\n" + "="*60)
    logger.info("Training complete!")
    logger.info(f"Best validation loss: {best_val_loss:.4f}")
    logger.info(f"Model saved to: {args.save_path}")
    logger.info("\n📝 Next steps:")
    logger.info("1. Update config.py:")
    logger.info(f"   MODEL_PATH = MODELS_DIR / '{Path(args.save_path).name}'")
    logger.info("\n2. Test the model:")
    logger.info("   python screensense_ai.py --threshold 0.4")
    logger.info("\n3. If detection is poor:")
    logger.info("   - Label more images (20-30+ recommended)")
    logger.info("   - Train for more epochs: --epochs 20")
    logger.info("   - Lower threshold: --threshold 0.3")
    logger.info("="*60)


if __name__ == "__main__":
    main()
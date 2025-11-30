"""
UI Element Detection Module
Uses CNN to detect UI elements in screenshots
"""

import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
import numpy as np
import logging
from typing import List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class UIDetector:
    """CNN-based UI element detector"""
    
    def __init__(self, model_path: str = None, num_classes: int = 11):
        """
        Initialize UI detector
        
        Args:
            model_path: Path to trained model weights
            num_classes: Number of UI element classes + background
        """
        self.num_classes = num_classes
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model
        self.model = self._load_model(model_path)
        self.model.eval()
        
        # Class names
        self.class_names = [
            'background', 'button', 'input', 'popup', 'ad', 
            'warning', 'checkbox', 'dropdown', 'link', 'text', 'image'
        ]
        
        logger.info(f"UI Detector initialized on {self.device}")
    
    def _load_model(self, model_path: str = None):
        """Load Faster R-CNN model"""
        # Load pre-trained model
        model = fasterrcnn_resnet50_fpn(pretrained=True)
        
        # Replace classifier head
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, self.num_classes)
        
        # Load custom weights if available
        if model_path and Path(model_path).exists():
            try:
                model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info(f"Loaded model weights from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model weights: {e}")
        
        model.to(self.device)
        return model
    
    def detect(self, image: np.ndarray, confidence_threshold: float = 0.5) -> List[dict]:
        """
        Detect UI elements in image
        
        Args:
            image: Input image as numpy array (RGB)
            confidence_threshold: Minimum confidence score
        
        Returns:
            List of detected elements with bounding boxes
        """
        try:
            # Prepare image
            img_tensor = self._prepare_image(image)
            
            # Run detection
            with torch.no_grad():
                predictions = self.model([img_tensor])[0]
            
            # Filter by confidence
            detections = self._filter_predictions(
                predictions, 
                confidence_threshold
            )
            
            logger.debug(f"Detected {len(detections)} UI elements")
            return detections
            
        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return []
    
    def _prepare_image(self, image: np.ndarray) -> torch.Tensor:
        """Convert numpy image to tensor"""
        # Normalize to [0, 1]
        if image.max() > 1:
            image = image / 255.0
        
        # Convert to tensor and move to device
        img_tensor = torch.from_numpy(image).permute(2, 0, 1).float()
        img_tensor = img_tensor.to(self.device)
        
        return img_tensor
    
    def _filter_predictions(self, predictions: dict, threshold: float) -> List[dict]:
        """Filter predictions by confidence threshold"""
        boxes = predictions['boxes'].cpu().numpy()
        labels = predictions['labels'].cpu().numpy()
        scores = predictions['scores'].cpu().numpy()
        
        detections = []
        for box, label, score in zip(boxes, labels, scores):
            if score >= threshold:
                detections.append({
                    'bbox': tuple(box.astype(int)),
                    'label': self.class_names[label],
                    'confidence': float(score)
                })
        
        return detections
    
    def train(self, train_loader, epochs: int = 10, learning_rate: float = 0.001):
        """
        Train the model
        
        Args:
            train_loader: PyTorch DataLoader with training data
            epochs: Number of training epochs
            learning_rate: Learning rate for optimizer
        """
        self.model.train()
        optimizer = torch.optim.SGD(
            self.model.parameters(), 
            lr=learning_rate, 
            momentum=0.9, 
            weight_decay=0.0005
        )
        
        logger.info(f"Starting training for {epochs} epochs")
        
        for epoch in range(epochs):
            epoch_loss = 0
            for images, targets in train_loader:
                images = [img.to(self.device) for img in images]
                targets = [{k: v.to(self.device) for k, v in t.items()} for t in targets]
                
                loss_dict = self.model(images, targets)
                losses = sum(loss for loss in loss_dict.values())
                
                optimizer.zero_grad()
                losses.backward()
                optimizer.step()
                
                epoch_loss += losses.item()
            
            avg_loss = epoch_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        self.model.eval()
        logger.info("Training completed")
    
    def save_model(self, path: str):
        """Save model weights"""
        torch.save(self.model.state_dict(), path)
        logger.info(f"Model saved to {path}")
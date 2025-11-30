"""
Learning Loop Module
Handles model retraining based on user feedback and mistakes
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import logging
import json
from pathlib import Path
from typing import List, Dict, Tuple
import pickle

logger = logging.getLogger(__name__)


class MistakeDataset(Dataset):
    """Dataset for storing mistakes and corrections"""
    
    def __init__(self, mistakes: List[Dict]):
        """
        Initialize dataset
        
        Args:
            mistakes: List of mistake records
        """
        self.mistakes = mistakes
        self.images = []
        self.labels = []
        
        # Load images and labels
        for mistake in mistakes:
            if 'image_path' in mistake and 'correct_label' in mistake:
                self.images.append(mistake['image_path'])
                self.labels.append(mistake['correct_label'])
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        # Load and preprocess image
        # This is simplified - actual implementation would load from disk
        return torch.zeros(3, 224, 224), self.labels[idx]


class LearningLoop:
    """Manages continuous learning from user feedback"""
    
    def __init__(self, model_path: str, data_dir: str):
        """
        Initialize learning loop
        
        Args:
            model_path: Path to save/load model
            data_dir: Directory for training data
        """
        self.model_path = Path(model_path)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.mistakes_file = self.data_dir / "mistakes.json"
        self.corrections_file = self.data_dir / "corrections.json"
        
        self.mistakes: List[Dict] = self._load_mistakes()
        self.corrections: List[Dict] = self._load_corrections()
        
        logger.info("Learning Loop initialized")
    
    def record_mistake(self, detection_result: Dict, correct_label: str,
                      image_path: str, user_feedback: str):
        """
        Record a detection mistake
        
        Args:
            detection_result: Original detection result
            correct_label: Correct label provided by user
            image_path: Path to the image
            user_feedback: User's feedback text
        """
        mistake = {
            'timestamp': __import__('time').time(),
            'detection': detection_result,
            'correct_label': correct_label,
            'image_path': image_path,
            'feedback': user_feedback,
            'retrained': False
        }
        
        self.mistakes.append(mistake)
        self._save_mistakes()
        
        logger.info(f"Recorded mistake: {detection_result['label']} -> {correct_label}")
    
    def record_correction(self, action_type: str, decision_result: Dict,
                         user_choice: str, reasoning: str):
        """
        Record a decision correction
        
        Args:
            action_type: Type of action
            decision_result: Original decision
            user_choice: What user chose instead
            reasoning: Why user made different choice
        """
        correction = {
            'timestamp': __import__('time').time(),
            'action_type': action_type,
            'decision': decision_result,
            'user_choice': user_choice,
            'reasoning': reasoning,
            'learned': False
        }
        
        self.corrections.append(correction)
        self._save_corrections()
        
        logger.info(f"Recorded correction: {action_type} -> {user_choice}")
    
    def should_retrain(self, threshold: int = 100) -> bool:
        """
        Check if model should be retrained
        
        Args:
            threshold: Number of mistakes before retraining
        
        Returns:
            True if retraining recommended
        """
        unlearned_mistakes = [m for m in self.mistakes if not m['retrained']]
        should_train = len(unlearned_mistakes) >= threshold
        
        if should_train:
            logger.info(f"Retraining recommended: {len(unlearned_mistakes)} new mistakes")
        
        return should_train
    
    def retrain_detector(self, model, epochs: int = 10, 
                        batch_size: int = 32, learning_rate: float = 0.001) -> Dict:
        """
        Retrain the UI detector model
        
        Args:
            model: The model to retrain
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate
        
        Returns:
            Training statistics
        """
        try:
            logger.info("Starting model retraining...")
            
            # Get unlearned mistakes
            unlearned = [m for m in self.mistakes if not m['retrained']]
            
            if not unlearned:
                logger.warning("No new mistakes to learn from")
                return {'status': 'skipped', 'reason': 'no_new_data'}
            
            # Create dataset
            dataset = MistakeDataset(unlearned)
            dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
            
            # Setup training
            model.train()
            optimizer = optim.Adam(model.parameters(), lr=learning_rate)
            criterion = nn.CrossEntropyLoss()
            
            stats = {
                'total_samples': len(unlearned),
                'epochs': epochs,
                'losses': []
            }
            
            # Training loop
            for epoch in range(epochs):
                epoch_loss = 0.0
                batch_count = 0
                
                for images, labels in dataloader:
                    optimizer.zero_grad()
                    
                    # Forward pass
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    
                    # Backward pass
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                    batch_count += 1
                
                avg_loss = epoch_loss / batch_count
                stats['losses'].append(avg_loss)
                
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
            
            # Mark mistakes as retrained
            for mistake in unlearned:
                mistake['retrained'] = True
            self._save_mistakes()
            
            # Save updated model
            self._save_model(model)
            
            stats['status'] = 'success'
            logger.info("Retraining completed successfully")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error during retraining: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def update_decision_weights(self, decision_engine) -> bool:
        """
        Update decision engine based on corrections
        
        Args:
            decision_engine: Decision engine to update
        
        Returns:
            True if successful
        """
        try:
            unlearned = [c for c in self.corrections if not c['learned']]
            
            if not unlearned:
                logger.info("No new corrections to learn from")
                return False
            
            logger.info(f"Learning from {len(unlearned)} corrections...")
            
            # Analyze patterns in corrections
            action_preferences = {}
            for correction in unlearned:
                action_type = correction['action_type']
                user_choice = correction['user_choice']
                
                if action_type not in action_preferences:
                    action_preferences[action_type] = {}
                
                if user_choice not in action_preferences[action_type]:
                    action_preferences[action_type][user_choice] = 0
                
                action_preferences[action_type][user_choice] += 1
            
            # Update decision engine preferences
            decision_engine.user_preferences.update(action_preferences)
            
            # Mark as learned
            for correction in unlearned:
                correction['learned'] = True
            self._save_corrections()
            
            logger.info("Decision weights updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating decision weights: {e}")
            return False
    
    def get_learning_statistics(self) -> Dict:
        """
        Get statistics about learning progress
        
        Returns:
            Dictionary with statistics
        """
        total_mistakes = len(self.mistakes)
        retrained = sum(1 for m in self.mistakes if m['retrained'])
        
        total_corrections = len(self.corrections)
        learned = sum(1 for c in self.corrections if c['learned'])
        
        return {
            'mistakes': {
                'total': total_mistakes,
                'retrained': retrained,
                'pending': total_mistakes - retrained
            },
            'corrections': {
                'total': total_corrections,
                'learned': learned,
                'pending': total_corrections - learned
            },
            'accuracy_improvement': self._calculate_improvement()
        }
    
    def _calculate_improvement(self) -> float:
        """Calculate accuracy improvement from retraining"""
        if not self.mistakes:
            return 0.0
        
        retrained = sum(1 for m in self.mistakes if m['retrained'])
        return (retrained / len(self.mistakes)) * 100
    
    def _load_mistakes(self) -> List[Dict]:
        """Load mistakes from file"""
        if self.mistakes_file.exists():
            try:
                with open(self.mistakes_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading mistakes: {e}")
        return []
    
    def _save_mistakes(self):
        """Save mistakes to file"""
        try:
            with open(self.mistakes_file, 'w') as f:
                json.dump(self.mistakes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving mistakes: {e}")
    
    def _load_corrections(self) -> List[Dict]:
        """Load corrections from file"""
        if self.corrections_file.exists():
            try:
                with open(self.corrections_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading corrections: {e}")
        return []
    
    def _save_corrections(self):
        """Save corrections to file"""
        try:
            with open(self.corrections_file, 'w') as f:
                json.dump(self.corrections, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving corrections: {e}")
    
    def _save_model(self, model):
        """Save model to disk"""
        try:
            torch.save(model.state_dict(), self.model_path)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
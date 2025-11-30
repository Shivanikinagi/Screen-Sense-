"""
Screen Capture Module
Continuously captures screenshots at specified intervals
"""

import numpy as np
import mss
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


class ScreenCapture:
    """Handles screen capture functionality"""
    
    def __init__(self, monitor_index: int = 1):
        """
        Initialize screen capture
        
        Args:
            monitor_index: Monitor to capture (1 for primary)
        """
        self.sct = mss.mss()
        self.monitor_index = monitor_index
        self.monitor = self.sct.monitors[monitor_index]
        logger.info(f"Screen capture initialized for monitor {monitor_index}")
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture current screen
        
        Returns:
            numpy array of screenshot in RGB format
        """
        try:
            # Capture screenshot
            screenshot = self.sct.grab(self.monitor)
            
            # Convert to numpy array
            img = np.array(screenshot)
            
            # Convert BGRA to RGB
            img = img[:, :, :3]
            
            return img
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None
    
    def capture_region(self, bbox: tuple) -> Optional[np.ndarray]:
        """
        Capture specific region of screen
        
        Args:
            bbox: (x, y, width, height)
        
        Returns:
            numpy array of screenshot region
        """
        try:
            x, y, width, height = bbox
            region = {
                'top': y,
                'left': x,
                'width': width,
                'height': height
            }
            
            screenshot = self.sct.grab(region)
            img = np.array(screenshot)[:, :, :3]
            
            return img
            
        except Exception as e:
            logger.error(f"Error capturing region: {e}")
            return None
    
    def save_screenshot(self, filepath: str) -> bool:
        """
        Capture and save screenshot
        
        Args:
            filepath: Path to save screenshot
        
        Returns:
            True if successful
        """
        try:
            img = self.capture()
            if img is not None:
                Image.fromarray(img).save(filepath)
                logger.debug(f"Screenshot saved to {filepath}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return False
    
    def get_monitor_info(self) -> dict:
        """Get information about current monitor"""
        return {
            'index': self.monitor_index,
            'width': self.monitor['width'],
            'height': self.monitor['height'],
            'top': self.monitor['top'],
            'left': self.monitor['left']
        }
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'sct'):
            self.sct.close()
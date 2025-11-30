"""
Image Preprocessing Module
Prepares images for CNN processing
"""

import cv2
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Handles image preprocessing for ML models"""
    
    def __init__(self, target_size: Tuple[int, int] = (640, 480)):
        """
        Initialize preprocessor
        
        Args:
            target_size: Target size for resized images (width, height)
        """
        self.target_size = target_size
        logger.info(f"Preprocessor initialized with target size {target_size}")
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Full preprocessing pipeline
        
        Args:
            image: Input image as numpy array
        
        Returns:
            Preprocessed image
        """
        try:
            # Resize
            processed = self.resize(image)
            
            # Normalize
            processed = self.normalize(processed)
            
            # Convert to float32 for model
            processed = processed.astype(np.float32)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image
    
    def resize(self, image: np.ndarray) -> np.ndarray:
        """
        Resize image to target size
        
        Args:
            image: Input image
        
        Returns:
            Resized image
        """
        return cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize pixel values to [0, 1]
        
        Args:
            image: Input image
        
        Returns:
            Normalized image
        """
        return image / 255.0
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE
        
        Args:
            image: Input image
        
        Returns:
            Contrast-enhanced image
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            
            # Convert back to RGB
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing contrast: {e}")
            return image
    
    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from image
        
        Args:
            image: Input image
        
        Returns:
            Denoised image
        """
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    
    def prepare_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Prepare image specifically for OCR
        
        Args:
            image: Input image
        
        Returns:
            OCR-ready image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Remove noise
            denoised = cv2.medianBlur(thresh, 3)
            
            return denoised
            
        except Exception as e:
            logger.error(f"Error preparing image for OCR: {e}")
            return image
    
    def extract_roi(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract region of interest
        
        Args:
            image: Input image
            bbox: Bounding box (x1, y1, x2, y2)
        
        Returns:
            Cropped region
        """
        x1, y1, x2, y2 = bbox
        return image[y1:y2, x1:x2]
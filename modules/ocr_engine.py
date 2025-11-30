"""
OCR Engine Module
Extracts text from images using Tesseract and EasyOCR
"""

import pytesseract
import easyocr
import numpy as np
import logging
from typing import List, Dict, Tuple
import cv2

logger = logging.getLogger(__name__)


class OCREngine:
    """Optical Character Recognition engine"""
    
    def __init__(self, use_easyocr: bool = True, languages: List[str] = ['en']):
        """
        Initialize OCR engine
        
        Args:
            use_easyocr: Use EasyOCR (more accurate but slower)
            languages: List of languages to detect
        """
        self.use_easyocr = use_easyocr
        self.languages = languages
        
        # Initialize EasyOCR if requested
        if use_easyocr:
            try:
                self.reader = easyocr.Reader(languages, gpu=True)
                logger.info("EasyOCR initialized with GPU support")
            except Exception as e:
                logger.warning(f"EasyOCR GPU failed, using CPU: {e}")
                self.reader = easyocr.Reader(languages, gpu=False)
        
        logger.info("OCR Engine initialized")
    
    def extract_text(self, image: np.ndarray, bbox: Tuple[int, int, int, int] = None) -> str:
        """
        Extract text from image or region
        
        Args:
            image: Input image
            bbox: Optional bounding box (x1, y1, x2, y2)
        
        Returns:
            Extracted text
        """
        try:
            # Crop to region if specified
            if bbox:
                x1, y1, x2, y2 = bbox
                image = image[y1:y2, x1:x2]
            
            # Preprocess for OCR
            processed = self._preprocess_for_ocr(image)
            
            # Extract text
            if self.use_easyocr:
                text = self._extract_with_easyocr(processed)
            else:
                text = self._extract_with_tesseract(processed)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def extract_text_with_boxes(self, image: np.ndarray) -> List[Dict]:
        """
        Extract text with bounding boxes
        
        Args:
            image: Input image
        
        Returns:
            List of dictionaries with text and bounding boxes
        """
        try:
            processed = self._preprocess_for_ocr(image)
            
            if self.use_easyocr:
                results = self.reader.readtext(processed)
                
                text_boxes = []
                for bbox, text, confidence in results:
                    # Convert bbox to standard format
                    x1 = int(min(point[0] for point in bbox))
                    y1 = int(min(point[1] for point in bbox))
                    x2 = int(max(point[0] for point in bbox))
                    y2 = int(max(point[1] for point in bbox))
                    
                    text_boxes.append({
                        'text': text,
                        'bbox': (x1, y1, x2, y2),
                        'confidence': confidence
                    })
                
                return text_boxes
            else:
                return self._extract_boxes_with_tesseract(processed)
                
        except Exception as e:
            logger.error(f"Error extracting text with boxes: {e}")
            return []
    
    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Resize if image is too small
        height, width = gray.shape
        if height < 50 or width < 50:
            scale = max(50 / height, 50 / width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        return denoised
    
    def _extract_with_easyocr(self, image: np.ndarray) -> str:
        """Extract text using EasyOCR"""
        results = self.reader.readtext(image, detail=0)
        return ' '.join(results)
    
    def _extract_with_tesseract(self, image: np.ndarray) -> str:
        """Extract text using Tesseract"""
        text = pytesseract.image_to_string(
            image, 
            lang='+'.join(self.languages),
            config='--psm 6'
        )
        return text
    
    def _extract_boxes_with_tesseract(self, image: np.ndarray) -> List[Dict]:
        """Extract text boxes using Tesseract"""
        data = pytesseract.image_to_data(
            image, 
            output_type=pytesseract.Output.DICT
        )
        
        text_boxes = []
        for i, text in enumerate(data['text']):
            if text.strip():
                confidence = data['conf'][i]
                if confidence > 0:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    text_boxes.append({
                        'text': text,
                        'bbox': (x, y, x + w, y + h),
                        'confidence': confidence / 100.0
                    })
        
        return text_boxes
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        
        Args:
            text: Input text
        
        Returns:
            Detected language code
        """
        # Simple heuristic - can be improved with langdetect library
        if any(ord(c) > 127 for c in text):
            return "multi"
        return "en"
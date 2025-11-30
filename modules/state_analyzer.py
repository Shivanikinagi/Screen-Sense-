"""
State Analyzer Module
Analyzes screen state and determines screen type
"""

import logging
from typing import List, Dict
from enum import Enum
import re

logger = logging.getLogger(__name__)


class ScreenType(Enum):
    """Types of screens"""
    LOGIN = "login"
    FORM = "form"
    ERROR = "error"
    SCAM = "scam"
    CHECKOUT = "checkout"
    MENU = "menu"
    NORMAL = "normal"
    POPUP = "popup"
    CONFIRMATION = "confirmation"


class StateAnalyzer:
    """Analyzes screen state from UI elements and text"""
    
    def __init__(self):
        """Initialize state analyzer"""
        # Keywords for screen type detection
        self.login_keywords = [
            'login', 'sign in', 'username', 'password', 
            'email', 'log in', 'signin', 'authenticate'
        ]
        
        self.form_keywords = [
            'submit', 'form', 'first name', 'last name',
            'address', 'phone', 'date of birth', 'register'
        ]
        
        self.error_keywords = [
            'error', 'failed', 'invalid', 'incorrect',
            'wrong', 'not found', '404', '500'
        ]
        
        self.scam_keywords = [
            'urgent', 'limited time', 'click now', 'congratulations',
            'you won', 'free gift', 'act now', 'verify account',
            'suspended', 'unusual activity', 'confirm identity',
            'claim prize', 'winner', 'exclusive offer'
        ]
        
        self.checkout_keywords = [
            'checkout', 'cart', 'payment', 'total', 'order',
            'shipping', 'billing', 'purchase', 'buy now', 'pay'
        ]
        
        logger.info("State Analyzer initialized")
    
    def analyze(self, ui_elements: List[dict], extracted_text: Dict[str, str]) -> ScreenType:
        """
        Analyze screen state
        
        Args:
            ui_elements: List of detected UI elements
            extracted_text: Dictionary of extracted text
        
        Returns:
            Detected screen type
        """
        try:
            # Combine all text for analysis
            all_text = ' '.join(extracted_text.values()).lower()
            
            # Check for popup first
            if self._has_popup(ui_elements):
                return ScreenType.POPUP
            
            # Check for scam/phishing
            if self._is_scam(all_text):
                logger.warning("Potential scam detected!")
                return ScreenType.SCAM
            
            # Check for error
            if self._is_error(all_text):
                return ScreenType.ERROR
            
            # Check for login
            if self._is_login(all_text, ui_elements):
                return ScreenType.LOGIN
            
            # Check for checkout
            if self._is_checkout(all_text):
                return ScreenType.CHECKOUT
            
            # Check for form
            if self._is_form(all_text, ui_elements):
                return ScreenType.FORM
            
            # Check for menu
            if self._is_menu(ui_elements):
                return ScreenType.MENU
            
            return ScreenType.NORMAL
            
        except Exception as e:
            logger.error(f"Error analyzing state: {e}")
            return ScreenType.NORMAL
    
    def _has_popup(self, elements: List[dict]) -> bool:
        """Check if there's a popup"""
        return any(elem['label'] == 'popup' for elem in elements)
    
    def _is_scam(self, text: str) -> bool:
        """Detect potential scam/phishing"""
        scam_score = sum(1 for keyword in self.scam_keywords if keyword in text)
        
        # Check for urgency + suspicious patterns
        has_urgency = any(word in text for word in ['urgent', 'immediately', 'now', 'limited'])
        has_action = any(word in text for word in ['click', 'verify', 'confirm', 'update'])
        
        return scam_score >= 2 or (has_urgency and has_action)
    
    def _is_error(self, text: str) -> bool:
        """Detect error screen"""
        return any(keyword in text for keyword in self.error_keywords)
    
    def _is_login(self, text: str, elements: List[dict]) -> bool:
        """Detect login screen"""
        has_login_text = any(keyword in text for keyword in self.login_keywords)
        has_input_fields = sum(1 for elem in elements if elem['label'] == 'input') >= 2
        has_button = any(elem['label'] == 'button' for elem in elements)
        
        return has_login_text and has_input_fields and has_button
    
    def _is_checkout(self, text: str) -> bool:
        """Detect checkout screen"""
        checkout_score = sum(1 for keyword in self.checkout_keywords if keyword in text)
        return checkout_score >= 2
    
    def _is_form(self, text: str, elements: List[dict]) -> bool:
        """Detect form screen"""
        has_form_text = any(keyword in text for keyword in self.form_keywords)
        input_count = sum(1 for elem in elements if elem['label'] == 'input')
        
        return has_form_text or input_count >= 3
    
    def _is_menu(self, elements: List[dict]) -> bool:
        """Detect menu screen"""
        link_count = sum(1 for elem in elements if elem['label'] == 'link')
        button_count = sum(1 for elem in elements if elem['label'] == 'button')
        
        return (link_count + button_count) >= 5
    
    def extract_form_fields(self, ui_elements: List[dict], text_boxes: List[Dict]) -> Dict[str, str]:
        """
        Extract form field information
        
        Args:
            ui_elements: Detected UI elements
            text_boxes: Text boxes with locations
        
        Returns:
            Dictionary mapping field names to types
        """
        form_fields = {}
        
        for text_box in text_boxes:
            text = text_box['text'].lower()
            
            # Detect field type from label
            if any(keyword in text for keyword in ['email', 'e-mail']):
                form_fields[text] = 'email'
            elif any(keyword in text for keyword in ['password', 'pwd']):
                form_fields[text] = 'password'
            elif any(keyword in text for keyword in ['name', 'username']):
                form_fields[text] = 'name'
            elif any(keyword in text for keyword in ['phone', 'mobile']):
                form_fields[text] = 'phone'
            elif any(keyword in text for keyword in ['address']):
                form_fields[text] = 'address'
        
        return form_fields
    
    def calculate_risk_score(self, screen_type: ScreenType, text: str) -> float:
        """
        Calculate risk score for current screen
        
        Args:
            screen_type: Detected screen type
            text: All text on screen
        
        Returns:
            Risk score from 0.0 (safe) to 1.0 (dangerous)
        """
        risk = 0.0
        
        # Base risk by screen type
        risk_map = {
            ScreenType.SCAM: 0.9,
            ScreenType.ERROR: 0.3,
            ScreenType.POPUP: 0.4,
            ScreenType.LOGIN: 0.2,
            ScreenType.CHECKOUT: 0.3,
            ScreenType.NORMAL: 0.0
        }
        
        risk = risk_map.get(screen_type, 0.0)
        
        # Increase risk for suspicious patterns
        text_lower = text.lower()
        if any(word in text_lower for word in ['download', 'install', 'exe']):
            risk += 0.2
        
        if re.search(r'http://[^\s]+', text):  # Non-HTTPS links
            risk += 0.1
        
        return min(risk, 1.0)
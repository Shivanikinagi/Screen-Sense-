"""
Decision Engine Module
Determines the best action based on screen state
"""

import logging
from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions"""
    AUTOFILL = "autofill"
    CLICK = "click"
    CLOSE_POPUP = "close_popup"
    BLOCK_CONTENT = "block_content"
    HIGHLIGHT = "highlight"
    DO_NOTHING = "do_nothing"
    ASK_USER = "ask_user"
    NAVIGATE_BACK = "navigate_back"


@dataclass
class Decision:
    """Action decision with reasoning"""
    action: ActionType
    target_element: Optional[Dict]
    reasoning: str
    confidence: float
    requires_confirmation: bool
    data: Optional[Dict] = None
    alternatives: Optional[List['Decision']] = None


class DecisionEngine:
    """Makes intelligent decisions based on screen state"""
    
    def __init__(self):
        """Initialize decision engine"""
        self.decision_history = []
        self.user_preferences = {}
        
        logger.info("Decision Engine initialized")
    
    def decide(self, screen_type: str, ui_elements: List[Dict], 
               extracted_text: Dict, risk_score: float) -> Decision:
        """
        Make action decision
        
        Args:
            screen_type: Type of screen detected
            ui_elements: List of UI elements
            extracted_text: Extracted text from screen
            risk_score: Risk score (0.0 to 1.0)
        
        Returns:
            Decision object with action and reasoning
        """
        try:
            # High risk - block or warn
            if risk_score > 0.7:
                return self._decide_high_risk(screen_type, ui_elements)
            
            # Handle specific screen types
            if screen_type == "scam":
                return self._decide_scam(ui_elements)
            elif screen_type == "popup":
                return self._decide_popup(ui_elements)
            elif screen_type == "login":
                return self._decide_login(ui_elements)
            elif screen_type == "form":
                return self._decide_form(ui_elements)
            elif screen_type == "error":
                return self._decide_error(ui_elements)
            elif screen_type == "checkout":
                return self._decide_checkout(ui_elements)
            else:
                return self._decide_normal(ui_elements)
                
        except Exception as e:
            logger.error(f"Error making decision: {e}")
            return Decision(
                action=ActionType.DO_NOTHING,
                target_element=None,
                reasoning=f"Error: {str(e)}",
                confidence=0.0,
                requires_confirmation=False
            )
    
    def _decide_high_risk(self, screen_type: str, elements: List[Dict]) -> Decision:
        """Handle high-risk situations"""
        return Decision(
            action=ActionType.BLOCK_CONTENT,
            target_element=None,
            reasoning="High risk detected - blocking content for safety",
            confidence=0.9,
            requires_confirmation=False,
            data={'risk_level': 'high', 'screen_type': screen_type}
        )
    
    def _decide_scam(self, elements: List[Dict]) -> Decision:
        """Handle scam/phishing screens"""
        return Decision(
            action=ActionType.NAVIGATE_BACK,
            target_element=None,
            reasoning="Potential scam detected - suggesting navigation back",
            confidence=0.85,
            requires_confirmation=True,
            data={'warning': 'This page may be attempting to steal your information'}
        )
    
    def _decide_popup(self, elements: List[Dict]) -> Decision:
        """Handle popup screens"""
        # Find close button
        close_button = self._find_element(elements, 'button', ['close', 'x', 'dismiss'])
        
        if close_button:
            return Decision(
                action=ActionType.CLOSE_POPUP,
                target_element=close_button,
                reasoning="Found close button for popup",
                confidence=0.8,
                requires_confirmation=False
            )
        
        return Decision(
            action=ActionType.HIGHLIGHT,
            target_element=None,
            reasoning="Popup detected but no close button found",
            confidence=0.6,
            requires_confirmation=False
        )
    
    def _decide_login(self, elements: List[Dict]) -> Decision:
        """Handle login screens"""
        # Check if we have saved credentials
        input_fields = [e for e in elements if e['label'] == 'input']
        
        if len(input_fields) >= 2:
            return Decision(
                action=ActionType.ASK_USER,
                target_element=None,
                reasoning="Login form detected - autofill available",
                confidence=0.75,
                requires_confirmation=True,
                data={'action': 'autofill', 'field_count': len(input_fields)}
            )
        
        return Decision(
            action=ActionType.DO_NOTHING,
            target_element=None,
            reasoning="Login form detected but insufficient fields",
            confidence=0.5,
            requires_confirmation=False
        )
    
    def _decide_form(self, elements: List[Dict]) -> Decision:
        """Handle form screens"""
        input_fields = [e for e in elements if e['label'] == 'input']
        
        if len(input_fields) >= 3:
            return Decision(
                action=ActionType.HIGHLIGHT,
                target_element=None,
                reasoning="Complex form detected - highlighting required fields",
                confidence=0.7,
                requires_confirmation=False,
                data={'field_count': len(input_fields)}
            )
        
        return Decision(
            action=ActionType.DO_NOTHING,
            target_element=None,
            reasoning="Simple form - no action needed",
            confidence=0.8,
            requires_confirmation=False
        )
    
    def _decide_error(self, elements: List[Dict]) -> Decision:
        """Handle error screens"""
        # Look for retry or back button
        retry_button = self._find_element(elements, 'button', ['retry', 'try again', 'back'])
        
        if retry_button:
            return Decision(
                action=ActionType.HIGHLIGHT,
                target_element=retry_button,
                reasoning="Error detected - highlighting retry option",
                confidence=0.75,
                requires_confirmation=False
            )
        
        return Decision(
            action=ActionType.DO_NOTHING,
            target_element=None,
            reasoning="Error detected - manual intervention needed",
            confidence=0.6,
            requires_confirmation=False
        )
    
    def _decide_checkout(self, elements: List[Dict]) -> Decision:
        """Handle checkout screens"""
        return Decision(
            action=ActionType.HIGHLIGHT,
            target_element=None,
            reasoning="Checkout detected - highlighting important elements",
            confidence=0.8,
            requires_confirmation=False,
            data={'suggestion': 'Review payment details carefully'}
        )
    
    def _decide_normal(self, elements: List[Dict]) -> Decision:
        """Handle normal screens"""
        # Check for annoying ads
        ads = [e for e in elements if e['label'] == 'ad']
        
        if len(ads) > 3:
            return Decision(
                action=ActionType.BLOCK_CONTENT,
                target_element=None,
                reasoning="Multiple ads detected - suggesting ad block",
                confidence=0.7,
                requires_confirmation=True,
                data={'ad_count': len(ads)}
            )
        
        return Decision(
            action=ActionType.DO_NOTHING,
            target_element=None,
            reasoning="Normal screen - no action needed",
            confidence=0.9,
            requires_confirmation=False
        )
    
    def _find_element(self, elements: List[Dict], label: str, 
                      keywords: List[str]) -> Optional[Dict]:
        """Find element by label and text keywords"""
        for element in elements:
            if element['label'] == label:
                text = element.get('text', '').lower()
                if any(keyword in text for keyword in keywords):
                    return element
        return None
    
    def record_decision(self, decision: Decision, success: bool, 
                       user_override: bool = False):
        """
        Record decision outcome for learning
        
        Args:
            decision: The decision that was made
            success: Whether the decision was successful
            user_override: Whether user overrode the decision
        """
        self.decision_history.append({
            'decision': decision,
            'success': success,
            'user_override': user_override,
            'timestamp': __import__('time').time()
        })
        
        if user_override:
            logger.info(f"User overrode decision: {decision.action}")
    
    def get_success_rate(self, action_type: ActionType) -> float:
        """Calculate success rate for specific action type"""
        relevant = [d for d in self.decision_history 
                   if d['decision'].action == action_type]
        
        if not relevant:
            return 0.0
        
        successful = sum(1 for d in relevant if d['success'])
        return successful / len(relevant)
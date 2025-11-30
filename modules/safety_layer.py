"""
Safety Layer Module
Ensures safe execution with user confirmation and explanations
"""

import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SafetyCheck:
    """Result of safety check"""
    safe: bool
    reasoning: str
    requires_confirmation: bool
    risk_level: str  # 'low', 'medium', 'high'


class SafetyLayer:
    """Safety checks and user confirmation"""
    
    def __init__(self, auto_confirm_low_risk: bool = True):
        """
        Initialize safety layer
        
        Args:
            auto_confirm_low_risk: Auto-confirm low risk actions
        """
        self.auto_confirm_low_risk = auto_confirm_low_risk
        self.confirmation_history = []
        
        logger.info("Safety Layer initialized")
    
    def check_action_safety(self, action_type: str, target_element: Optional[dict],
                           screen_type: str, risk_score: float) -> SafetyCheck:
        """
        Check if action is safe to execute
        
        Args:
            action_type: Type of action
            target_element: Target element for action
            screen_type: Type of current screen
            risk_score: Risk score (0.0 to 1.0)
        
        Returns:
            SafetyCheck result
        """
        try:
            # High risk screens
            if screen_type == "scam" or risk_score > 0.8:
                return SafetyCheck(
                    safe=False,
                    reasoning="High-risk screen detected",
                    requires_confirmation=True,
                    risk_level='high'
                )
            
            # Determine risk level
            if action_type in ['autofill', 'close_popup']:
                if risk_score < 0.3:
                    risk_level = 'low'
                    requires_conf = False
                elif risk_score < 0.6:
                    risk_level = 'medium'
                    requires_conf = True
                else:
                    risk_level = 'high'
                    requires_conf = True
            elif action_type in ['click', 'navigate_back']:
                risk_level = 'medium' if risk_score > 0.4 else 'low'
                requires_conf = risk_score > 0.4
            elif action_type == 'block_content':
                risk_level = 'low'
                requires_conf = False
            else:
                risk_level = 'low'
                requires_conf = False
            
            return SafetyCheck(
                safe=True,
                reasoning=f"Action assessed as {risk_level} risk",
                requires_confirmation=requires_conf and not (
                    self.auto_confirm_low_risk and risk_level == 'low'
                ),
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            return SafetyCheck(
                safe=False,
                reasoning=f"Error: {str(e)}",
                requires_confirmation=True,
                risk_level='high'
            )
    
    def ask_confirmation(self, action_type: str, reasoning: str,
                        risk_level: str, show_why: bool = True) -> bool:
        """
        Ask user for confirmation
        
        Args:
            action_type: Type of action
            reasoning: Explanation for action
            risk_level: Risk level of action
            show_why: Show detailed reasoning
        
        Returns:
            True if user confirms
        """
        try:
            # Build confirmation message
            message = f"ScreenSense AI wants to perform: {action_type}\n\n"
            
            if show_why:
                message += f"Reason: {reasoning}\n"
                message += f"Risk Level: {risk_level.upper()}\n\n"
            
            message += "Do you want to proceed?"
            
            # Show confirmation dialog
            root = tk.Tk()
            root.withdraw()
            
            result = messagebox.askyesno(
                "ScreenSense AI - Confirmation Required",
                message,
                icon='warning' if risk_level == 'high' else 'question'
            )
            
            root.destroy()
            
            # Record decision
            self.confirmation_history.append({
                'action': action_type,
                'confirmed': result,
                'risk_level': risk_level,
                'timestamp': __import__('time').time()
            })
            
            logger.info(f"User {'confirmed' if result else 'rejected'} {action_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error showing confirmation: {e}")
            return False
    
    def show_explanation(self, action_type: str, reasoning: str,
                        alternatives: list = None):
        """
        Show explanation of decision
        
        Args:
            action_type: Type of action
            reasoning: Explanation
            alternatives: List of alternative actions
        """
        try:
            message = f"ScreenSense AI Decision:\n\n"
            message += f"Action: {action_type}\n"
            message += f"Why: {reasoning}\n"
            
            if alternatives:
                message += f"\nAlternatives:\n"
                for alt in alternatives[:3]:
                    message += f"  • {alt}\n"
            
            root = tk.Tk()
            root.withdraw()
            
            messagebox.showinfo(
                "ScreenSense AI - Explanation",
                message
            )
            
            root.destroy()
            
        except Exception as e:
            logger.error(f"Error showing explanation: {e}")
    
    def show_warning(self, warning_type: str, details: str):
        """
        Show warning to user
        
        Args:
            warning_type: Type of warning
            details: Warning details
        """
        try:
            message = f"⚠️ {warning_type}\n\n{details}"
            
            root = tk.Tk()
            root.withdraw()
            
            messagebox.showwarning(
                "ScreenSense AI - Warning",
                message
            )
            
            root.destroy()
            
            logger.warning(f"Showed warning: {warning_type}")
            
        except Exception as e:
            logger.error(f"Error showing warning: {e}")
    
    def get_user_feedback(self, action_type: str, success: bool) -> Optional[str]:
        """
        Get user feedback on action
        
        Args:
            action_type: Type of action performed
            success: Whether action was successful
        
        Returns:
            User feedback text or None
        """
        try:
            message = f"Action performed: {action_type}\n"
            message += f"Result: {'Success' if success else 'Failed'}\n\n"
            message += "Was this action helpful?\n"
            message += "Click Yes if it was helpful, No if it wasn't."
            
            root = tk.Tk()
            root.withdraw()
            
            result = messagebox.askyesnocancel(
                "ScreenSense AI - Feedback",
                message
            )
            
            root.destroy()
            
            if result is None:
                return None
            
            return "helpful" if result else "not helpful"
            
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return None
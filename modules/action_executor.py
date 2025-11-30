"""
Action Executor Module
Executes actions using browser automation
"""

import time
import logging
import pyautogui
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Page, Browser

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes actions on screen"""
    
    def __init__(self, use_playwright: bool = True, action_delay: float = 0.5):
        """
        Initialize action executor
        
        Args:
            use_playwright: Use Playwright (True) or pyautogui (False)
            action_delay: Delay between actions in seconds
        """
        self.use_playwright = use_playwright
        self.action_delay = action_delay
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Configure pyautogui
        pyautogui.PAUSE = action_delay
        pyautogui.FAILSAFE = True
        
        logger.info(f"Action Executor initialized (playwright={use_playwright})")
    
    def initialize_browser(self, headless: bool = False):
        """Initialize Playwright browser"""
        if self.use_playwright:
            try:
                playwright = sync_playwright().start()
                self.browser = playwright.chromium.launch(headless=headless)
                self.page = self.browser.new_page()
                logger.info("Playwright browser initialized")
            except Exception as e:
                logger.error(f"Failed to initialize browser: {e}")
    
    def execute_click(self, bbox: Tuple[int, int, int, int], 
                     element_label: str = "") -> bool:
        """
        Execute click action
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            element_label: Label of element being clicked
        
        Returns:
            True if successful
        """
        try:
            # Calculate center of bounding box
            x1, y1, x2, y2 = bbox
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            logger.info(f"Clicking {element_label} at ({center_x}, {center_y})")
            
            if self.use_playwright and self.page:
                # Use Playwright if browser is active
                self.page.mouse.click(center_x, center_y)
            else:
                # Use pyautogui
                pyautogui.click(center_x, center_y)
            
            time.sleep(self.action_delay)
            return True
            
        except Exception as e:
            logger.error(f"Error executing click: {e}")
            return False
    
    def execute_type(self, text: str, bbox: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        Execute typing action
        
        Args:
            text: Text to type
            bbox: Optional bounding box to click before typing
        
        Returns:
            True if successful
        """
        try:
            # Click field if bbox provided
            if bbox:
                self.execute_click(bbox, "input field")
            
            logger.info(f"Typing text: {text[:20]}...")
            
            if self.use_playwright and self.page:
                self.page.keyboard.type(text)
            else:
                pyautogui.write(text, interval=0.05)
            
            time.sleep(self.action_delay)
            return True
            
        except Exception as e:
            logger.error(f"Error executing type: {e}")
            return False
    
    def execute_autofill(self, form_data: dict, field_positions: dict) -> bool:
        """
        Execute autofill action
        
        Args:
            form_data: Dictionary of field names and values
            field_positions: Dictionary of field names and bounding boxes
        
        Returns:
            True if successful
        """
        try:
            logger.info("Executing autofill...")
            
            for field_name, value in form_data.items():
                if field_name in field_positions:
                    bbox = field_positions[field_name]
                    
                    # Click field
                    self.execute_click(bbox, field_name)
                    
                    # Type value
                    self.execute_type(value)
                    
                    logger.info(f"Filled {field_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing autofill: {e}")
            return False
    
    def execute_close_popup(self, close_button_bbox: Tuple[int, int, int, int]) -> bool:
        """
        Execute close popup action
        
        Args:
            close_button_bbox: Bounding box of close button
        
        Returns:
            True if successful
        """
        return self.execute_click(close_button_bbox, "popup close button")
    
    def execute_scroll(self, direction: str = "down", amount: int = 3) -> bool:
        """
        Execute scroll action
        
        Args:
            direction: "up" or "down"
            amount: Number of scroll units
        
        Returns:
            True if successful
        """
        try:
            scroll_amount = amount if direction == "down" else -amount
            
            logger.info(f"Scrolling {direction} by {amount}")
            
            if self.use_playwright and self.page:
                self.page.mouse.wheel(0, scroll_amount * 100)
            else:
                pyautogui.scroll(scroll_amount * 100)
            
            time.sleep(self.action_delay)
            return True
            
        except Exception as e:
            logger.error(f"Error executing scroll: {e}")
            return False
    
    def execute_navigate_back(self) -> bool:
        """
        Navigate back in browser
        
        Returns:
            True if successful
        """
        try:
            logger.info("Navigating back")
            
            if self.use_playwright and self.page:
                self.page.go_back()
            else:
                pyautogui.hotkey('alt', 'left')
            
            time.sleep(self.action_delay)
            return True
            
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            return False
    
    def execute_highlight(self, bboxes: list) -> bool:
        """
        Highlight elements on screen
        
        Args:
            bboxes: List of bounding boxes to highlight
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Highlighting {len(bboxes)} elements")
            # This would typically draw overlays on screen
            # Implementation depends on UI framework
            return True
            
        except Exception as e:
            logger.error(f"Error highlighting elements: {e}")
            return False
    
    def undo_last_action(self) -> bool:
        """
        Undo the last action
        
        Returns:
            True if successful
        """
        try:
            logger.info("Undoing last action")
            
            if self.use_playwright and self.page:
                self.page.go_back()
            else:
                pyautogui.hotkey('ctrl', 'z')
            
            return True
            
        except Exception as e:
            logger.error(f"Error undoing action: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            self.browser.close()
            logger.info("Browser closed")
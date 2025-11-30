"""
ScreenSense AI - Main Pipeline
Automated screen monitoring and intelligent action system
"""

import time
import logging
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path

# Import modules
from modules.screen_capture import ScreenCapture
from modules.preprocessor import ImagePreprocessor
from modules.ui_detector import UIDetector
from modules.ocr_engine import OCREngine
from modules.state_analyzer import StateAnalyzer, ScreenType
from modules.decision_engine import DecisionEngine, ActionType, Decision
from modules.action_executor import ActionExecutor
from modules.safety_layer import SafetyLayer
from modules.learning_loop import LearningLoop
from modules.database_logger import DatabaseLogger
import config

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / 'screensense.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class UIElement:
    """Detected UI element with bounding box and metadata"""
    label: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    text: Optional[str] = None


@dataclass
class ScreenState:
    """Current state of the screen"""
    screen_type: ScreenType
    elements: List[UIElement]
    extracted_text: Dict[str, str]
    timestamp: float
    past_actions: List[str]


class ScreenSenseAI:
    """Main ScreenSense AI Pipeline"""
    
    def __init__(self, capture_interval: float = None, detection_threshold: float = None):
        """
        Initialize ScreenSense AI
        
        Args:
            capture_interval: Time between screenshots in seconds (default from config)
            detection_threshold: Confidence threshold for UI detection (default from config)
        """
        self.capture_interval = capture_interval or config.CAPTURE_INTERVAL
        self.detection_threshold = detection_threshold or config.CONFIDENCE_THRESHOLD
        self.running = False
        self.current_state: Optional[ScreenState] = None
        self.action_history: List[Dict] = []
        
        logger.info("Initializing ScreenSense AI components...")
        
        try:
            # Initialize components
            self.screen_capture = ScreenCapture(monitor_index=1)
            logger.info("[OK] Screen capture initialized")
            
            self.preprocessor = ImagePreprocessor(target_size=config.TARGET_IMAGE_SIZE)
            logger.info("[OK] Preprocessor initialized")
            
            self.ui_detector = UIDetector(
                model_path=str(config.MODEL_PATH),
                num_classes=len(config.UI_CLASSES) + 1
            )
            logger.info("[OK] UI detector initialized")
            
            self.ocr_engine = OCREngine(
                use_easyocr=True,
                languages=['en']
            )
            logger.info("[OK] OCR engine initialized")
            
            self.state_analyzer = StateAnalyzer()
            logger.info("[OK] State analyzer initialized")
            
            self.decision_engine = DecisionEngine()
            logger.info("[OK] Decision engine initialized")
            
            self.action_executor = ActionExecutor(
                use_playwright=False,
                action_delay=config.ACTION_DELAY
            )
            logger.info("[OK] Action executor initialized")
            
            self.safety_layer = SafetyLayer(auto_confirm_low_risk=True)
            logger.info("[OK] Safety layer initialized")
            
            self.learning_loop = LearningLoop(
                model_path=str(config.MODEL_PATH),
                data_dir=str(config.DATA_DIR)
            )
            logger.info("[OK] Learning loop initialized")
            
            self.database_logger = DatabaseLogger(
                db_path=str(config.DATA_DIR / "screensense.db")
            )
            logger.info("[OK] Database logger initialized")
            
            logger.info("="*60)
            logger.info("ScreenSense AI fully initialized and ready!")
            logger.info(f"Capture interval: {self.capture_interval}s")
            logger.info(f"Detection threshold: {self.detection_threshold}")
            logger.info("")
            logger.info("NOTE: If detecting 0 elements, the pre-trained model")
            logger.info("needs fine-tuning on UI elements. Run 'python test_detection.py'")
            logger.info("to collect training data and test detection.")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            raise
    
    def start(self):
        """Start the main monitoring loop"""
        self.running = True
        logger.info("="*60)
        logger.info("Starting ScreenSense AI monitoring...")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*60)
        
        frame_count = 0
        total_elements_detected = 0
        
        try:
            while self.running:
                frame_count += 1
                logger.debug(f"Processing frame #{frame_count}")
                
                elements_count = self._process_frame()
                total_elements_detected += elements_count
                
                time.sleep(self.capture_interval)
                
        except KeyboardInterrupt:
            logger.info("\nStopping ScreenSense AI (user interrupt)...")
            logger.info(f"Processed {frame_count} frames")
            logger.info(f"Average elements per frame: {total_elements_detected/frame_count:.1f}")
            self.stop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            self.stop()
    
    def stop(self):
        """Stop the monitoring loop"""
        self.running = False
        
        # Cleanup
        if hasattr(self, 'action_executor'):
            self.action_executor.cleanup()
        
        if hasattr(self, 'database_logger'):
            self.database_logger.close()
        
        # Print statistics
        if hasattr(self, 'database_logger'):
            stats = self.database_logger.get_statistics()
            logger.info("="*60)
            logger.info("Session Statistics:")
            logger.info(f"  Total detections: {stats.get('total_detections', 0)}")
            logger.info(f"  Total decisions: {stats.get('total_decisions', 0)}")
            logger.info(f"  Success rate: {stats.get('success_rate', 0):.1f}%")
            logger.info(f"  Total mistakes: {stats.get('total_mistakes', 0)}")
            logger.info("="*60)
        
        logger.info("ScreenSense AI stopped")
    
    def _process_frame(self) -> int:
        """
        Process a single frame through the entire pipeline
        
        Returns:
            Number of UI elements detected
        """
        try:
            start_time = time.time()
            
            # Step 1: Capture screen
            screenshot = self._capture_screen()
            if screenshot is None:
                logger.warning("Failed to capture screen, skipping frame")
                return 0
            
            # Step 2: Preprocess
            processed_image = self._preprocess(screenshot)
            
            # Step 3: Detect UI elements
            ui_elements = self._detect_ui_elements(processed_image)
            
            # Step 4: Extract text with OCR (only if elements detected)
            extracted_text = {}
            if len(ui_elements) > 0:
                extracted_text = self._extract_text(screenshot, ui_elements)
            
            # Step 5: Understand page state
            screen_state = self._analyze_state(ui_elements, extracted_text)
            self.current_state = screen_state
            
            # Log detection
            detection_id = self.database_logger.log_detection(
                screen_type=screen_state.screen_type.value,
                ui_elements=[vars(elem) for elem in ui_elements],
                extracted_text=extracted_text,
                confidence=0.8,
                screenshot_path=None
            )
            
            # Step 6: Make decision
            decision = self._make_decision(screen_state)
            
            # Log decision
            decision_id = self.database_logger.log_decision(
                detection_id=detection_id,
                action_type=decision.action.value,
                reasoning=decision.reasoning,
                confidence=decision.confidence,
                requires_confirmation=decision.requires_confirmation
            )
            
            # Step 7: Execute action (with safety checks)
            if decision.action != ActionType.DO_NOTHING:
                execution_success = self._execute_action(decision, decision_id)
            else:
                execution_success = True
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(f"Frame processed in {processing_time:.3f}s - "
                       f"Type: {screen_state.screen_type.value}, "
                       f"Elements: {len(ui_elements)}, "
                       f"Action: {decision.action.value}")
            
            return len(ui_elements)
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
            return 0
    
    def _capture_screen(self):
        """Capture current screen"""
        try:
            screenshot = self.screen_capture.capture()
            logger.debug("Screen captured successfully")
            return screenshot
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None
    
    def _preprocess(self, image):
        """Preprocess image for CNN"""
        try:
            processed = self.preprocessor.preprocess(image)
            logger.debug("Image preprocessed")
            return processed
        except Exception as e:
            logger.error(f"Error preprocessing: {e}")
            return image
    
    def _detect_ui_elements(self, image) -> List[UIElement]:
        """Detect UI elements using CNN"""
        try:
            detections = self.ui_detector.detect(
                image,
                confidence_threshold=self.detection_threshold
            )
            
            # Convert to UIElement objects
            ui_elements = []
            for det in detections:
                ui_elements.append(UIElement(
                    label=det['label'],
                    bbox=det['bbox'],
                    confidence=det['confidence'],
                    text=None
                ))
            
            if len(ui_elements) > 0:
                logger.debug(f"Detected {len(ui_elements)} UI elements:")
                for elem in ui_elements:
                    logger.debug(f"  - {elem.label} (conf: {elem.confidence:.2f})")
            else:
                logger.debug("No UI elements detected (model may need fine-tuning)")
            
            return ui_elements
            
        except Exception as e:
            logger.error(f"Error detecting UI elements: {e}")
            return []
    
    def _extract_text(self, image, elements: List[UIElement]) -> Dict[str, str]:
        """Extract text from detected regions"""
        try:
            extracted_text = {}
            
            # Extract text from each element
            for i, element in enumerate(elements):
                if element.label in ['button', 'input', 'text', 'link']:
                    text = self.ocr_engine.extract_text(image, element.bbox)
                    if text:
                        extracted_text[f"{element.label}_{i}"] = text
                        element.text = text
            
            logger.debug(f"Extracted text from {len(extracted_text)} elements")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return {}
    
    def _analyze_state(self, elements: List[UIElement], text: Dict[str, str]) -> ScreenState:
        """Analyze screen state"""
        try:
            # Convert UIElement to dict for analyzer
            element_dicts = [vars(elem) for elem in elements]
            
            screen_type = self.state_analyzer.analyze(element_dicts, text)
            
            state = ScreenState(
                screen_type=screen_type,
                elements=elements,
                extracted_text=text,
                timestamp=time.time(),
                past_actions=[]
            )
            
            logger.debug(f"Screen type: {screen_type.value}")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing state: {e}")
            return ScreenState(
                screen_type=ScreenType.NORMAL,
                elements=elements,
                extracted_text=text,
                timestamp=time.time(),
                past_actions=[]
            )
    
    def _make_decision(self, state: ScreenState) -> Decision:
        """Make action decision based on state"""
        try:
            # Convert UIElement to dict for decision engine
            element_dicts = [vars(elem) for elem in state.elements]
            
            # Calculate risk score
            all_text = ' '.join(state.extracted_text.values())
            risk_score = self.state_analyzer.calculate_risk_score(
                state.screen_type,
                all_text
            )
            
            decision = self.decision_engine.decide(
                screen_type=state.screen_type.value,
                ui_elements=element_dicts,
                extracted_text=state.extracted_text,
                risk_score=risk_score
            )
            
            logger.debug(f"Decision: {decision.action.value} (confidence: {decision.confidence:.2f})")
            return decision
            
        except Exception as e:
            logger.error(f"Error making decision: {e}")
            return Decision(
                action=ActionType.DO_NOTHING,
                target_element=None,
                reasoning=f"Error: {str(e)}",
                confidence=0.0,
                requires_confirmation=False
            )
    
    def _execute_action(self, decision: Decision, decision_id: int) -> bool:
        """Execute the decided action"""
        start_time = time.time()
        
        try:
            # Step 8: Safety layer
            safety_check = self.safety_layer.check_action_safety(
                action_type=decision.action.value,
                target_element=decision.target_element,
                screen_type=self.current_state.screen_type.value,
                risk_score=0.5
            )
            
            if not safety_check.safe:
                logger.warning(f"Action blocked by safety layer: {safety_check.reasoning}")
                self.database_logger.log_action(
                    decision_id=decision_id,
                    action_type=decision.action.value,
                    success=False,
                    execution_time=0,
                    error_message="Blocked by safety layer"
                )
                return False
            
            if safety_check.requires_confirmation:
                confirmed = self.safety_layer.ask_confirmation(
                    action_type=decision.action.value,
                    reasoning=decision.reasoning,
                    risk_level=safety_check.risk_level
                )
                
                if not confirmed:
                    logger.info("Action cancelled by user")
                    self.database_logger.log_action(
                        decision_id=decision_id,
                        action_type=decision.action.value,
                        success=False,
                        execution_time=0,
                        error_message="Cancelled by user"
                    )
                    return False
            
            # Execute action
            success = False
            error_msg = None
            
            if decision.action == ActionType.CLICK and decision.target_element:
                success = self.action_executor.execute_click(
                    bbox=decision.target_element['bbox'],
                    element_label=decision.target_element['label']
                )
            elif decision.action == ActionType.CLOSE_POPUP and decision.target_element:
                success = self.action_executor.execute_close_popup(
                    close_button_bbox=decision.target_element['bbox']
                )
            elif decision.action == ActionType.NAVIGATE_BACK:
                success = self.action_executor.execute_navigate_back()
            elif decision.action == ActionType.HIGHLIGHT:
                bboxes = [e.bbox for e in self.current_state.elements]
                success = self.action_executor.execute_highlight(bboxes)
            else:
                success = True
            
            # Log action
            execution_time = time.time() - start_time
            self.database_logger.log_action(
                decision_id=decision_id,
                action_type=decision.action.value,
                success=success,
                execution_time=execution_time,
                error_message=error_msg
            )
            
            # Record decision outcome
            self.decision_engine.record_decision(decision, success, False)
            
            # Add to history
            self.action_history.append({
                'timestamp': time.time(),
                'action': decision.action.value,
                'reasoning': decision.reasoning,
                'confidence': decision.confidence,
                'success': success
            })
            
            logger.info(f"Action executed: {decision.action.value} ({'success' if success else 'failed'})")
            return success
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            execution_time = time.time() - start_time
            self.database_logger.log_action(
                decision_id=decision_id,
                action_type=decision.action.value,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            return False
    
    def retrain_model(self):
        """Retrain CNN based on logged mistakes"""
        try:
            if self.learning_loop.should_retrain():
                logger.info("Starting model retraining...")
                stats = self.learning_loop.retrain_detector(
                    model=self.ui_detector.model,
                    epochs=config.EPOCHS,
                    learning_rate=config.LEARNING_RATE
                )
                logger.info(f"Retraining completed: {stats}")
                return stats
            else:
                logger.info("Not enough mistakes for retraining yet")
                return None
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ScreenSense AI')
    parser.add_argument('--interval', type=float, default=None,
                       help='Screen capture interval in seconds')
    parser.add_argument('--threshold', type=float, default=None,
                       help='Detection confidence threshold (0.0-1.0)')
    parser.add_argument('--log-level', type=str, default=None,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        ai = ScreenSenseAI(
            capture_interval=args.interval,
            detection_threshold=args.threshold
        )
        ai.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
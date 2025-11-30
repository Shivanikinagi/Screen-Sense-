"""
Database Logger Module
Handles logging of all detections, decisions, and actions
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pickle

logger = logging.getLogger(__name__)


class DatabaseLogger:
    """Logs all system activities to SQLite database"""
    
    def __init__(self, db_path: str = "data/screensense.db"):
        """
        Initialize database logger
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()
        
        logger.info(f"Database logger initialized: {db_path}")
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Detections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                screen_type TEXT NOT NULL,
                ui_elements TEXT NOT NULL,
                extracted_text TEXT,
                confidence REAL,
                screenshot_path TEXT
            )
        """)
        
        # Decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER,
                timestamp REAL NOT NULL,
                action_type TEXT NOT NULL,
                reasoning TEXT,
                confidence REAL,
                requires_confirmation INTEGER,
                user_confirmed INTEGER,
                FOREIGN KEY (detection_id) REFERENCES detections(id)
            )
        """)
        
        # Actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER,
                timestamp REAL NOT NULL,
                action_type TEXT NOT NULL,
                success INTEGER,
                execution_time REAL,
                error_message TEXT,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        """)
        
        # Mistakes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER,
                timestamp REAL NOT NULL,
                wrong_label TEXT,
                correct_label TEXT,
                user_feedback TEXT,
                retrained INTEGER DEFAULT 0,
                FOREIGN KEY (detection_id) REFERENCES detections(id)
            )
        """)
        
        # User overrides table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER,
                timestamp REAL NOT NULL,
                original_action TEXT,
                user_action TEXT,
                reasoning TEXT,
                learned INTEGER DEFAULT 0,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        """)
        
        self.conn.commit()
        logger.info("Database tables created")
    
    def log_detection(self, screen_type: str, ui_elements: List[Dict],
                     extracted_text: Dict, confidence: float,
                     screenshot_path: str = None) -> int:
        """
        Log a detection event
        
        Args:
            screen_type: Type of screen detected
            ui_elements: List of detected UI elements
            extracted_text: Extracted text from screen
            confidence: Detection confidence
            screenshot_path: Path to saved screenshot
        
        Returns:
            Detection ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO detections 
                (timestamp, screen_type, ui_elements, extracted_text, confidence, screenshot_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().timestamp(),
                screen_type,
                json.dumps(ui_elements),
                json.dumps(extracted_text),
                confidence,
                screenshot_path
            ))
            
            self.conn.commit()
            detection_id = cursor.lastrowid
            
            logger.debug(f"Logged detection: {detection_id}")
            return detection_id
            
        except Exception as e:
            logger.error(f"Error logging detection: {e}")
            return -1
    
    def log_decision(self, detection_id: int, action_type: str, reasoning: str,
                    confidence: float, requires_confirmation: bool,
                    user_confirmed: bool = None) -> int:
        """
        Log a decision event
        
        Args:
            detection_id: Associated detection ID
            action_type: Type of action decided
            reasoning: Reasoning for decision
            confidence: Decision confidence
            requires_confirmation: Whether confirmation was required
            user_confirmed: Whether user confirmed (None if not asked)
        
        Returns:
            Decision ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO decisions
                (detection_id, timestamp, action_type, reasoning, confidence, 
                 requires_confirmation, user_confirmed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                detection_id,
                datetime.now().timestamp(),
                action_type,
                reasoning,
                confidence,
                1 if requires_confirmation else 0,
                1 if user_confirmed else (0 if user_confirmed is False else None)
            ))
            
            self.conn.commit()
            decision_id = cursor.lastrowid
            
            logger.debug(f"Logged decision: {decision_id}")
            return decision_id
            
        except Exception as e:
            logger.error(f"Error logging decision: {e}")
            return -1
    
    def log_action(self, decision_id: int, action_type: str, success: bool,
                   execution_time: float, error_message: str = None) -> int:
        """
        Log an action execution
        
        Args:
            decision_id: Associated decision ID
            action_type: Type of action executed
            success: Whether action was successful
            execution_time: Time taken to execute
            error_message: Error message if failed
        
        Returns:
            Action ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO actions
                (decision_id, timestamp, action_type, success, execution_time, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                decision_id,
                datetime.now().timestamp(),
                action_type,
                1 if success else 0,
                execution_time,
                error_message
            ))
            
            self.conn.commit()
            action_id = cursor.lastrowid
            
            logger.debug(f"Logged action: {action_id}")
            return action_id
            
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return -1
    
    def log_mistake(self, detection_id: int, wrong_label: str,
                   correct_label: str, user_feedback: str) -> int:
        """
        Log a detection mistake
        
        Args:
            detection_id: Associated detection ID
            wrong_label: Incorrect label predicted
            correct_label: Correct label from user
            user_feedback: User's feedback
        
        Returns:
            Mistake ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO mistakes
                (detection_id, timestamp, wrong_label, correct_label, user_feedback)
                VALUES (?, ?, ?, ?, ?)
            """, (
                detection_id,
                datetime.now().timestamp(),
                wrong_label,
                correct_label,
                user_feedback
            ))
            
            self.conn.commit()
            mistake_id = cursor.lastrowid
            
            logger.info(f"Logged mistake: {wrong_label} -> {correct_label}")
            return mistake_id
            
        except Exception as e:
            logger.error(f"Error logging mistake: {e}")
            return -1
    
    def log_user_override(self, decision_id: int, original_action: str,
                         user_action: str, reasoning: str) -> int:
        """
        Log a user override
        
        Args:
            decision_id: Associated decision ID
            original_action: Original action suggested
            user_action: Action user chose instead
            reasoning: User's reasoning
        
        Returns:
            Override ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO user_overrides
                (decision_id, timestamp, original_action, user_action, reasoning)
                VALUES (?, ?, ?, ?, ?)
            """, (
                decision_id,
                datetime.now().timestamp(),
                original_action,
                user_action,
                reasoning
            ))
            
            self.conn.commit()
            override_id = cursor.lastrowid
            
            logger.info(f"Logged user override: {original_action} -> {user_action}")
            return override_id
            
        except Exception as e:
            logger.error(f"Error logging override: {e}")
            return -1
    
    def get_mistakes(self, retrained: bool = False) -> List[Dict]:
        """
        Get logged mistakes
        
        Args:
            retrained: Filter by retrained status
        
        Returns:
            List of mistake records
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM mistakes
                WHERE retrained = ?
                ORDER BY timestamp DESC
            """, (1 if retrained else 0,))
            
            columns = [desc[0] for desc in cursor.description]
            mistakes = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return mistakes
            
        except Exception as e:
            logger.error(f"Error getting mistakes: {e}")
            return []
    
    def get_user_overrides(self, learned: bool = False) -> List[Dict]:
        """
        Get user overrides
        
        Args:
            learned: Filter by learned status
        
        Returns:
            List of override records
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM user_overrides
                WHERE learned = ?
                ORDER BY timestamp DESC
            """, (1 if learned else 0,))
            
            columns = [desc[0] for desc in cursor.description]
            overrides = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return overrides
            
        except Exception as e:
            logger.error(f"Error getting overrides: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get system statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            cursor = self.conn.cursor()
            
            # Total counts
            cursor.execute("SELECT COUNT(*) FROM detections")
            total_detections = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM decisions")
            total_decisions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM actions WHERE success = 1")
            successful_actions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM actions WHERE success = 0")
            failed_actions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM mistakes")
            total_mistakes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM mistakes WHERE retrained = 1")
            retrained_mistakes = cursor.fetchone()[0]
            
            return {
                'total_detections': total_detections,
                'total_decisions': total_decisions,
                'successful_actions': successful_actions,
                'failed_actions': failed_actions,
                'success_rate': (successful_actions / (successful_actions + failed_actions) * 100) 
                               if (successful_actions + failed_actions) > 0 else 0,
                'total_mistakes': total_mistakes,
                'retrained_mistakes': retrained_mistakes,
                'pending_mistakes': total_mistakes - retrained_mistakes
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
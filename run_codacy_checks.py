"""
Helper script to run Codacy analysis on all project files
Run this after making changes to analyze code quality
"""

import subprocess
import sys
from pathlib import Path

# List of all Python files to check
FILES_TO_CHECK = [
    "screensense_ai.py",
    "config.py",
    "setup.py",
    "modules/screen_capture.py",
    "modules/preprocessor.py",
    "modules/ui_detector.py",
    "modules/ocr_engine.py",
    "modules/state_analyzer.py",
    "modules/decision_engine.py",
    "modules/action_executor.py",
    "modules/safety_layer.py",
    "modules/learning_loop.py",
    "modules/database_logger.py",
]

def run_codacy_check(file_path: str, root_path: str):
    """Run Codacy analysis on a single file"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {file_path}")
    print(f"{'='*60}")
    
    try:
        # This would be the actual Codacy CLI command
        # Replace with actual command based on your setup
        result = subprocess.run(
            ["codacy-analysis-cli", "analyze", 
             "--directory", root_path,
             "--file", file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✓ {file_path}: No issues found")
        else:
            print(f"⚠ {file_path}: Issues detected")
            print(result.stdout)
            
    except FileNotFoundError:
        print("❌ Codacy CLI not installed")
        print("Please install it or use the MCP server integration")
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠ Timeout analyzing {file_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def main():
    """Run checks on all files"""
    root_path = Path(__file__).parent
    print(f"Root path: {root_path}")
    
    success_count = 0
    total_count = len(FILES_TO_CHECK)
    
    for file_path in FILES_TO_CHECK:
        full_path = root_path / file_path
        if full_path.exists():
            if run_codacy_check(str(file_path), str(root_path)):
                success_count += 1
        else:
            print(f"⚠ File not found: {file_path}")
    
    print(f"\n{'='*60}")
    print(f"Analysis complete: {success_count}/{total_count} files checked")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
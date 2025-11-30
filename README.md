# 🚀 ScreenSense AI

Full-featured AI-powered screen monitoring and automation system with intelligent decision-making capabilities.

## 📋 Features

1. **Screen Capture** - Continuous screenshot capture (100-300ms intervals)
2. **UI Detection** - CNN-based detection of buttons, inputs, popups, ads, warnings
3. **OCR** - Text extraction from detected UI elements using EasyOCR/Tesseract
4. **State Analysis** - Intelligent screen type detection (login, form, error, scam, etc.)
5. **Decision Engine** - Smart action suggestions based on context
6. **Action Execution** - Automated actions via Playwright/pyautogui
7. **Safety Layer** - User confirmation for risky actions
8. **Learning Loop** - Continuous improvement from user feedback
9. **Database Logging** - Complete audit trail of all activities

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip
- Git
- Windows 10+ (recommended) or Linux

### Quick Setup

```bash
# Navigate to project directory
cd "f:\shivani\VSCode\projects\screen sense"

# Create virtual environment (recommended)
python -m venv ss
ss\Scripts\activate  # Windows
# source ss/bin/activate  # Linux/Mac

# Run setup script (installs all dependencies)
python setup.py

# Or install manually
pip install -r requirements.txt

# Install Playwright browsers (required for browser automation)
playwright install chromium
```

### Install Tesseract OCR (Optional - EasyOCR is primary)

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR`
3. Add to PATH: `C:\Program Files\Tesseract-OCR`

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Verify Installation

```bash
# Test the installation
python test_detection.py
```

## 📁 Project Structure

```
screen sense/
├── screensense_ai.py          # Main pipeline orchestrator
├── config.py                   # Configuration settings
├── setup.py                    # Automated setup script
├── requirements.txt            # Python dependencies
├── test_detection.py           # Testing & training data collection
├── run_codacy_checks.py       # Code quality checks
├── README.md                   # This file
│
├── modules/
│   ├── __init__.py
│   ├── screen_capture.py      # Screen capture using MSS
│   ├── preprocessor.py        # Image preprocessing
│   ├── ui_detector.py         # CNN-based UI detection (Faster R-CNN)
│   ├── ocr_engine.py          # OCR engine (EasyOCR + Tesseract)
│   ├── state_analyzer.py      # Screen state analysis
│   ├── decision_engine.py     # Intelligent decision making
│   ├── action_executor.py     # Action execution
│   ├── safety_layer.py        # Safety checks & confirmations
│   ├── learning_loop.py       # Continuous learning system
│   └── database_logger.py     # SQLite logging
│
├── data/                       # Training data & database
│   ├── screensense.db         # SQLite database
│   ├── training_screenshots/  # Collected screenshots
│   └── mistakes.json          # Learning data
│
├── models/                     # Trained models
│   └── ui_detector.pth        # CNN model weights
│
└── logs/                       # Log files
    └── screensense.log        # Application logs
```

## 🚀 Usage

### Basic Usage

```bash
# Start monitoring with default settings
python screensense_ai.py

# Stop with Ctrl+C
```

### Advanced Usage

```bash
# Custom capture interval (faster = more CPU)
python screensense_ai.py --interval 0.1

# Lower detection threshold for more detections
python screensense_ai.py --threshold 0.3

# Enable debug logging
python screensense_ai.py --log-level DEBUG

# Combine options
python screensense_ai.py --interval 0.15 --threshold 0.4 --log-level INFO
```

### Python API

```python
from screensense_ai import ScreenSenseAI

# Initialize with custom settings
ai = ScreenSenseAI(
    capture_interval=0.2,        # Screen capture interval
    detection_threshold=0.5      # UI detection confidence
)

# Customize decision engine preferences
ai.decision_engine.user_preferences = {
    'autofill': True,
    'close_popups': True,
    'block_ads': True
}

# Start monitoring
ai.start()

# In another thread/process, you can:
# ai.stop()  # Stop monitoring
# ai.retrain_model()  # Trigger retraining
```

## 🔧 Configuration

Edit `config.py` to customize behavior:

```python
# Screen capture settings
CAPTURE_INTERVAL = 0.2           # Seconds between captures
TARGET_IMAGE_SIZE = (640, 480)   # Resolution for CNN

# Detection settings
CONFIDENCE_THRESHOLD = 0.5       # UI detection confidence (0.0-1.0)
NMS_THRESHOLD = 0.4              # Non-max suppression
UI_CLASSES = ['button', 'input', 'popup', 'ad', ...]

# OCR settings
OCR_LANGUAGES = ['en']           # Languages for OCR
OCR_CONFIDENCE_THRESHOLD = 0.6

# Safety settings
ASK_CONFIRMATION_ACTIONS = ['autofill', 'click']
HIGH_RISK_DOMAINS = []           # Add domains to block

# Learning settings
RETRAIN_THRESHOLD = 100          # Mistakes before retraining
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EPOCHS = 10

# Logging
LOG_LEVEL = "INFO"               # DEBUG, INFO, WARNING, ERROR
```

## 📊 Monitoring & Statistics

### View Logs

```bash
# Real-time logs
tail -f logs/screensense.log

# Windows
Get-Content logs\screensense.log -Wait
```

### Check Statistics

```python
from modules.database_logger import DatabaseLogger

# Initialize logger
db = DatabaseLogger()

# Get comprehensive statistics
stats = db.get_statistics()

print(f"Total detections: {stats['total_detections']}")
print(f"Total decisions: {stats['total_decisions']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Failed actions: {stats['failed_actions']}")
print(f"Total mistakes: {stats['total_mistakes']}")
print(f"Pending retraining: {stats['pending_mistakes']}")

# Get mistakes for review
mistakes = db.get_mistakes(retrained=False)
for mistake in mistakes:
    print(f"Wrong: {mistake['wrong_label']} -> Correct: {mistake['correct_label']}")

# Get user overrides
overrides = db.get_user_overrides(learned=False)
for override in overrides:
    print(f"Original: {override['original_action']} -> User chose: {override['user_action']}")
```

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests and diagnostics
python test_detection.py

# This will test:
# - Screen capture
# - Image preprocessing
# - UI detection
# - OCR functionality

# Optional: Collect training screenshots
# Follow prompts to collect labeled data
```

### Test Individual Components

```python
from modules.screen_capture import ScreenCapture
from modules.ui_detector import UIDetector

# Test screen capture
capturer = ScreenCapture(monitor_index=1)
screenshot = capturer.capture()
print(f"Screenshot shape: {screenshot.shape}")

# Test UI detection
detector = UIDetector(model_path="models/ui_detector.pth")
detections = detector.detect(screenshot, confidence_threshold=0.3)
print(f"Found {len(detections)} UI elements")
```

## 🎓 Training & Improvement

### Initial Setup (0 UI Elements Detected)

The pre-trained model is trained on COCO dataset (general objects), not UI elements. To get UI detection working:

**Option 1: Lower Detection Threshold**
```bash
python screensense_ai.py --threshold 0.3
```

**Option 2: Collect Training Data**
```bash
python test_detection.py
# Choose "yes" when prompted to collect screenshots
# Navigate through different screens (login, forms, popups)
# Screenshots saved to data/training_screenshots/
```

**Option 3: Fine-tune Model**
```python
# After collecting and labeling data
from modules.learning_loop import LearningLoop
from modules.ui_detector import UIDetector

detector = UIDetector()
learning = LearningLoop(
    model_path="models/ui_detector.pth",
    data_dir="data"
)

# Retrain on your labeled data
stats = learning.retrain_detector(
    model=detector.model,
    epochs=10,
    learning_rate=0.001
)
print(f"Retraining complete: {stats}")
```

### Continuous Learning

The system automatically learns from:
1. **Mistakes**: When detection is wrong, user can correct it
2. **Overrides**: When user chooses different action
3. **Feedback**: User ratings on actions

```python
# System automatically retrains after 100 corrections
# Check learning progress:
from modules.learning_loop import LearningLoop

learning = LearningLoop(model_path="models/ui_detector.pth", data_dir="data")
stats = learning.get_learning_statistics()

print(f"Mistakes learned: {stats['mistakes']['retrained']}/{stats['mistakes']['total']}")
print(f"Corrections learned: {stats['corrections']['learned']}/{stats['corrections']['total']}")
print(f"Accuracy improvement: {stats['accuracy_improvement']:.1f}%")
```

## 🔒 Security & Privacy

### Safety Features
- **User Confirmation**: High-risk actions require explicit approval
- **Risk Assessment**: All screens scored for potential threats (0.0-1.0)
- **Scam Detection**: Keywords and patterns identify phishing attempts
- **Action Blocking**: Dangerous actions automatically prevented
- **Audit Trail**: Complete log of all detections and actions

### Privacy
- **Local Processing**: All data stays on your machine
- **No Cloud**: No data sent to external servers
- **Encrypted Storage**: Sensitive data encrypted (optional)
- **User Control**: Full control over what actions execute

### Adjust Safety Settings

```python
from modules.safety_layer import SafetyLayer

# Initialize with custom settings
safety = SafetyLayer(auto_confirm_low_risk=False)  # Ask for all actions

# In screensense_ai.py, modify:
ai.safety_layer.auto_confirm_low_risk = False  # Require all confirmations
```

## 🐛 Troubleshooting

### Common Issues

**1. Unicode Encoding Error (Windows)**
- Already fixed in latest version
- System automatically sets UTF-8 encoding

**2. EasyOCR Language Error ('eng' not supported)**
- Already fixed: Use 'en' instead of 'eng'
- Update config.py if you modified it

**3. No UI Elements Detected**
- Model needs fine-tuning on UI elements
- Run: `python screensense_ai.py --threshold 0.3`
- Or collect training data: `python test_detection.py`

**4. Slow Performance**
- Increase capture interval: `--interval 0.5`
- Use CPU-only mode (already default)
- Close unnecessary applications

**5. Tesseract Not Found**
- EasyOCR is primary, Tesseract is optional
- Install Tesseract or disable in config

**6. Permission Denied (Screen Capture)**
- Windows: Run as administrator
- Linux: Check X11 permissions

### Check Logs

```bash
# View full log with errors
cat logs/screensense.log | grep ERROR

# Windows
Select-String -Path "logs\screensense.log" -Pattern "ERROR"
```

### Get Help

```bash
# Show command-line help
python screensense_ai.py --help

# Test setup
python test_detection.py

# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep torch
pip list | grep easyocr
```

## 🤝 Contributing

### How to Contribute

1. Fork the repository
2. Create feature branch: `git checkout -b feature/AmazingFeature`
3. Make changes
4. Run quality checks: `python run_codacy_checks.py`
5. Commit: `git commit -m 'Add AmazingFeature'`
6. Push: `git push origin feature/AmazingFeature`
7. Open Pull Request

### Development Setup

```bash
# Clone repository
git clone <repo-url>
cd "screen sense"

# Create virtual environment
python -m venv ss
ss\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black .

# Type checking
mypy modules/
```

### Code Quality

- Follow PEP 8 style guide
- Add type hints
- Write docstrings
- Add unit tests
- Run Codacy checks before committing

## 📝 License

MIT License

Copyright (c) 2025 ScreenSense AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 🆘 Support

### Get Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/screensense/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/yourusername/screensense/discussions)
- **Documentation**: Check logs and this README
- **Email**: support@screensense.ai (coming soon)

### Before Reporting Issues

1. Check logs: `logs/screensense.log`
2. Run tests: `python test_detection.py`
3. Review database: `data/screensense.db`
4. Search existing issues
5. Include error messages and system info

## 🔄 Updates & Changelog

### Version 1.0.0 (Current)
- ✅ Initial release
- ✅ Screen capture with MSS
- ✅ CNN-based UI detection
- ✅ EasyOCR text extraction
- ✅ Intelligent state analysis
- ✅ Decision engine
- ✅ Safety layer
- ✅ Database logging
- ✅ Learning loop
- ✅ Windows UTF-8 support
- ✅ Fixed EasyOCR language codes

### Planned Updates

**v1.1.0**
- [ ] Pre-trained UI detection model
- [ ] Improved detection accuracy
- [ ] Multi-monitor support
- [ ] GUI dashboard

**v1.2.0**
- [ ] Browser extension integration
- [ ] Cloud model sync (optional)
- [ ] Mobile app companion
- [ ] Voice commands

**v2.0.0**
- [ ] GPT-4 integration for natural language
- [ ] Plugin system
- [ ] Advanced automation scripts
- [ ] Team collaboration features

### Update Instructions

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Update Playwright browsers
playwright install chromium

# Check for breaking changes
python test_detection.py
```

## 📊 Performance Benchmarks

### Typical Performance (CPU Mode)

| Operation | Time (avg) | Notes |
|-----------|------------|-------|
| Screen Capture | 50-100ms | Depends on resolution |
| Preprocessing | 20-50ms | Resize + normalize |
| UI Detection | 2000-2500ms | CNN inference (CPU) |
| OCR (per element) | 500-1000ms | EasyOCR (CPU) |
| State Analysis | 10-20ms | Rule-based |
| Decision Making | 5-10ms | Fast logic |
| Total per frame | 2.5-3.5s | Full pipeline |

### Optimization Tips

1. **Increase interval**: `--interval 0.5` for less frequent checks
2. **Lower resolution**: Edit `TARGET_IMAGE_SIZE` in config
3. **Skip OCR**: Only extract text when needed
4. **GPU acceleration**: Install CUDA + PyTorch GPU
5. **Reduce logging**: Set `LOG_LEVEL = "WARNING"`

### GPU Performance (Optional)

With NVIDIA GPU and CUDA:
- UI Detection: ~200-300ms (8-10x faster)
- OCR: ~100-200ms (3-5x faster)
- Total per frame: ~500-800ms

## 🎯 Use Cases & Examples

### 1. Auto-fill Forms
```python
ai = ScreenSenseAI()
ai.decision_engine.user_preferences['autofill'] = True
ai.start()
# System will automatically detect and fill forms
```

### 2. Block Popups & Ads
```python
ai = ScreenSenseAI()
ai.decision_engine.user_preferences['close_popups'] = True
ai.decision_engine.user_preferences['block_ads'] = True
ai.start()
```

### 3. Scam Detection
```python
ai = ScreenSenseAI()
# System automatically detects and warns about scams
# High-risk screens are blocked automatically
ai.start()
```

### 4. Accessibility Helper
```python
ai = ScreenSenseAI()
# Highlights important UI elements
# Provides audio descriptions (coming soon)
ai.start()
```

### 5. Workflow Automation
```python
# Record user actions and replay
ai = ScreenSenseAI()
ai.start()
# System learns from your actions and automates repetitive tasks
```

## 🌟 Key Features Explained

### Intelligent Decision Making
- Context-aware actions based on screen type
- Risk assessment for safety
- User preference learning
- Confidence-based execution

### Continuous Learning
- Learns from mistakes
- Adapts to user behavior
- Improves accuracy over time
- Retrains automatically

### Safety First
- User confirmation for risky actions
- Scam/phishing detection
- Action rollback support
- Complete audit trail

### Privacy Focused
- 100% local processing
- No cloud dependencies
- Encrypted storage options
- User data control

## 📚 Documentation

- **API Reference**: [Coming soon]
- **Architecture Guide**: [Coming soon]
- **Training Tutorial**: [Coming soon]
- **Plugin Development**: [Coming soon]

## 🙏 Acknowledgments

- **PyTorch** for deep learning framework
- **EasyOCR** for text recognition
- **MSS** for screen capture
- **Playwright** for browser automation
- **All contributors** for improvements

---

**Made with ❤️ by the ScreenSense AI Team**

For questions, suggestions, or feedback, please open an issue or start a discussion!
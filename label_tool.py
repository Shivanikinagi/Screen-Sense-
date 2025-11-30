"""
Simple UI Element Labeling Tool
Helps annotate screenshots for training the UI detector
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LabelingTool:
    """GUI tool for labeling UI elements in screenshots"""
    
    def __init__(self, screenshots_dir: str, output_file: str):
        """
        Initialize labeling tool
        
        Args:
            screenshots_dir: Directory containing screenshots
            output_file: JSON file to save annotations
        """
        self.screenshots_dir = Path(screenshots_dir)
        self.output_file = Path(output_file)
        self.screenshots = sorted(list(self.screenshots_dir.glob("*.png")))
        self.current_index = 0
        self.annotations = self._load_annotations()
        
        # UI element classes
        self.classes = [
            'button', 'input', 'popup', 'ad', 'warning',
            'checkbox', 'dropdown', 'link', 'text', 'image',
            'close_button', 'menu', 'icon', 'notification'
        ]
        
        # Drawing state
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_rect = None
        self.rectangles = []
        
        if not self.screenshots:
            logger.error(f"No screenshots found in {screenshots_dir}")
            logger.info("Please run: python test_detection.py")
            logger.info("And choose 'yes' to collect training screenshots")
            return
        
        # Setup GUI
        self._setup_gui()
        self._load_image()
        
        logger.info(f"Loaded {len(self.screenshots)} screenshots")
        logger.info(f"Existing annotations: {len(self.annotations)}")
    
    def _setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("ScreenSense AI - Labeling Tool")
        self.root.geometry("1200x800")
        
        # Top frame - controls
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Class:").pack(side=tk.LEFT, padx=5)
        
        self.class_var = tk.StringVar(value=self.classes[0])
        class_combo = ttk.Combobox(
            top_frame, 
            textvariable=self.class_var,
            values=self.classes,
            width=15
        )
        class_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Undo Last", command=self._undo_last).pack(side=tk.LEFT, padx=5)
        
        self.info_label = ttk.Label(top_frame, text="")
        self.info_label.pack(side=tk.LEFT, padx=20)
        
        # Middle frame - canvas
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        # Bottom frame - navigation
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="<< Previous", command=self._prev_image).pack(side=tk.LEFT, padx=5)
        
        self.progress_label = ttk.Label(bottom_frame, text="")
        self.progress_label.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(bottom_frame, text="Next >>", command=self._next_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Save & Exit", command=self._save_and_exit).pack(side=tk.RIGHT, padx=5)
        
        # Instructions panel
        inst_frame = ttk.LabelFrame(self.root, text="Instructions", padding="10")
        inst_frame.pack(fill=tk.X, padx=10, pady=5)
        
        instructions = """1. Select class from dropdown  2. Click & drag to draw box  3. Release to save  4. Use Previous/Next to navigate"""
        ttk.Label(inst_frame, text=instructions, justify=tk.LEFT).pack()
    
    def _load_annotations(self):
        """Load existing annotations from file"""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded existing annotations: {len(data)} images")
                    return data
            except Exception as e:
                logger.error(f"Error loading annotations: {e}")
        return {}
    
    def _save_annotations(self):
        """Save annotations to file"""
        try:
            # Ensure directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.annotations, f, indent=2)
            logger.info(f"Annotations saved: {len(self.annotations)} images")
        except Exception as e:
            logger.error(f"Error saving annotations: {e}")
            messagebox.showerror("Error", f"Failed to save annotations: {e}")
    
    def _load_image(self):
        """Load current image"""
        if not self.screenshots:
            messagebox.showerror("Error", "No screenshots found!")
            return
            
        if self.current_index >= len(self.screenshots):
            messagebox.showinfo("Complete", "All images labeled!")
            return
        
        # Load image
        image_path = self.screenshots[self.current_index]
        self.current_image = Image.open(image_path)
        
        # Resize if too large
        max_size = (1000, 700)
        self.current_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        self.photo = ImageTk.PhotoImage(self.current_image)
        
        # Clear canvas
        self.canvas.delete("all")
        self.rectangles = []
        
        # Display image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        
        # Load existing annotations for this image
        image_name = image_path.name
        if image_name in self.annotations:
            self._draw_existing_annotations(self.annotations[image_name])
        
        # Update info
        self._update_info()
    
    def _draw_existing_annotations(self, annotations):
        """Draw existing annotations on canvas"""
        for ann in annotations:
            x1, y1, x2, y2 = ann['bbox']
            rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='red',
                width=2
            )
            text_id = self.canvas.create_text(
                x1, y1 - 10,
                text=ann['class'],
                fill='red',
                anchor=tk.SW
            )
            self.rectangles.append({
                'rect_id': rect_id,
                'text_id': text_id,
                'class': ann['class'],
                'bbox': [x1, y1, x2, y2]
            })
    
    def _update_info(self):
        """Update information labels"""
        total = len(self.screenshots)
        current = self.current_index + 1
        annotated = len(self.annotations)
        
        self.progress_label.config(text=f"Image {current}/{total} | Annotated: {annotated}")
        
        image_name = self.screenshots[self.current_index].name
        boxes = len(self.rectangles)
        self.info_label.config(text=f"{image_name} | Boxes: {boxes}")
    
    def _on_mouse_down(self, event):
        """Handle mouse down event"""
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
    
    def _on_mouse_drag(self, event):
        """Handle mouse drag event"""
        if self.drawing:
            # Remove previous rectangle
            if self.current_rect:
                self.canvas.delete(self.current_rect)
            
            # Draw new rectangle
            self.current_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y,
                event.x, event.y,
                outline='green',
                width=2
            )
    
    def _on_mouse_up(self, event):
        """Handle mouse up event"""
        if self.drawing:
            self.drawing = False
            
            # Calculate bbox
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)
            
            # Minimum size check
            if (x2 - x1) < 10 or (y2 - y1) < 10:
                if self.current_rect:
                    self.canvas.delete(self.current_rect)
                self.current_rect = None
                return
            
            # Change color to red (saved)
            if self.current_rect:
                self.canvas.delete(self.current_rect)
            
            rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='red',
                width=2
            )
            
            # Add class label
            current_class = self.class_var.get()
            text_id = self.canvas.create_text(
                x1, y1 - 10,
                text=current_class,
                fill='red',
                anchor=tk.SW
            )
            
            # Save annotation
            self.rectangles.append({
                'rect_id': rect_id,
                'text_id': text_id,
                'class': current_class,
                'bbox': [x1, y1, x2, y2]
            })
            
            self.current_rect = None
            self._update_info()
            self._auto_save()
    
    def _clear_all(self):
        """Clear all annotations for current image"""
        for rect in self.rectangles:
            self.canvas.delete(rect['rect_id'])
            self.canvas.delete(rect['text_id'])
        self.rectangles = []
        self._update_info()
        self._auto_save()
    
    def _undo_last(self):
        """Remove last annotation"""
        if self.rectangles:
            last = self.rectangles.pop()
            self.canvas.delete(last['rect_id'])
            self.canvas.delete(last['text_id'])
            self._update_info()
            self._auto_save()
    
    def _auto_save(self):
        """Auto-save current annotations"""
        image_name = self.screenshots[self.current_index].name
        
        if self.rectangles:
            self.annotations[image_name] = [
                {
                    'class': rect['class'],
                    'bbox': rect['bbox']
                }
                for rect in self.rectangles
            ]
        elif image_name in self.annotations:
            del self.annotations[image_name]
        
        self._save_annotations()
    
    def _prev_image(self):
        """Go to previous image"""
        if self.current_index > 0:
            self.current_index -= 1
            self._load_image()
    
    def _next_image(self):
        """Go to next image"""
        if self.current_index < len(self.screenshots) - 1:
            self.current_index += 1
            self._load_image()
        else:
            messagebox.showinfo("Complete", f"All {len(self.screenshots)} images reviewed!\n\nAnnotated: {len(self.annotations)}")
    
    def _save_and_exit(self):
        """Save and exit"""
        self._save_annotations()
        messagebox.showinfo("Saved", f"Annotations saved to:\n{self.output_file}\n\nTotal annotated: {len(self.annotations)}")
        self.root.quit()
    
    def run(self):
        """Run the labeling tool"""
        if not self.screenshots:
            logger.error("No screenshots to label!")
            return
        self.root.mainloop()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UI Element Labeling Tool')
    parser.add_argument('--dir', type=str, 
                       default='data/training_screenshots',
                       help='Directory containing screenshots')
    parser.add_argument('--output', type=str,
                       default='data/annotations.json',
                       help='Output JSON file for annotations')
    
    args = parser.parse_args()
    
    # Check if directory exists
    screenshots_dir = Path(args.dir)
    if not screenshots_dir.exists():
        logger.error(f"Directory not found: {args.dir}")
        logger.info("\nPlease collect screenshots first:")
        logger.info("  python test_detection.py")
        logger.info("  Choose 'yes' when prompted")
        return
    
    # Check if there are images
    screenshots = list(screenshots_dir.glob("*.png"))
    if not screenshots:
        logger.error(f"No .png screenshots found in {args.dir}")
        logger.info(f"\nFound {len(list(screenshots_dir.iterdir()))} files")
        logger.info("\nPlease collect screenshots first:")
        logger.info("  python test_detection.py")
        return
    
    logger.info("="*60)
    logger.info("ScreenSense AI - Labeling Tool")
    logger.info("="*60)
    logger.info(f"Screenshots directory: {args.dir}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Found {len(screenshots)} screenshots")
    logger.info("="*60)
    
    # Run tool
    try:
        tool = LabelingTool(args.dir, args.output)
        tool.run()
    except Exception as e:
        logger.error(f"Error running labeling tool: {e}", exc_info=True)


if __name__ == "__main__":
    main()
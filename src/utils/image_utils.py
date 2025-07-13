import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Optional, Dict
import cv2

class ImageUtils:
    """Utility class for image operations"""
    
    @staticmethod
    def resize_image(image: Image.Image, max_width: int = 1920, max_height: int = 1080) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        width, height = image.size
        
        if width <= max_width and height <= max_height:
            return image
        
        # Calculate scaling factor
        scale = min(max_width / width, max_height / height)
        
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def create_thumbnail(image: Image.Image, size: Tuple[int, int] = (200, 200)) -> Image.Image:
        """Create thumbnail of image"""
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
        return thumbnail
    
    @staticmethod
    def draw_text_boxes(image: Image.Image, boxes: List[Dict]) -> Image.Image:
        """Draw bounding boxes around text regions"""
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        for box in boxes:
            bbox = box.get('bbox', {})
            x = bbox.get('x', 0)
            y = bbox.get('y', 0)
            width = bbox.get('width', 0)
            height = bbox.get('height', 0)
            
            # Draw rectangle
            draw.rectangle(
                [(x, y), (x + width, y + height)],
                outline='red',
                width=2
            )
            
            # Draw confidence score if available
            if 'confidence' in box:
                conf_text = f"{box['confidence']:.0f}%"
                draw.text((x, y - 15), conf_text, fill='red')
        
        return img_copy
    
    @staticmethod
    def create_comparison_image(original: Image.Image, processed: Image.Image) -> Image.Image:
        """Create side-by-side comparison image"""
        # Ensure both images have the same height
        height = max(original.height, processed.height)
        
        # Resize if needed
        if original.height != height:
            scale = height / original.height
            original = original.resize(
                (int(original.width * scale), height),
                Image.Resampling.LANCZOS
            )
        
        if processed.height != height:
            scale = height / processed.height
            processed = processed.resize(
                (int(processed.width * scale), height),
                Image.Resampling.LANCZOS
            )
        
        # Create new image
        total_width = original.width + processed.width + 20  # 20px gap
        comparison = Image.new('RGB', (total_width, height), 'white')
        
        # Paste images
        comparison.paste(original, (0, 0))
        comparison.paste(processed, (original.width + 20, 0))
        
        # Add labels
        draw = ImageDraw.Draw(comparison)
        try:
            font = ImageFont.truetype("Arial", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 10), "Original", fill='black', font=font)
        draw.text((original.width + 30, 10), "Processed", fill='black', font=font)
        
        return comparison
    
    @staticmethod
    def get_image_stats(image: Image.Image) -> Dict:
        """Get statistical information about image"""
        img_array = np.array(image)
        
        stats = {
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'format': image.format,
            'channels': len(image.getbands()),
            'size_mb': (img_array.nbytes / (1024 * 1024))
        }
        
        # Color statistics
        if len(img_array.shape) == 2:
            # Grayscale
            stats['mean_brightness'] = float(np.mean(img_array))
            stats['std_brightness'] = float(np.std(img_array))
            stats['min_brightness'] = float(np.min(img_array))
            stats['max_brightness'] = float(np.max(img_array))
        else:
            # Color
            stats['mean_rgb'] = [float(np.mean(img_array[:, :, i])) for i in range(3)]
            stats['std_rgb'] = [float(np.std(img_array[:, :, i])) for i in range(3)]
        
        return stats
    
    @staticmethod
    def convert_to_grayscale(image: Image.Image) -> Image.Image:
        """Convert image to grayscale"""
        return image.convert('L')
    
    @staticmethod
    def apply_morphology(image: Image.Image, operation: str = 'close') -> Image.Image:
        """Apply morphological operations"""
        img_array = np.array(image.convert('L'))
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        if operation == 'close':
            result = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
        elif operation == 'open':
            result = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, kernel)
        elif operation == 'dilate':
            result = cv2.dilate(img_array, kernel, iterations=1)
        elif operation == 'erode':
            result = cv2.erode(img_array, kernel, iterations=1)
        else:
            result = img_array
        
        return Image.fromarray(result)
    
    @staticmethod
    def detect_document_corners(image: Image.Image) -> Optional[np.ndarray]:
        """Detect document corners for perspective correction"""
        img_array = np.array(image.convert('L'))
        
        # Edge detection
        edges = cv2.Canny(img_array, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Approximate to quadrilateral
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        if len(approx) == 4:
            return approx.reshape(4, 2)
        
        return None
import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, Tuple, Optional

class ImageAnalyzer:
    """Analyzes image quality and characteristics for preprocessing decisions"""
    
    def __init__(self):
        self.metrics = {}
    
    def analyze(self, image: Image.Image) -> Dict[str, float]:
        """Comprehensive image quality analysis"""
        img_array = np.array(image)
        
        # Convert to grayscale for analysis if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        self.metrics = {
            'blur_score': self._detect_blur(gray),
            'contrast': self._measure_contrast(gray),
            'brightness': self._measure_brightness(gray),
            'noise_level': self._estimate_noise(gray),
            'text_confidence': self._quick_ocr_confidence(gray),
            'skew_angle': self._detect_skew(gray),
            'is_color': len(img_array.shape) == 3,
            'has_low_contrast': False,
            'is_too_dark': False,
            'is_too_bright': False,
            'is_blurry': False,
            'is_noisy': False,
            'needs_skew_correction': False,
            'overall_quality': 0.0
        }
        
        # Determine quality issues
        self._determine_quality_issues()
        
        # Calculate overall quality score
        self._calculate_overall_quality()
        
        return self.metrics
    
    def _detect_blur(self, gray: np.ndarray) -> float:
        """Detect image blur using Laplacian variance"""
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(laplacian_var)
    
    def _measure_contrast(self, gray: np.ndarray) -> float:
        """Measure image contrast using standard deviation"""
        return float(gray.std())
    
    def _measure_brightness(self, gray: np.ndarray) -> float:
        """Measure average brightness"""
        return float(gray.mean())
    
    def _estimate_noise(self, gray: np.ndarray) -> float:
        """Estimate noise level using median absolute deviation"""
        median = np.median(gray)
        mad = np.median(np.abs(gray - median))
        return float(mad)
    
    def _quick_ocr_confidence(self, gray: np.ndarray) -> float:
        """Quick OCR test to estimate text quality"""
        try:
            # Resize for faster processing
            height, width = gray.shape
            if width > 1000:
                scale = 1000 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized = cv2.resize(gray, (new_width, new_height))
            else:
                resized = gray
            
            # Get OCR data
            data = pytesseract.image_to_data(resized, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            
            return float(np.mean(confidences)) if confidences else 0.0
        except Exception:
            return 0.0
    
    def _detect_skew(self, gray: np.ndarray) -> float:
        """Detect text skew angle using Hough transform"""
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough transform to detect lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None and len(lines) > 0:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = (theta * 180 / np.pi) - 90
                if -45 <= angle <= 45:  # Only consider reasonable angles
                    angles.append(angle)
            
            if angles:
                # Use median to avoid outliers
                return float(np.median(angles))
        
        return 0.0
    
    def _determine_quality_issues(self):
        """Determine specific quality issues based on metrics"""
        self.metrics['has_low_contrast'] = self.metrics['contrast'] < 40
        self.metrics['is_too_dark'] = self.metrics['brightness'] < 80
        self.metrics['is_too_bright'] = self.metrics['brightness'] > 200
        self.metrics['is_blurry'] = self.metrics['blur_score'] < 100
        self.metrics['is_noisy'] = self.metrics['noise_level'] > 15
        self.metrics['needs_skew_correction'] = abs(self.metrics['skew_angle']) > 0.5
    
    def _calculate_overall_quality(self):
        """Calculate overall quality score (0-100)"""
        score = 100.0
        
        # Deduct points for various issues
        if self.metrics['has_low_contrast']:
            score -= 20
        if self.metrics['is_too_dark'] or self.metrics['is_too_bright']:
            score -= 15
        if self.metrics['is_blurry']:
            score -= 25
        if self.metrics['is_noisy']:
            score -= 15
        if self.metrics['needs_skew_correction']:
            score -= 10
        
        # Consider OCR confidence
        ocr_factor = self.metrics['text_confidence'] / 100.0
        score = score * (0.5 + 0.5 * ocr_factor)
        
        self.metrics['overall_quality'] = max(0.0, min(100.0, score))
    
    def get_preprocessing_recommendations(self) -> Dict[str, bool]:
        """Get recommended preprocessing steps based on analysis"""
        recommendations = {
            'convert_grayscale': self.metrics['is_color'] and self.metrics['text_confidence'] < 70,
            'adjust_brightness': self.metrics['is_too_dark'] or self.metrics['is_too_bright'],
            'enhance_contrast': self.metrics['has_low_contrast'],
            'sharpen': self.metrics['is_blurry'],
            'denoise': self.metrics['is_noisy'],
            'correct_skew': self.metrics['needs_skew_correction'],
            'apply_threshold': self.metrics['text_confidence'] < 60
        }
        
        return recommendations
    
    def needs_preprocessing(self) -> bool:
        """Determine if image needs any preprocessing"""
        return self.metrics['overall_quality'] < 80 or any(self.get_preprocessing_recommendations().values())
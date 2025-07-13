import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from typing import Dict, Tuple, List, Optional
import math
from .image_analyzer import ImageAnalyzer

class SmartPreprocessor:
    """Smart image preprocessing with automatic detection and enhancement"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.analyzer = ImageAnalyzer()
        self.processing_history = []
    
    def auto_preprocess(self, image: Image.Image, force_steps: Optional[List[str]] = None) -> Tuple[Image.Image, Dict]:
        """
        Automatically preprocess image based on quality analysis
        
        Args:
            image: Input PIL Image
            force_steps: Optional list of preprocessing steps to force apply
            
        Returns:
            Tuple of (processed_image, processing_info)
        """
        # Analyze image quality
        metrics = self.analyzer.analyze(image)
        recommendations = self.analyzer.get_preprocessing_recommendations()
        
        # Start with original image
        processed = image.copy()
        applied_steps = []
        step_details = []
        
        # Apply forced steps if any
        if force_steps:
            for step in force_steps:
                if step in recommendations:
                    recommendations[step] = True
        
        # Apply preprocessing steps based on recommendations
        if recommendations.get('convert_grayscale', False) and processed.mode != 'L':
            processed = processed.convert('L')
            applied_steps.append('grayscale')
            step_details.append({'step': 'grayscale', 'reason': 'Improve text recognition'})
        
        if recommendations.get('correct_skew', False):
            angle = metrics['skew_angle']
            processed = self._correct_skew(processed, angle)
            applied_steps.append('skew_correction')
            step_details.append({'step': 'skew_correction', 'angle': angle, 'reason': 'Text alignment'})
        
        if recommendations.get('adjust_brightness', False):
            processed = self._auto_brightness(processed, metrics['brightness'])
            applied_steps.append('brightness_adjustment')
            step_details.append({'step': 'brightness_adjustment', 'reason': 'Optimize brightness'})
        
        if recommendations.get('enhance_contrast', False):
            processed = self._enhance_contrast(processed)
            applied_steps.append('contrast_enhancement')
            step_details.append({'step': 'contrast_enhancement', 'reason': 'Improve text clarity'})
        
        if recommendations.get('denoise', False):
            processed = self._smart_denoise(processed, metrics['noise_level'])
            applied_steps.append('denoising')
            step_details.append({'step': 'denoising', 'noise_level': metrics['noise_level'], 'reason': 'Reduce noise'})
        
        if recommendations.get('sharpen', False):
            processed = self._smart_sharpen(processed, metrics['blur_score'])
            applied_steps.append('sharpening')
            step_details.append({'step': 'sharpening', 'blur_score': metrics['blur_score'], 'reason': 'Reduce blur'})
        
        if recommendations.get('apply_threshold', False):
            processed = self._adaptive_threshold(processed)
            applied_steps.append('adaptive_threshold')
            step_details.append({'step': 'adaptive_threshold', 'reason': 'Binarize text'})
        
        # Re-analyze processed image
        processed_metrics = self.analyzer.analyze(processed)
        
        processing_info = {
            'original_metrics': metrics,
            'processed_metrics': processed_metrics,
            'applied_steps': applied_steps,
            'step_details': step_details,
            'quality_improvement': processed_metrics['overall_quality'] - metrics['overall_quality'],
            'recommendations': recommendations
        }
        
        self.processing_history.append(processing_info)
        
        return processed, processing_info
    
    def _correct_skew(self, image: Image.Image, angle: float) -> Image.Image:
        """Correct image skew"""
        if abs(angle) < 0.5:
            return image
        
        # Rotate image
        rotated = image.rotate(-angle, expand=True, fillcolor='white' if image.mode != 'RGBA' else (255, 255, 255, 0))
        
        return rotated
    
    def _auto_brightness(self, image: Image.Image, current_brightness: float) -> Image.Image:
        """Automatically adjust brightness to optimal level"""
        target_brightness = 140  # Optimal brightness for OCR
        
        if abs(current_brightness - target_brightness) < 10:
            return image
        
        # Calculate enhancement factor
        if current_brightness > 0:
            factor = target_brightness / current_brightness
            factor = max(0.3, min(3.0, factor))  # Limit factor range
        else:
            factor = 1.5
        
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast using CLAHE or standard enhancement"""
        img_array = np.array(image)
        
        if len(img_array.shape) == 2:
            # Grayscale - use CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(img_array)
            return Image.fromarray(enhanced)
        else:
            # Color - use PIL enhancement
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(1.5)
    
    def _smart_denoise(self, image: Image.Image, noise_level: float) -> Image.Image:
        """Apply appropriate denoising based on noise level"""
        img_array = np.array(image)
        
        if noise_level < 5:
            return image  # No significant noise
        
        if noise_level > 20:
            # Heavy noise - use Non-local Means
            if len(img_array.shape) == 2:
                denoised = cv2.fastNlMeansDenoising(img_array, h=10, templateWindowSize=7, searchWindowSize=21)
            else:
                denoised = cv2.fastNlMeansDenoisingColored(img_array, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)
        elif noise_level > 10:
            # Medium noise - use bilateral filter
            denoised = cv2.bilateralFilter(img_array, d=9, sigmaColor=75, sigmaSpace=75)
        else:
            # Light noise - use Gaussian blur
            denoised = cv2.GaussianBlur(img_array, (3, 3), 0)
        
        return Image.fromarray(denoised)
    
    def _smart_sharpen(self, image: Image.Image, blur_score: float) -> Image.Image:
        """Apply sharpening based on blur level"""
        if blur_score > 500:
            return image  # Already sharp enough
        
        if blur_score < 50:
            # Very blurry - aggressive sharpening
            kernel = np.array([[-1, -1, -1],
                              [-1, 9, -1],
                              [-1, -1, -1]])
            img_array = np.array(image)
            sharpened = cv2.filter2D(img_array, -1, kernel)
            return Image.fromarray(sharpened)
        else:
            # Moderate blur - use unsharp mask
            return image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    def _adaptive_threshold(self, image: Image.Image) -> Image.Image:
        """Apply adaptive thresholding for better text extraction"""
        # Convert to grayscale if needed
        if image.mode != 'L':
            image = image.convert('L')
        
        img_array = np.array(image)
        
        # Try multiple thresholding methods and choose the best
        methods = []
        
        # Otsu's method
        _, otsu = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        methods.append(('otsu', otsu))
        
        # Adaptive Gaussian
        adaptive_gaussian = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        methods.append(('adaptive_gaussian', adaptive_gaussian))
        
        # Adaptive Mean
        adaptive_mean = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        methods.append(('adaptive_mean', adaptive_mean))
        
        # Choose the best method based on text area ratio
        best_method = None
        best_score = 0
        
        for name, result in methods:
            # Calculate text pixel ratio
            text_pixels = np.sum(result == 0)  # Black pixels (text)
            total_pixels = result.size
            ratio = text_pixels / total_pixels
            
            # Ideal ratio is between 0.05 and 0.3
            if 0.05 <= ratio <= 0.3:
                score = 1.0 - abs(ratio - 0.15) / 0.15
                if score > best_score:
                    best_score = score
                    best_method = result
        
        if best_method is None:
            best_method = otsu  # Default to Otsu
        
        return Image.fromarray(best_method)
    
    def manual_preprocess(self, image: Image.Image, steps: List[str]) -> Tuple[Image.Image, Dict]:
        """Apply specific preprocessing steps manually"""
        processed = image.copy()
        applied_steps = []
        
        step_mapping = {
            'grayscale': lambda img: img.convert('L'),
            'brightness': lambda img: self._auto_brightness(img, np.array(img).mean()),
            'contrast': lambda img: self._enhance_contrast(img),
            'denoise': lambda img: self._smart_denoise(img, 10),
            'sharpen': lambda img: self._smart_sharpen(img, 100),
            'threshold': lambda img: self._adaptive_threshold(img),
            'invert': lambda img: ImageOps.invert(img.convert('L'))
        }
        
        for step in steps:
            if step in step_mapping:
                processed = step_mapping[step](processed)
                applied_steps.append(step)
        
        return processed, {'applied_steps': applied_steps}
    
    def get_processing_preview(self, image: Image.Image) -> Dict[str, Image.Image]:
        """Generate preview of different preprocessing options"""
        previews = {
            'original': image,
            'auto': self.auto_preprocess(image)[0],
            'grayscale': image.convert('L'),
            'enhanced': self._enhance_contrast(image),
            'threshold': self._adaptive_threshold(image)
        }
        
        return previews
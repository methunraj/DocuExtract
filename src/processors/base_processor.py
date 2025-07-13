from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PIL import Image

class BaseProcessor(ABC):
    """Abstract base class for all processors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def process(self, image: Image.Image, **kwargs) -> Dict[str, Any]:
        """Process an image and return results"""
        pass
    
    def validate_input(self, image: Image.Image) -> bool:
        """Validate input image"""
        if not isinstance(image, Image.Image):
            raise ValueError("Input must be a PIL Image object")
        return True
    
    def prepare_response(self, data: Any, error: Optional[str] = None) -> Dict[str, Any]:
        """Prepare standardized response"""
        if error:
            return {
                'success': False,
                'error': error,
                'data': None
            }
        
        return {
            'success': True,
            'error': None,
            'data': data
        }
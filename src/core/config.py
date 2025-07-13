import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages application configuration from YAML file"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            return self._config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_path} not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the loaded configuration"""
        if self._config is None:
            self.load_config()
        return self._config
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM-specific configuration"""
        return self.config.get('llm', {})
    
    def get_ocr_config(self) -> Dict[str, Any]:
        """Get OCR-specific configuration"""
        return self.config.get('ocr', {})
    
    def get_preprocessing_config(self) -> Dict[str, Any]:
        """Get preprocessing configuration"""
        return self.config.get('preprocessing', {})
    
    def get_general_config(self) -> Dict[str, Any]:
        """Get general configuration"""
        return self.config.get('general', {})
    
    def get_llm_models(self) -> list:
        """Get list of available LLM models"""
        return self.get_llm_config().get('models', [])
    
    def get_vision_models(self) -> list:
        """Get list of vision-capable LLM models"""
        return [m for m in self.get_llm_models() if m.get('type') == 'vision']
    
    def get_text_models(self) -> list:
        """Get list of text-only LLM models"""
        return [m for m in self.get_llm_models() if m.get('type') == 'text']
    
    def get_ocr_languages(self) -> list:
        """Get list of supported OCR languages"""
        return self.get_ocr_config().get('languages', ['eng'])
    
    def get_default_llm_model(self) -> Optional[str]:
        """Get default LLM model name"""
        return self.get_llm_config().get('default_model')
    
    def get_default_ocr_language(self) -> str:
        """Get default OCR language"""
        return self.get_ocr_config().get('default_language', 'eng')
    
    def get_max_images(self) -> int:
        """Get maximum number of images for batch processing"""
        return self.get_general_config().get('max_images', 50)
    
    def get_temp_dir(self) -> Path:
        """Get temporary directory path"""
        temp_dir = self.get_general_config().get('temp_dir', './temp')
        path = Path(temp_dir)
        path.mkdir(exist_ok=True)
        return path
    
    def get_supported_formats(self) -> list:
        """Get list of supported image formats"""
        return self.get_general_config().get('supported_formats', 
            ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'pdf'])
    
    def is_preprocessing_enabled_by_default(self) -> bool:
        """Check if preprocessing is enabled by default"""
        return self.get_preprocessing_config().get('enabled_by_default', False)
    
    def get_preprocessing_steps(self) -> list:
        """Get list of preprocessing steps"""
        return self.get_preprocessing_config().get('steps', [])
    
    def get_llm_parameters(self) -> Dict[str, Any]:
        """Get LLM parameters for fine-tuning"""
        return self.get_llm_config().get('parameters', {
            'temperature': 0.1,
            'top_p': 0.9,
            'top_k': 40,
            'num_ctx': 4096,
            'num_predict': 2048
        })
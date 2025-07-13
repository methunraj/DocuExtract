import json
from typing import Any, Dict, List, Optional, Tuple
import os

class Validators:
    """Utility class for various validations"""
    
    @staticmethod
    def validate_json_schema(schema_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if string is valid JSON
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not schema_str or not schema_str.strip():
            return True, None  # Empty schema is valid (optional)
        
        try:
            json.loads(schema_str)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if file path exists and is accessible
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "File path is empty"
        
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        if not os.access(file_path, os.R_OK):
            return False, f"File is not readable: {file_path}"
        
        return True, None
    
    @staticmethod
    def validate_folder_path(folder_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if folder path exists and is accessible
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not folder_path:
            return False, "Folder path is empty"
        
        if not os.path.exists(folder_path):
            return False, f"Folder does not exist: {folder_path}"
        
        if not os.path.isdir(folder_path):
            return False, f"Path is not a directory: {folder_path}"
        
        if not os.access(folder_path, os.R_OK):
            return False, f"Folder is not readable: {folder_path}"
        
        return True, None
    
    @staticmethod
    def validate_image_format(file_path: str, supported_formats: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate if file has supported image format
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        extension = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if not extension:
            return False, "File has no extension"
        
        if extension not in supported_formats:
            return False, f"Unsupported format: {extension}. Supported: {', '.join(supported_formats)}"
        
        return True, None
    
    @staticmethod
    def validate_model_config(model_name: str, model_list: List[Dict]) -> Tuple[bool, Optional[str]]:
        """
        Validate if model exists in configuration
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not model_name:
            return False, "Model name is empty"
        
        model_names = [m.get('name') for m in model_list]
        
        if model_name not in model_names:
            return False, f"Model '{model_name}' not found. Available: {', '.join(model_names)}"
        
        return True, None
    
    @staticmethod
    def validate_language_code(language: str, supported_languages: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate OCR language code
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not language:
            return False, "Language code is empty"
        
        if language not in supported_languages:
            return False, f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}"
        
        return True, None
    
    @staticmethod
    def validate_output_format(format: str, mode: str) -> Tuple[bool, Optional[str]]:
        """
        Validate output format for given processing mode
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_formats = {
            "LLM-based": ["JSON", "XLSX"],
            "Standard OCR": ["JSON", "Markdown"],
            "OCR + LLM Extraction": ["JSON", "XLSX"]
        }
        
        if mode not in valid_formats:
            return False, f"Unknown processing mode: {mode}"
        
        if format not in valid_formats[mode]:
            return False, f"Format '{format}' not supported for mode '{mode}'. Valid: {', '.join(valid_formats[mode])}"
        
        return True, None
    
    @staticmethod
    def validate_batch_size(num_files: int, max_allowed: int) -> Tuple[bool, Optional[str]]:
        """
        Validate batch size for processing
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if num_files <= 0:
            return False, "No files to process"
        
        if num_files > max_allowed:
            return False, f"Too many files: {num_files}. Maximum allowed: {max_allowed}"
        
        return True, None
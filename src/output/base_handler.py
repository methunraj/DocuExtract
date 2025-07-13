from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os
from datetime import datetime

class BaseOutputHandler(ABC):
    """Abstract base class for output handlers"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @abstractmethod
    def save(self, results: List[Dict[str, Any]], output_path: str) -> str:
        """Save results to file"""
        pass
    
    @abstractmethod
    def format_single_result(self, result: Dict[str, Any]) -> Any:
        """Format a single result"""
        pass
    
    def generate_filename(self, base_name: str, extension: str) -> str:
        """Generate timestamped filename"""
        return f"{base_name}_{self.timestamp}.{extension}"
    
    def ensure_directory(self, file_path: str):
        """Ensure directory exists for file path"""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
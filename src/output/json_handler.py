import json
from typing import List, Dict, Any
from .base_handler import BaseOutputHandler

class JSONHandler(BaseOutputHandler):
    """Handler for JSON output format"""
    
    def __init__(self, pretty_print: bool = True):
        super().__init__()
        self.pretty_print = pretty_print
    
    def save(self, results: List[Dict[str, Any]], output_path: str) -> str:
        """Save results as JSON file"""
        self.ensure_directory(output_path)
        
        formatted_results = [self.format_single_result(r) for r in results]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if self.pretty_print:
                json.dump(formatted_results, f, indent=2, ensure_ascii=False)
            else:
                json.dump(formatted_results, f, ensure_ascii=False)
        
        return output_path
    
    def format_single_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single result for JSON output"""
        formatted = {
            'filename': result.get('filename', 'unknown'),
            'timestamp': self.timestamp,
            'processing_mode': result.get('mode', 'unknown')
        }
        
        # Handle different result types
        if 'error' in result:
            formatted['status'] = 'error'
            formatted['error'] = result['error']
        else:
            formatted['status'] = 'success'
            
            # Extract data based on processing mode
            if 'data' in result:
                data = result['data']
                
                # Direct data from LLM or structured extraction
                if isinstance(data, dict):
                    formatted['extracted_data'] = data
                else:
                    formatted['extracted_data'] = {'content': data}
            
            # OCR-specific data
            elif 'text' in result:
                formatted['extracted_data'] = {
                    'text': result['text'],
                    'confidence': result.get('confidence'),
                    'word_count': result.get('word_count')
                }
            
            # Hybrid mode data
            elif 'ocr_result' in result:
                formatted['ocr_data'] = {
                    'text': result['ocr_result'].get('text', ''),
                    'confidence': result['ocr_result'].get('confidence', 0)
                }
                if result.get('llm_result'):
                    formatted['extracted_data'] = result['llm_result']
        
        # Add processing info if available
        if 'processing_info' in result:
            formatted['processing_details'] = result['processing_info']
        
        return formatted
    
    def to_string(self, results: List[Dict[str, Any]]) -> str:
        """Convert results to JSON string"""
        formatted_results = [self.format_single_result(r) for r in results]
        
        if self.pretty_print:
            return json.dumps(formatted_results, indent=2, ensure_ascii=False)
        else:
            return json.dumps(formatted_results, ensure_ascii=False)
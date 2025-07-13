from typing import List, Dict, Any
from .base_handler import BaseOutputHandler
import json

class MarkdownHandler(BaseOutputHandler):
    """Handler for Markdown output format"""
    
    def save(self, results: List[Dict[str, Any]], output_path: str) -> str:
        """Save results as Markdown file"""
        self.ensure_directory(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown(results))
        
        return output_path
    
    def format_single_result(self, result: Dict[str, Any]) -> str:
        """Format a single result as Markdown section"""
        sections = []
        
        # Header with filename
        filename = result.get('filename', 'Unknown')
        sections.append(f"## {filename}\n")
        
        # Status
        if 'error' in result:
            sections.append(f"**Status:** ❌ Error\n")
            sections.append(f"**Error:** {result['error']}\n")
        else:
            sections.append(f"**Status:** ✅ Success\n")
            
            # Processing mode
            mode = result.get('mode', 'Unknown')
            sections.append(f"**Processing Mode:** {mode}\n")
            
            # Main content
            if 'text' in result:
                # Simple OCR result
                sections.append("\n### Extracted Text\n")
                sections.append("```\n")
                sections.append(result['text'])
                sections.append("\n```\n")
                
                # Confidence if available
                if 'confidence' in result:
                    sections.append(f"\n**OCR Confidence:** {result['confidence']:.1f}%\n")
                
                if 'word_count' in result:
                    sections.append(f"**Word Count:** {result['word_count']}\n")
            
            elif 'data' in result:
                # Structured data from LLM
                sections.append("\n### Extracted Data\n")
                
                data = result['data']
                if isinstance(data, dict):
                    if 'text' in data:
                        sections.append(data['text'])
                    else:
                        # Format as code block for structured data
                        sections.append("```json\n")
                        sections.append(json.dumps(data, indent=2, ensure_ascii=False))
                        sections.append("\n```\n")
                else:
                    sections.append(str(data))
            
            # Hybrid mode results
            elif 'ocr_result' in result:
                sections.append("\n### OCR Result\n")
                ocr_data = result['ocr_result']
                sections.append("```\n")
                sections.append(ocr_data.get('text', 'No text extracted'))
                sections.append("\n```\n")
                sections.append(f"**OCR Confidence:** {ocr_data.get('confidence', 0):.1f}%\n")
                
                if result.get('llm_result'):
                    sections.append("\n### LLM Extraction\n")
                    llm_data = result['llm_result']
                    if isinstance(llm_data, dict):
                        sections.append("```json\n")
                        sections.append(json.dumps(llm_data, indent=2, ensure_ascii=False))
                        sections.append("\n```\n")
                    else:
                        sections.append(str(llm_data))
        
        # Processing details if available
        if 'processing_info' in result:
            info = result['processing_info']
            if info.get('applied_steps'):
                sections.append("\n### Processing Steps Applied\n")
                for step in info['applied_steps']:
                    sections.append(f"- {step}\n")
            
            if info.get('quality_improvement') is not None:
                sections.append(f"\n**Quality Improvement:** {info['quality_improvement']:.1f}%\n")
        
        sections.append("\n---\n")
        
        return '\n'.join(sections)
    
    def _generate_markdown(self, results: List[Dict[str, Any]]) -> str:
        """Generate complete Markdown document"""
        sections = []
        
        # Document header
        sections.append("# OCR & Data Extraction Results\n")
        sections.append(f"**Generated:** {self.timestamp}\n")
        sections.append(f"**Total Images:** {len(results)}\n")
        
        # Summary statistics
        successful = sum(1 for r in results if 'error' not in r)
        sections.append(f"**Successful:** {successful}/{len(results)}\n")
        
        sections.append("\n---\n\n")
        
        # Individual results
        for result in results:
            sections.append(self.format_single_result(result))
        
        return '\n'.join(sections)
    
    def to_string(self, results: List[Dict[str, Any]]) -> str:
        """Convert results to Markdown string"""
        return self._generate_markdown(results)
import pytesseract
from PIL import Image
from typing import Dict, Any, Optional, List
import cv2
import numpy as np
from .base_processor import BaseProcessor

class OCRProcessor(BaseProcessor):
    """Processor for traditional OCR text extraction"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine = config.get('ocr', {}).get('engine', 'tesseract')
        self.tesseract_path = config.get('ocr', {}).get('path')
        
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
    
    def process(self, image: Image.Image, language: str = 'eng', **kwargs) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Args:
            image: PIL Image to process
            language: OCR language code (e.g., 'eng', 'fra', 'deu')
            
        Returns:
            Dictionary with extracted text and metadata
        """
        self.validate_input(image)
        
        try:
            # Basic text extraction
            text = pytesseract.image_to_string(image, lang=language)
            
            # Get detailed data including confidence scores
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = np.mean(confidences) if confidences else 0
            
            # Get bounding boxes for text regions
            boxes = self._extract_text_boxes(data)
            
            # Get additional info
            osd = self._get_orientation_info(image)
            
            result = {
                'text': text.strip(),
                'confidence': float(avg_confidence),
                'word_count': len([w for w in data['text'] if w.strip()]),
                'language': language,
                'text_boxes': boxes,
                'orientation': osd
            }
            
            return self.prepare_response(result)
            
        except Exception as e:
            return self.prepare_response(None, f"OCR processing failed: {str(e)}")
    
    def _extract_text_boxes(self, data: Dict) -> List[Dict]:
        """Extract bounding boxes for text regions"""
        boxes = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0 and data['text'][i].strip():
                box = {
                    'text': data['text'][i],
                    'confidence': int(data['conf'][i]),
                    'bbox': {
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    }
                }
                boxes.append(box)
        
        return boxes
    
    def _get_orientation_info(self, image: Image.Image) -> Dict:
        """Get image orientation and script detection info"""
        try:
            osd = pytesseract.image_to_osd(image)
            osd_dict = {}
            
            for line in osd.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    osd_dict[key.strip()] = value.strip()
            
            return {
                'rotation': osd_dict.get('Rotate', '0'),
                'orientation_confidence': osd_dict.get('Orientation confidence', '0'),
                'script': osd_dict.get('Script', 'Unknown'),
                'script_confidence': osd_dict.get('Script confidence', '0')
            }
        except:
            return {
                'rotation': '0',
                'orientation_confidence': '0',
                'script': 'Unknown',
                'script_confidence': '0'
            }
    
    def process_with_multiple_languages(self, image: Image.Image, languages: List[str]) -> Dict[str, Any]:
        """Process image with multiple language options"""
        results = {}
        best_result = None
        best_confidence = 0
        
        for lang in languages:
            result = self.process(image, lang)
            if result['success']:
                results[lang] = result['data']
                if result['data']['confidence'] > best_confidence:
                    best_confidence = result['data']['confidence']
                    best_result = result['data']
                    best_result['detected_language'] = lang
        
        return self.prepare_response({
            'best_result': best_result,
            'all_results': results
        })
    
    def extract_structured_data(self, image: Image.Image, language: str = 'eng') -> Dict[str, Any]:
        """Extract structured data like tables from image"""
        try:
            # Get TSV output for better structure parsing
            tsv_data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            # Group text by blocks and paragraphs
            blocks = self._group_text_by_blocks(tsv_data)
            
            # Detect potential table structures
            tables = self._detect_tables(tsv_data)
            
            result = {
                'blocks': blocks,
                'tables': tables,
                'has_tables': len(tables) > 0
            }
            
            return self.prepare_response(result)
            
        except Exception as e:
            return self.prepare_response(None, f"Structured extraction failed: {str(e)}")
    
    def _group_text_by_blocks(self, data: Dict) -> List[Dict]:
        """Group text elements by blocks"""
        blocks = {}
        
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                block_num = data['block_num'][i]
                
                if block_num not in blocks:
                    blocks[block_num] = {
                        'block_num': block_num,
                        'text': [],
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    }
                
                blocks[block_num]['text'].append(data['text'][i])
                
                # Update bounding box to encompass all text in block
                blocks[block_num]['bbox']['width'] = max(
                    blocks[block_num]['bbox']['width'],
                    data['left'][i] + data['width'][i] - blocks[block_num]['bbox']['x']
                )
                blocks[block_num]['bbox']['height'] = max(
                    blocks[block_num]['bbox']['height'],
                    data['top'][i] + data['height'][i] - blocks[block_num]['bbox']['y']
                )
        
        # Convert to list and join text
        block_list = []
        for block in blocks.values():
            block['text'] = ' '.join(block['text'])
            block_list.append(block)
        
        return sorted(block_list, key=lambda x: (x['bbox']['y'], x['bbox']['x']))
    
    def _detect_tables(self, data: Dict) -> List[Dict]:
        """Detect potential table structures in OCR data"""
        # Simple table detection based on aligned text positions
        # This is a basic implementation - could be enhanced with more sophisticated methods
        
        tables = []
        # Group words by approximate Y position (rows)
        rows = {}
        tolerance = 10  # pixels
        
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                y = data['top'][i]
                
                # Find which row this belongs to
                row_y = None
                for existing_y in rows:
                    if abs(existing_y - y) < tolerance:
                        row_y = existing_y
                        break
                
                if row_y is None:
                    row_y = y
                    rows[row_y] = []
                
                rows[row_y].append({
                    'text': data['text'][i],
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })
        
        # Check if we have a table-like structure (multiple rows with similar column positions)
        if len(rows) > 2:
            sorted_rows = sorted(rows.items(), key=lambda x: x[0])
            
            # Simple table detection: check if words align vertically
            potential_table = []
            for y, words in sorted_rows:
                sorted_words = sorted(words, key=lambda x: x['x'])
                potential_table.append(sorted_words)
            
            # If we have consistent number of "columns" across rows, it might be a table
            col_counts = [len(row) for row in potential_table]
            if col_counts and max(col_counts) > 1 and min(col_counts) > 0:
                tables.append({
                    'rows': potential_table,
                    'row_count': len(potential_table),
                    'col_count': max(col_counts)
                })
        
        return tables
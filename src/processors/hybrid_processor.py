from typing import Dict, Any, Optional
from PIL import Image
from .base_processor import BaseProcessor
from .ocr_processor import OCRProcessor
from .llm_processor import LLMProcessor

class HybridProcessor(BaseProcessor):
    """Processor that combines OCR and LLM for enhanced extraction"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ocr_processor = OCRProcessor(config)
        self.llm_processor = LLMProcessor(config)
    
    def process(self, image: Image.Image, language: str, model: str, 
                prompt: str, schema: Optional[str] = None, llm_parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Process image using OCR first, then LLM for structured extraction
        
        Args:
            image: PIL Image to process
            language: OCR language code
            model: LLM model name
            prompt: Prompt for LLM extraction
            schema: Optional JSON schema for structured output
            llm_parameters: Optional LLM parameters for fine-tuning
            
        Returns:
            Dictionary with combined results
        """
        self.validate_input(image)
        
        # Step 1: Extract text using OCR
        ocr_result = self.ocr_processor.process(image, language)
        
        if not ocr_result['success']:
            return self.prepare_response(None, f"OCR failed: {ocr_result['error']}")
        
        ocr_data = ocr_result['data']
        extracted_text = ocr_data['text']
        
        if not extracted_text.strip():
            return self.prepare_response({
                'ocr_result': ocr_data,
                'llm_result': None,
                'warning': 'No text extracted by OCR'
            })
        
        # Step 2: Process extracted text with LLM
        enhanced_prompt = self._enhance_prompt(prompt, extracted_text, ocr_data)
        
        # Create a text-based request for LLM
        llm_result = self.llm_processor.process_text(
            extracted_text, 
            model, 
            enhanced_prompt, 
            schema,
            llm_parameters
        )
        
        # Combine results
        combined_result = {
            'ocr_result': ocr_data,
            'llm_result': llm_result['data'] if llm_result['success'] else None,
            'llm_error': llm_result.get('error'),
            'extraction_method': 'hybrid',
            'confidence_score': self._calculate_combined_confidence(ocr_data, llm_result)
        }
        
        return self.prepare_response(combined_result)
    
    def _enhance_prompt(self, base_prompt: str, extracted_text: str, ocr_data: Dict) -> str:
        """Enhance prompt with OCR context"""
        confidence = ocr_data.get('confidence', 0)
        
        enhanced = f"{base_prompt}\n\n"
        enhanced += f"The following text was extracted from an image using OCR "
        enhanced += f"(confidence: {confidence:.1f}%):\n\n"
        enhanced += f"{extracted_text}\n\n"
        
        if confidence < 70:
            enhanced += "Note: The OCR confidence is relatively low, so some text might be inaccurate. "
            enhanced += "Please use your best judgment to interpret and correct any obvious errors.\n\n"
        
        enhanced += "Based on this extracted text, please provide the requested information."
        
        return enhanced
    
    def _calculate_combined_confidence(self, ocr_data: Dict, llm_result: Dict) -> float:
        """Calculate combined confidence score"""
        ocr_confidence = ocr_data.get('confidence', 0) / 100.0
        
        # Base confidence on OCR quality
        confidence = ocr_confidence * 0.7
        
        # Boost confidence if LLM processing was successful
        if llm_result.get('success'):
            confidence += 0.3
        
        return min(confidence * 100, 100)
    
    def process_with_fallback(self, image: Image.Image, language: str, 
                            vision_model: str, text_model: str, prompt: str,
                            schema: Optional[str] = None, llm_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Try vision model first, fall back to OCR+LLM if it fails
        """
        # Try direct vision processing first
        vision_result = self.llm_processor.process(image, vision_model, prompt, schema, llm_parameters)
        
        if vision_result['success']:
            return self.prepare_response({
                'method': 'direct_vision',
                'result': vision_result['data']
            })
        
        # Fall back to hybrid approach
        hybrid_result = self.process(image, language, text_model, prompt, schema, llm_parameters)
        
        if hybrid_result['success']:
            result_data = hybrid_result['data']
            result_data['method'] = 'hybrid_fallback'
            result_data['vision_error'] = vision_result.get('error')
            return self.prepare_response(result_data)
        
        return self.prepare_response(None, 
            f"Both methods failed. Vision: {vision_result.get('error')}, "
            f"Hybrid: {hybrid_result.get('error')}")
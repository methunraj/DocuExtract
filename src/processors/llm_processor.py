import json
import tempfile
import base64
from typing import Dict, Any, Optional
from PIL import Image
import ollama
import requests
from io import BytesIO
from .base_processor import BaseProcessor

class LLMProcessor(BaseProcessor):
    """Processor for LLM-based image analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get('llm', {}).get('endpoint', 'http://localhost:11434')
        self.available_models = self._get_available_models()
    
    def _get_available_models(self) -> list:
        """Get list of available models from Ollama"""
        try:
            response = ollama.list()
            # Handle both dict response and object response
            if hasattr(response, 'models'):
                # Object response from newer ollama library
                # The attribute is 'model', not 'name'
                return [model.model for model in response.models]
            elif isinstance(response, dict) and 'models' in response:
                # Dict response
                return [model['name'] for model in response.get('models', [])]
            else:
                # Try direct API call as fallback
                import requests
                api_response = requests.get(f"{self.endpoint}/api/tags")
                if api_response.status_code == 200:
                    data = api_response.json()
                    return [model['name'] for model in data.get('models', [])]
                return []
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    def process(self, image: Image.Image, model: str, prompt: str, 
                schema: Optional[str] = None, llm_parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Process image using LLM with vision capabilities
        
        Args:
            image: PIL Image to process
            model: Name of the LLM model to use
            prompt: Prompt to guide the extraction
            schema: Optional JSON schema for structured output
            llm_parameters: Optional LLM parameters for fine-tuning
            
        Returns:
            Dictionary with processing results
        """
        self.validate_input(image)
        
        # Validate model (vision capability required for image processing)
        if not self._validate_model(model, require_vision=True):
            return self.prepare_response(None, f"Model '{model}' not found or not vision-capable")
        
        try:
            # Convert image to base64
            image_base64 = self._image_to_base64(image)
            
            # Prepare request
            request_params = {
                'model': model,
                'prompt': prompt,
                'images': [image_base64],
                'stream': False  # Disable streaming for easier response handling
            }
            
            # Add LLM parameters if provided
            if llm_parameters:
                options = {}
                for param in ['temperature', 'top_p', 'top_k', 'num_ctx', 'num_predict']:
                    if param in llm_parameters:
                        options[param] = llm_parameters[param]
                if options:
                    request_params['options'] = options
            
            # Add schema if provided
            if schema:
                try:
                    schema_dict = json.loads(schema)
                    request_params['format'] = 'json'
                    # Add schema to prompt for better compliance
                    request_params['prompt'] = f"{prompt}\n\nPlease format your response according to this JSON schema:\n{json.dumps(schema_dict, indent=2)}"
                except json.JSONDecodeError:
                    return self.prepare_response(None, "Invalid JSON schema provided")
            
            # Call Ollama
            response = ollama.generate(**request_params)
            
            # Process response
            result_text = response.get('response', '')
            
            if schema:
                # Try to parse as JSON
                try:
                    result_data = json.loads(result_text)
                    return self.prepare_response(result_data)
                except json.JSONDecodeError:
                    # Return raw text if JSON parsing fails
                    return self.prepare_response({
                        'raw_response': result_text,
                        'warning': 'Failed to parse response as JSON'
                    })
            else:
                return self.prepare_response({'text': result_text})
            
        except Exception as e:
            return self.prepare_response(None, f"LLM processing failed: {str(e)}")
    
    def _validate_model(self, model: str, require_vision: bool = True) -> bool:
        """Validate if model exists and has required capabilities"""
        if model not in self.available_models:
            return False
        
        if require_vision:
            # Check if model is vision-capable
            vision_models = [m['name'] for m in self.config.get('llm', {}).get('models', []) 
                            if m.get('type') == 'vision']
            return model in vision_models
        else:
            # For text-only processing, any model is acceptable
            return True
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def process_text(self, text: str, model: str, prompt: str, 
                     schema: Optional[str] = None, llm_parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Process text using LLM without vision capabilities
        
        Args:
            text: Text to process
            model: Name of the LLM model to use
            prompt: Prompt to guide the processing
            schema: Optional JSON schema for structured output
            llm_parameters: Optional LLM parameters for fine-tuning
            
        Returns:
            Dictionary with processing results
        """
        # Validate model (vision not required for text processing)
        if not self._validate_model(model, require_vision=False):
            return self.prepare_response(None, f"Model '{model}' not found")
        
        try:
            # Prepare request with text in prompt
            full_prompt = f"{prompt}\n\nText to process:\n{text}"
            
            request_params = {
                'model': model,
                'prompt': full_prompt,
                'stream': False  # Disable streaming for easier response handling
            }
            
            # Add LLM parameters if provided
            if llm_parameters:
                options = {}
                for param in ['temperature', 'top_p', 'top_k', 'num_ctx', 'num_predict']:
                    if param in llm_parameters:
                        options[param] = llm_parameters[param]
                if options:
                    request_params['options'] = options
            
            # Add schema if provided
            if schema:
                try:
                    schema_dict = json.loads(schema)
                    request_params['format'] = 'json'
                    # Add schema to prompt for better compliance
                    request_params['prompt'] = f"{full_prompt}\n\nPlease format your response according to this JSON schema:\n{json.dumps(schema_dict, indent=2)}"
                except json.JSONDecodeError:
                    return self.prepare_response(None, "Invalid JSON schema provided")
            
            # Call Ollama
            response = ollama.generate(**request_params)
            
            # Process response
            result_text = response.get('response', '')
            
            if schema:
                # Try to parse as JSON
                try:
                    result_data = json.loads(result_text)
                    return self.prepare_response(result_data)
                except json.JSONDecodeError:
                    # Return raw text if JSON parsing fails
                    return self.prepare_response({
                        'raw_response': result_text,
                        'warning': 'Failed to parse response as JSON'
                    })
            else:
                return self.prepare_response({'text': result_text})
            
        except Exception as e:
            return self.prepare_response(None, f"LLM text processing failed: {str(e)}")
    
    def batch_process(self, images: list, model: str, prompt: str, 
                     schema: Optional[str] = None, llm_parameters: Optional[Dict[str, Any]] = None, **kwargs) -> list:
        """Process multiple images"""
        results = []
        
        for idx, image in enumerate(images):
            result = self.process(image, model, prompt, schema, llm_parameters, **kwargs)
            result['image_index'] = idx
            results.append(result)
        
        return results
    
    def batch_process_text(self, texts: list, model: str, prompt: str, 
                          schema: Optional[str] = None, llm_parameters: Optional[Dict[str, Any]] = None, **kwargs) -> list:
        """Process multiple text inputs"""
        results = []
        
        for idx, text in enumerate(texts):
            result = self.process_text(text, model, prompt, schema, llm_parameters, **kwargs)
            result['text_index'] = idx
            results.append(result)
        
        return results
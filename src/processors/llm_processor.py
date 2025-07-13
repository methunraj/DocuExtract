import json
import tempfile
from typing import Dict, Any, Optional
from PIL import Image
import ollama
import requests
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
            llm_parameters: Optional LLM parameters for fine-tuning behavior
            
        Returns:
            Dictionary with processing results
        """
        self.validate_input(image)
        
        # Validate model
        if not self._validate_model(model):
            return self.prepare_response(None, f"Model '{model}' not found or not vision-capable")
        
        # Save image temporarily
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            image.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Prepare request
            request_params = {
                'model': model,
                'prompt': prompt,
                'images': [temp_path]
            }
            
            # Add LLM parameters as options if provided
            if llm_parameters:
                # Prepare options dictionary for ollama
                options = {}
                if 'temperature' in llm_parameters:
                    options['temperature'] = llm_parameters['temperature']
                if 'top_p' in llm_parameters:
                    options['top_p'] = llm_parameters['top_p']
                if 'top_k' in llm_parameters:
                    options['top_k'] = llm_parameters['top_k']
                if 'num_ctx' in llm_parameters:
                    options['num_ctx'] = llm_parameters['num_ctx']
                if 'num_predict' in llm_parameters:
                    options['num_predict'] = llm_parameters['num_predict']
                
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
        finally:
            # Clean up temp file
            import os
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def _validate_model(self, model: str) -> bool:
        """Validate if model exists and is vision-capable"""
        if model not in self.available_models:
            return False
        
        # Check if model is vision-capable
        vision_models = [m['name'] for m in self.config.get('llm', {}).get('models', []) 
                        if m.get('type') == 'vision']
        
        return model in vision_models
    
    def batch_process(self, images: list, model: str, prompt: str, 
                     schema: Optional[str] = None, llm_parameters: Optional[Dict[str, Any]] = None, **kwargs) -> list:
        """Process multiple images"""
        results = []
        
        for idx, image in enumerate(images):
            result = self.process(image, model, prompt, schema, llm_parameters, **kwargs)
            result['image_index'] = idx
            results.append(result)
        
        return results
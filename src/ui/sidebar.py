import streamlit as st
from typing import Dict, Any, Tuple, Optional
from src.core.config import ConfigManager
from src.utils.validators import Validators

def create_sidebar(config_manager: ConfigManager) -> Dict[str, Any]:
    """Create and manage sidebar configuration UI"""
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Processing Mode Selection
        mode = st.radio(
            "Processing Mode",
            ["LLM-based", "Standard OCR", "OCR + LLM Extraction"],
            help="""
            • **LLM-based**: Direct image analysis using vision models
            • **Standard OCR**: Traditional text extraction
            • **OCR + LLM**: OCR followed by LLM structuring
            """
        )
        
        st.divider()
        
        # Model Selection based on mode
        selected_llm = None
        selected_language = None
        
        if mode in ["LLM-based", "OCR + LLM Extraction"]:
            st.subheader("🤖 LLM Configuration")
            
            # Get appropriate models
            if mode == "LLM-based":
                models = [m['name'] for m in config_manager.get_vision_models()]
                model_type = "Vision"
            else:
                models = [m['name'] for m in config_manager.get_text_models()]
                model_type = "Text"
            
            if models:
                selected_llm = st.selectbox(
                    f"{model_type} Model",
                    models,
                    index=0 if not config_manager.get_default_llm_model() 
                          else models.index(config_manager.get_default_llm_model()) 
                          if config_manager.get_default_llm_model() in models else 0,
                    help=f"Select {model_type.lower()} model for processing"
                )
            else:
                st.error(f"No {model_type.lower()} models configured")
        
        if mode in ["Standard OCR", "OCR + LLM Extraction"]:
            st.subheader("📝 OCR Configuration")
            
            languages = config_manager.get_ocr_languages()
            selected_language = st.selectbox(
                "OCR Language",
                languages,
                index=languages.index(config_manager.get_default_ocr_language()) 
                      if config_manager.get_default_ocr_language() in languages else 0,
                help="Select language for text extraction"
            )
        
        st.divider()
        
        # Output Format Selection
        st.subheader("📄 Output Format")
        
        output_formats = {
            "LLM-based": ["JSON", "XLSX"],
            "Standard OCR": ["JSON", "Markdown"],
            "OCR + LLM Extraction": ["JSON", "XLSX"]
        }
        
        output_format = st.selectbox(
            "Format",
            output_formats[mode],
            help="Select output file format"
        )
        
        st.divider()
        
        # Advanced Options
        with st.expander("🔧 Advanced Options", expanded=False):
            custom_prompt = None
            json_schema = None
            
            if mode in ["LLM-based", "OCR + LLM Extraction"]:
                st.subheader("Prompt Customization")
                
                default_prompts = {
                    "LLM-based": "Extract all relevant information from this image. Be thorough and structured.",
                    "OCR + LLM Extraction": "Extract and structure the key information from the provided text."
                }
                
                custom_prompt = st.text_area(
                    "Custom Prompt",
                    value=default_prompts[mode],
                    height=100,
                    help="Guide the LLM on what to extract"
                )
                
                st.subheader("JSON Schema (Optional)")
                
                schema_examples = {
                    "invoice": '''{
  "invoice_number": "string",
  "date": "string",
  "total": "number",
  "items": [{
    "description": "string",
    "amount": "number"
  }]
}''',
                    "form": '''{
  "name": "string",
  "email": "string",
  "phone": "string",
  "address": "string"
}'''
                }
                
                # Schema template selector
                template = st.selectbox(
                    "Schema Template",
                    ["None", "Invoice", "Form", "Custom"],
                    help="Select a template or create custom schema"
                )
                
                if template == "Invoice":
                    json_schema = st.text_area(
                        "JSON Schema",
                        value=schema_examples["invoice"],
                        height=150
                    )
                elif template == "Form":
                    json_schema = st.text_area(
                        "JSON Schema",
                        value=schema_examples["form"],
                        height=150
                    )
                elif template == "Custom":
                    json_schema = st.text_area(
                        "JSON Schema",
                        value="",
                        height=150,
                        placeholder="Enter your JSON schema here..."
                    )
                else:
                    json_schema = ""
                
                # Validate schema
                if json_schema:
                    is_valid, error = Validators.validate_json_schema(json_schema)
                    if not is_valid:
                        st.error(f"❌ {error}")
            
            st.subheader("Preprocessing")
            
            preprocessing_mode = st.radio(
                "Preprocessing Mode",
                ["Automatic", "Manual", "Disabled"],
                index=0 if config_manager.is_preprocessing_enabled_by_default() else 2,
                help="""
                • **Automatic**: AI detects and applies optimal preprocessing
                • **Manual**: Choose specific preprocessing steps
                • **Disabled**: No preprocessing applied
                """
            )
            
            manual_steps = []
            if preprocessing_mode == "Manual":
                st.write("Select preprocessing steps:")
                
                available_steps = [
                    ("Grayscale", "grayscale"),
                    ("Auto Brightness", "brightness"),
                    ("Enhance Contrast", "contrast"),
                    ("Denoise", "denoise"),
                    ("Sharpen", "sharpen"),
                    ("Threshold", "threshold"),
                    ("Invert Colors", "invert")
                ]
                
                for label, step in available_steps:
                    if st.checkbox(label, key=f"prep_{step}"):
                        manual_steps.append(step)
            
            # Batch Processing Options
            st.subheader("Batch Processing")
            
            batch_options = {
                "parallel_processing": st.checkbox(
                    "Enable Parallel Processing",
                    value=False,
                    help="Process multiple images simultaneously (faster but uses more resources)"
                ),
                "save_individual_results": st.checkbox(
                    "Save Individual Results",
                    value=True,
                    help="Save results for each image separately"
                ),
                "stop_on_error": st.checkbox(
                    "Stop on Error",
                    value=False,
                    help="Stop processing if an error occurs"
                )
            }
        
        # Configuration summary
        st.divider()
        st.subheader("📋 Configuration Summary")
        
        config_summary = {
            "mode": mode,
            "llm_model": selected_llm,
            "ocr_language": selected_language,
            "output_format": output_format,
            "preprocessing": preprocessing_mode,
            "custom_prompt": custom_prompt if mode in ["LLM-based", "OCR + LLM Extraction"] else None,
            "json_schema": json_schema if mode in ["LLM-based", "OCR + LLM Extraction"] else None,
            "manual_preprocessing_steps": manual_steps if preprocessing_mode == "Manual" else [],
            "batch_options": batch_options if 'batch_options' in locals() else {}
        }
        
        # Display summary
        with st.container():
            st.caption(f"**Mode:** {mode}")
            if selected_llm:
                st.caption(f"**Model:** {selected_llm}")
            if selected_language:
                st.caption(f"**Language:** {selected_language}")
            st.caption(f"**Output:** {output_format}")
            st.caption(f"**Preprocessing:** {preprocessing_mode}")
        
        return config_summary
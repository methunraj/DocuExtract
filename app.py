import streamlit as st
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.core.config import ConfigManager
from src.preprocessing import SmartPreprocessor
from src.processors import LLMProcessor, OCRProcessor, HybridProcessor
from src.ui import create_sidebar, create_main_area, display_results
from src.utils.file_handler import FileHandler
from src.utils.image_utils import ImageUtils
from PIL import Image
from pdf2image import convert_from_path

# Page configuration
st.set_page_config(
    page_title="DocuExtract",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = None

def process_single_image(image_path: str, image: Image.Image, config: dict, 
                        preprocessor: SmartPreprocessor, processors: dict) -> dict:
    """Process a single image based on configuration"""
    
    result = {
        'filename': os.path.basename(image_path),
        'mode': config['mode']
    }
    
    try:
        # Preprocessing
        if config['preprocessing'] == "Automatic":
            processed_image, processing_info = preprocessor.auto_preprocess(image)
            result['processing_info'] = processing_info
        elif config['preprocessing'] == "Manual" and config['manual_preprocessing_steps']:
            processed_image, processing_info = preprocessor.manual_preprocess(
                image, config['manual_preprocessing_steps']
            )
            result['processing_info'] = processing_info
        else:
            processed_image = image
        
        # Show preprocessing preview if requested
        if st.session_state.get('show_preprocessing_preview', False):
            col1, col2 = st.columns(2)
            with col1:
                st.image(image, caption="Original", use_container_width=True)
            with col2:
                st.image(processed_image, caption="Processed", use_container_width=True)
        
        # Process based on mode
        if config['mode'] == "LLM-based":
            processor_result = processors['llm'].process(
                processed_image,
                config['llm_model'],
                config['custom_prompt'],
                config['json_schema']
            )
            
        elif config['mode'] == "Standard OCR":
            processor_result = processors['ocr'].process(
                processed_image,
                config['ocr_language']
            )
            
        else:  # OCR + LLM Extraction
            processor_result = processors['hybrid'].process(
                processed_image,
                config['ocr_language'],
                config['llm_model'],
                config['custom_prompt'],
                config['json_schema']
            )
        
        # Merge processor results
        if processor_result['success']:
            result.update(processor_result['data'])
        else:
            result['error'] = processor_result['error']
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """Main application function"""
    
    # Initialize session state
    initialize_session_state()
    
    # Title and description
    st.title("🔍 DocuExtract")
    st.markdown("Extract text and structured data from your documents with ease.")
    
    # Load configuration
    try:
        if st.session_state.config_manager is None:
            st.session_state.config_manager = ConfigManager()
        config_manager = st.session_state.config_manager
    except Exception as e:
        st.error(f"Failed to load configuration: {str(e)}")
        st.stop()
    
    # Create sidebar and get configuration
    config = create_sidebar(config_manager)
    
    # Create main input area
    image_files, temp_dir = create_main_area(config_manager)
    
    # Process button
    if image_files:
        st.divider()
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            process_button = st.button(
                "🚀 Run Extraction",
                type="primary",
                disabled=st.session_state.processing,
                use_container_width=True
            )
        
        if process_button:
            st.session_state.processing = True
            st.session_state.results = []
            
            # Initialize processors
            preprocessor = SmartPreprocessor(config_manager.config)
            processors = {
                'llm': LLMProcessor(config_manager.config),
                'ocr': OCRProcessor(config_manager.config),
                'hybrid': HybridProcessor(config_manager.config)
            }
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            # Process images
            for idx, image_path in enumerate(image_files):
                status_text.text(f"Processing {idx + 1}/{len(image_files)}: {os.path.basename(image_path)}")
                
                try:
                    # Handle PDF files
                    if image_path.lower().endswith('.pdf'):
                        pdf_pages = FileHandler.process_pdf(image_path, temp_dir)
                        
                        for page_path, page_num in pdf_pages:
                            page_image = Image.open(page_path)
                            page_result = process_single_image(
                                f"{os.path.basename(image_path)}_page_{page_num}",
                                page_image,
                                config,
                                preprocessor,
                                processors
                            )
                            results.append(page_result)
                    else:
                        # Regular image file
                        image = Image.open(image_path)
                        result = process_single_image(
                            image_path,
                            image,
                            config,
                            preprocessor,
                            processors
                        )
                        results.append(result)
                
                except Exception as e:
                    results.append({
                        'filename': os.path.basename(image_path),
                        'error': str(e),
                        'mode': config['mode']
                    })
                
                # Update progress
                progress = (idx + 1) / len(image_files)
                progress_bar.progress(progress)
                
                # Stop on error if configured
                if config.get('batch_options', {}).get('stop_on_error', False):
                    if results[-1].get('error'):
                        status_text.text(f"Stopped due to error in {os.path.basename(image_path)}")
                        break
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Store results in session state
            st.session_state.results = results
            st.session_state.processing = False
            
            # Show completion message
            st.success(f"✅ Processing complete! Processed {len(results)} items.")
    
    # Display results if available
    if st.session_state.results:
        st.divider()
        display_results(st.session_state.results, config)
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>DocuExtract | Powered by Tesseract & Ollama</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
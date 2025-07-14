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
    page_title="OCR & Data Extraction Tool",
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
            try:
                col1, col2 = st.columns(2)
                with col1:
                    st.image(image, caption="Original")
                with col2:
                    st.image(processed_image, caption="Processed")
            except Exception as e:
                st.info("Preview not available for this image type")
        
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
    st.title("🔍 OCR & Data Extraction Tool")
    st.markdown("Extract text and structured data from images using OCR and LLMs")
    
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
            
            # Batch processing with monitoring
            import time
            import os
            
            def get_memory_usage():
                try:
                    import psutil
                    process = psutil.Process()
                    return process.memory_info().rss / 1024 / 1024  # MB
                except ImportError:
                    return 0
            
            # Check batch limits
            max_batch_size = config.get('batch_options', {}).get('max_batch_size', 100)
            warning_threshold = 50
            
            if len(image_files) > max_batch_size:
                st.error(f"Batch size ({len(image_files)}) exceeds limit of {max_batch_size}. Use smaller batches or adjust configuration.")
                return
                
            if len(image_files) > warning_threshold:
                st.warning(f"Processing {len(image_files)} images may consume significant memory and time.")
            
            # Memory monitoring
            start_time = time.time()
            initial_memory = get_memory_usage()
            
            enable_parallel = config.get('batch_options', {}).get('parallel_processing', False)
            max_workers = min(config.get('batch_options', {}).get('max_workers', 4), os.cpu_count() or 4)
            
            if enable_parallel and len(image_files) > 1:
                # Parallel processing
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_path = {}
                    
                    for image_path in image_files:
                        if image_path.lower().endswith('.pdf'):
                            pdf_pages = FileHandler.process_pdf(image_path, temp_dir)
                            for page_path, page_num in pdf_pages:
                                future = executor.submit(
                                    process_single_image,
                                    f"{os.path.basename(image_path)}_page_{page_num}",
                                    Image.open(page_path),
                                    config,
                                    preprocessor,
                                    processors
                                )
                                future_to_path[future] = (f"{os.path.basename(image_path)}_page_{page_num}", image_path)
                        else:
                            future = executor.submit(
                                process_single_image,
                                image_path,
                                Image.open(image_path),
                                config,
                                preprocessor,
                                processors
                            )
                            future_to_path[future] = (os.path.basename(image_path), image_path)
                    
                    for idx, future in enumerate(as_completed(future_to_path)):
                        progress = (idx + 1) / len(future_to_path)
                        progress_bar.progress(progress)
                        filename, original_path = future_to_path[future]
                        status_text.text(f"Processing {idx + 1}/{len(future_to_path)}: {filename}")
                        
                        try:
                            result = future.result(timeout=60)
                            results.append(result)
                            
                            if config.get('batch_options', {}).get('stop_on_error', False) and result.get('error'):
                                status_text.text(f"Stopped due to error in {filename}")
                                break
                                
                        except Exception as e:
                            results.append({
                                'filename': filename,
                                'error': str(e),
                                'mode': config['mode']
                            })
                            
                        current_memory = get_memory_usage()
                        if current_memory > initial_memory * 2:
                            st.warning(f"High memory usage: {current_memory:.1f} MB")
            else:
                # Serial processing with monitoring
                for idx, image_path in enumerate(image_files):
                    current_memory = get_memory_usage()
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
                            image = image.convert('RGB')  # Ensure consistent format
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
                    
                    # Memory monitoring
                    if current_memory > initial_memory * 1.5:
                        st.warning(f"High memory usage: {current_memory:.1f} MB")
                    
                    # Stop on error if configured
                    if config.get('batch_options', {}).get('stop_on_error', False):
                        if results and results[-1].get('error'):
                            status_text.text(f"Stopped due to error in {os.path.basename(image_path)}")
                            break
                    
                    # Small delay to prevent overwhelming the system
                    time.sleep(0.1)
            
            # Final summary
            processing_time = time.time() - start_time
            final_memory = get_memory_usage()
            
            st.info(f"Batch processing completed: {len(results)}/{len(image_files)} successful. "
                   f"Time: {processing_time:.1f}s" + 
                   (f", Memory increased by {final_memory - initial_memory:.1f} MB" if initial_memory > 0 else ""))
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Store results in session state
            st.session_state.results = results
            st.session_state.processing = False
            
            # Show completion message
            st.success(f"✅ Processing complete! Processed {len(results)} items.")
            
            # Cleanup temporary files
            if temp_dir and os.path.exists(temp_dir):
                try:
                    FileHandler.cleanup_temp_files(temp_dir)
                    st.success("🗑️ Cleaned up temporary files")
                except Exception as e:
                    st.warning(f"Failed to cleanup temporary files: {e}")
    
    # Display results if available
    if st.session_state.results:
        st.divider()
        display_results(st.session_state.results, config)
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>OCR & Data Extraction Tool | Powered by Tesseract & Ollama</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
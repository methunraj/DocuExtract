import streamlit as st
from typing import List, Optional, Tuple
import os
from src.utils.file_handler import FileHandler
from src.utils.validators import Validators
from src.core.config import ConfigManager

def create_main_area(config_manager: ConfigManager) -> Tuple[List[str], str]:
    """Create main input area and return list of image files and temp directory"""
    
    st.header("📥 Input")
    
    # Input method selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        input_method = st.radio(
            "Input Method",
            ["Upload Images", "Folder Path"],
            help="Choose how to provide images"
        )
    
    image_files = []
    temp_dir = str(config_manager.get_temp_dir())
    
    with col2:
        if input_method == "Upload Images":
            # File uploader
            uploaded_files = st.file_uploader(
                "Choose images",
                type=config_manager.get_supported_formats(),
                accept_multiple_files=True,
                help="Select one or more image files (max 2GB per file)"
            )
            
            if uploaded_files:
                # Display upload summary
                st.success(f"✅ {len(uploaded_files)} file(s) selected")
                
                # Save uploaded files
                with st.spinner("Processing uploads..."):
                    for uploaded_file in uploaded_files:
                        try:
                            temp_path = FileHandler.save_uploaded_file(uploaded_file, temp_dir)
                            image_files.append(temp_path)
                        except Exception as e:
                            st.error(f"Failed to process {uploaded_file.name}: {str(e)}")
                
                # Show file details
                with st.expander("📋 File Details", expanded=False):
                    for i, uploaded_file in enumerate(uploaded_files):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.text(uploaded_file.name)
                        with col2:
                            st.text(f"{uploaded_file.size / 1024:.1f} KB")
                        with col3:
                            st.text(uploaded_file.type)
        
        else:  # Folder Path
            folder_path = st.text_input(
                "Enter folder path",
                placeholder="/path/to/your/images",
                help="Provide absolute path to folder containing images"
            )
            
            if folder_path:
                # Validate folder
                is_valid, error = Validators.validate_folder_path(folder_path)
                
                if is_valid:
                    try:
                        # Get images from folder
                        max_images = config_manager.get_max_images()
                        found_files = FileHandler.get_images_from_folder(folder_path, max_images)
                        
                        if found_files:
                            image_files = found_files
                            st.success(f"✅ Found {len(image_files)} image(s)")
                            
                            if len(found_files) == max_images:
                                st.warning(f"⚠️ Limited to first {max_images} images")
                            
                            # Show file list
                            with st.expander("📋 Files Found", expanded=False):
                                for file_path in image_files[:10]:  # Show first 10
                                    st.text(f"• {os.path.basename(file_path)}")
                                if len(image_files) > 10:
                                    st.text(f"... and {len(image_files) - 10} more")
                        else:
                            st.warning("No image files found in the specified folder")
                    
                    except Exception as e:
                        st.error(f"Error reading folder: {str(e)}")
                else:
                    st.error(f"❌ {error}")
    
    # Preview section
    if image_files:
        st.divider()
        st.subheader("👁️ Preview")
        
        # Limit preview to first 5 images
        preview_files = image_files[:5]
        cols = st.columns(min(len(preview_files), 5))
        
        for idx, (col, file_path) in enumerate(zip(cols, preview_files)):
            with col:
                try:
                    from PIL import Image
                    img = Image.open(file_path)
                    
                    # Create thumbnail
                    from src.utils.image_utils import ImageUtils
                    thumbnail = ImageUtils.create_thumbnail(img, size=(150, 150))
                    
                    st.image(thumbnail, caption=os.path.basename(file_path))
                    
                    # Show image info
                    st.caption(f"{img.width}×{img.height}")
                    
                except Exception as e:
                    st.error(f"Preview error: {str(e)}")
        
        if len(image_files) > 5:
            st.info(f"Showing first 5 of {len(image_files)} images")
    
    # Processing options
    if image_files:
        st.divider()
        st.subheader("⚡ Processing Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Preprocessing preview option
            if st.checkbox("Show preprocessing preview", value=False):
                st.session_state['show_preprocessing_preview'] = True
            else:
                st.session_state['show_preprocessing_preview'] = False
        
        with col2:
            # Batch size for large sets
            if len(image_files) > 10:
                batch_size = st.slider(
                    "Batch size",
                    min_value=1,
                    max_value=min(50, len(image_files)),
                    value=min(10, len(image_files)),
                    help="Process images in smaller batches"
                )
                st.session_state['batch_size'] = batch_size
    
    return image_files, temp_dir
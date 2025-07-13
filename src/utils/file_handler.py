import os
import glob
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from pdf2image import convert_from_path
from PIL import Image

class FileHandler:
    """Utility class for file operations"""
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported image formats"""
        return ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'pdf']
    
    @staticmethod
    def get_images_from_folder(folder_path: str, max_images: Optional[int] = None) -> List[str]:
        """Get list of image files from folder"""
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        image_files = []
        supported_formats = FileHandler.get_supported_formats()
        
        for format_ext in supported_formats:
            # Search for both lowercase and uppercase extensions
            for pattern in [f"*.{format_ext}", f"*.{format_ext.upper()}"]:
                pattern_path = os.path.join(folder_path, pattern)
                found_files = glob.glob(pattern_path)
                image_files.extend(found_files)
        
        # Remove duplicates and sort
        image_files = sorted(list(set(image_files)))
        
        if max_images and len(image_files) > max_images:
            image_files = image_files[:max_images]
        
        return image_files
    
    @staticmethod
    def save_uploaded_file(uploaded_file, temp_dir: str) -> str:
        """Save uploaded file to temporary directory"""
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        return temp_path
    
    @staticmethod
    def process_pdf(pdf_path: str, output_dir: Optional[str] = None) -> List[Tuple[str, int]]:
        """Convert PDF pages to images"""
        if not os.path.exists(pdf_path):
            raise ValueError(f"PDF file does not exist: {pdf_path}")
        
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        image_paths = []
        base_name = Path(pdf_path).stem
        
        for i, image in enumerate(images):
            page_num = i + 1
            image_path = os.path.join(output_dir, f"{base_name}_page_{page_num}.png")
            image.save(image_path, 'PNG')
            image_paths.append((image_path, page_num))
        
        return image_paths
    
    @staticmethod
    def load_image(file_path: str) -> Image.Image:
        """Load image from file path"""
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        try:
            return Image.open(file_path)
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
    
    @staticmethod
    def create_temp_directory() -> str:
        """Create a temporary directory"""
        return tempfile.mkdtemp()
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str):
        """Clean up temporary files and directory"""
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """Get information about a file"""
        if not os.path.exists(file_path):
            return {'exists': False}
        
        stat = os.stat(file_path)
        
        return {
            'exists': True,
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'extension': Path(file_path).suffix.lower(),
            'name': Path(file_path).name,
            'stem': Path(file_path).stem
        }
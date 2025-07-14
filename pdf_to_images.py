#!/usr/bin/env python3
"""
PDF to Images Converter
Converts a PDF file into individual page images using PyMuPDF and pdf2image libraries.
"""

import os
import sys
import argparse
from pathlib import Path
import tempfile

def convert_pdf_to_images(pdf_path, output_dir=None, dpi=200, image_format='PNG'):
    """
    Convert PDF to individual page images
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save images (default: pdf_name_images)
        dpi (int): Resolution for image conversion (default: 200)
        image_format (str): Output image format (PNG, JPG, etc.)
    
    Returns:
        list: List of created image file paths
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Create output directory
    if output_dir is None:
        pdf_name = Path(pdf_path).stem
        output_dir = f"{pdf_name}_images"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Get PDF filename for naming images
    base_name = Path(pdf_path).stem
    image_paths = []
    
    print(f"📄 Converting PDF: {pdf_path}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎯 DPI: {dpi}, Format: {image_format}")
    
    # Try PyMuPDF first (better cross-platform support)
    try:
        import fitz  # PyMuPDF
        print("🔧 Using PyMuPDF for conversion...")
        
        # Open PDF
        pdf_document = fitz.open(pdf_path)
        total_pages = pdf_document.page_count
        print(f"📊 Total pages: {total_pages}")
        
        # Convert each page
        for page_num in range(total_pages):
            page = pdf_document.load_page(page_num)
            
            # Create transformation matrix for DPI
            zoom = dpi / 72.0  # 72 DPI is default
            matrix = fitz.Matrix(zoom, zoom)
            
            # Render page to image
            pix = page.get_pixmap(matrix=matrix)
            
            # Save image
            image_filename = f"{base_name}_page_{page_num + 1:03d}.{image_format.lower()}"
            image_path = os.path.join(output_dir, image_filename)
            
            pix.save(image_path)
            image_paths.append(image_path)
            
            print(f"✅ Page {page_num + 1}/{total_pages}: {image_filename}")
            
            # Free memory
            pix = None
        
        pdf_document.close()
        
    except ImportError:
        print("⚠️  PyMuPDF not available, trying pdf2image...")
        
        # Fallback to pdf2image
        try:
            from pdf2image import convert_from_path
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=dpi)
            total_pages = len(images)
            print(f"📊 Total pages: {total_pages}")
            
            # Save each page
            for i, image in enumerate(images, 1):
                image_filename = f"{base_name}_page_{i:03d}.{image_format.upper()}"
                image_path = os.path.join(output_dir, image_filename)
                
                image.save(image_path, image_format.upper())
                image_paths.append(image_path)
                
                print(f"✅ Page {i}/{total_pages}: {image_filename}")
        
        except ImportError:
            raise RuntimeError(
                "Neither PyMuPDF nor pdf2image is available.\n"
                "Please install one of them:\n"
                "- pip install PyMuPDF (recommended)\n"
                "- pip install pdf2image (requires Poppler)"
            )
        except Exception as e:
            if "poppler" in str(e).lower():
                raise RuntimeError(
                    "pdf2image requires Poppler utilities.\n"
                    "Install Poppler:\n"
                    "- macOS: brew install poppler\n"
                    "- Ubuntu: sudo apt-get install poppler-utils\n"
                    "- Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/\n"
                    "Or use: pip install PyMuPDF (no external dependencies)"
                )
            else:
                raise e
    
    except Exception as e:
        raise RuntimeError(f"Error processing PDF: {str(e)}")
    
    print(f"🎉 Successfully converted {len(image_paths)} pages to images!")
    print(f"📁 Images saved in: {os.path.abspath(output_dir)}")
    
    return image_paths

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Convert PDF pages to individual images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_to_images.py document.pdf
  python pdf_to_images.py document.pdf -o my_images
  python pdf_to_images.py document.pdf --dpi 300 --format JPG
  python pdf_to_images.py document.pdf -o output --dpi 150 --format PNG
        """
    )
    
    parser.add_argument(
        'pdf_path',
        help='Path to the PDF file to convert'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output directory for images (default: {pdf_name}_images)',
        default=None
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        help='Resolution for image conversion (default: 200)',
        default=200
    )
    
    parser.add_argument(
        '--format',
        choices=['PNG', 'JPG', 'JPEG', 'BMP', 'TIFF'],
        help='Output image format (default: PNG)',
        default='PNG'
    )
    
    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Only list what would be created, don\'t actually convert'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate input
        if not os.path.exists(args.pdf_path):
            print(f"❌ Error: PDF file not found: {args.pdf_path}")
            sys.exit(1)
        
        if not args.pdf_path.lower().endswith('.pdf'):
            print(f"❌ Error: File must be a PDF: {args.pdf_path}")
            sys.exit(1)
        
        # List-only mode
        if args.list_only:
            print("🔍 List-only mode - showing what would be created:")
            # Quick page count
            try:
                import fitz
                pdf_doc = fitz.open(args.pdf_path)
                page_count = pdf_doc.page_count
                pdf_doc.close()
            except:
                from pdf2image import convert_from_path
                images = convert_from_path(args.pdf_path, dpi=50)  # Low DPI for quick count
                page_count = len(images)
            
            output_dir = args.output or f"{Path(args.pdf_path).stem}_images"
            base_name = Path(args.pdf_path).stem
            
            print(f"📄 PDF: {args.pdf_path}")
            print(f"📁 Output directory: {output_dir}")
            print(f"📊 Total pages: {page_count}")
            print(f"🎯 DPI: {args.dpi}, Format: {args.format}")
            print("\nFiles that would be created:")
            for i in range(1, page_count + 1):
                filename = f"{base_name}_page_{i:03d}.{args.format.lower()}"
                print(f"  {os.path.join(output_dir, filename)}")
            sys.exit(0)
        
        # Convert PDF to images
        image_paths = convert_pdf_to_images(
            args.pdf_path,
            args.output,
            args.dpi,
            args.format
        )
        
        print(f"\n📝 Summary:")
        print(f"✅ Converted {len(image_paths)} pages")
        print(f"📁 Location: {os.path.abspath(args.output or f'{Path(args.pdf_path).stem}_images')}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Conversion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
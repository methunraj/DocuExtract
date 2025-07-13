# OCR & Data Extraction Tool

A powerful, modular Streamlit application for performing Optical Character Recognition (OCR) and structured data extraction from images using local LLMs and traditional OCR engines.

## 🚀 Features

### Core Capabilities
- **Multiple Processing Modes**:
  - **LLM-based**: Direct image processing using vision-capable LLMs (e.g., LLaVA)
  - **Standard OCR**: Traditional text extraction using Tesseract
  - **OCR + LLM Extraction**: OCR followed by LLM-based structured extraction

- **Smart Preprocessing with Auto-Detection**:
  - Automatic image quality analysis
  - Intelligent preprocessing recommendations
  - Automatic skew correction
  - Adaptive contrast and brightness adjustment
  - Smart denoising and sharpening
  - Manual override options

- **Flexible Input Options**:
  - Single or multiple image uploads
  - Folder path processing
  - Support for JPG, PNG, BMP, TIFF, and PDF formats
  - Batch processing with progress tracking

- **Multiple Output Formats**:
  - JSON (all modes)
  - Markdown (Standard OCR only)
  - XLSX with multi-sheet support (LLM-based modes)

- **Advanced Features**:
  - Custom prompts for LLM guidance
  - JSON schema enforcement for structured output
  - Preprocessing preview and comparison
  - Detailed processing reports
  - Configurable via YAML without code changes

## 📁 Project Structure

```
Simple OCR Pipeline/
├── app.py                 # Main Streamlit application
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .gitignore          # Git ignore file
└── src/                # Source code modules
    ├── __init__.py
    ├── core/           # Core functionality
    │   ├── __init__.py
    │   └── config.py   # Configuration management
    ├── preprocessing/  # Image preprocessing
    │   ├── __init__.py
    │   ├── image_analyzer.py    # Image quality analysis
    │   └── smart_preprocessor.py # Preprocessing logic
    ├── processors/     # Processing engines
    │   ├── __init__.py
    │   ├── base_processor.py    # Base processor class
    │   ├── llm_processor.py     # LLM processing
    │   ├── ocr_processor.py     # OCR processing
    │   └── hybrid_processor.py  # Hybrid processing
    ├── output/         # Output handlers
    │   ├── __init__.py
    │   ├── base_handler.py      # Base output handler
    │   ├── json_handler.py      # JSON output
    │   ├── markdown_handler.py  # Markdown output
    │   └── excel_handler.py     # Excel output
    ├── ui/             # UI components
    │   ├── __init__.py
    │   ├── sidebar.py           # Sidebar configuration
    │   ├── main_area.py         # Main input area
    │   └── results_display.py   # Results display
    └── utils/          # Utility functions
        ├── __init__.py
        ├── file_handler.py      # File operations
        ├── image_utils.py       # Image utilities
        └── validators.py        # Input validation
```

## 🛠️ Prerequisites

### System Requirements

1. **Python 3.8+**

2. **Tesseract OCR**:
   ```bash
   # macOS
   brew install tesseract
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # Windows
   # Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Ollama** (for LLM inference):
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull required models
   ollama pull llava  # For vision capabilities
   ollama pull llama2  # For text processing
   ollama pull mistral  # Alternative text model
   ```

4. **Poppler** (for PDF support):
   ```bash
   # macOS
   brew install poppler
   
   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   
   # Windows
   # Download from: https://blog.alivate.com.au/poppler-windows/
   ```

### Additional Language Support for OCR

To use languages other than English with Tesseract:
```bash
# macOS
brew install tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr-[lang]
# Example: sudo apt-get install tesseract-ocr-fra tesseract-ocr-deu
```

## 📦 Installation

1. Clone or download this repository:
   ```bash
   cd "Simple OCR Pipeline"
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **LLM Models**: Add or remove models available in Ollama
- **OCR Languages**: Configure supported Tesseract languages
- **Preprocessing**: Set automatic preprocessing parameters
- **Limits**: Adjust maximum images for batch processing

### Key Configuration Options:

```yaml
preprocessing:
  enabled_by_default: true
  auto_detect: true
  quality_thresholds:
    blur_threshold: 100
    contrast_threshold: 40
    brightness_min: 80
    brightness_max: 200
```

## 🚀 Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. Open your browser to `http://localhost:8501`

3. Configure your extraction:
   - Select processing mode
   - Choose models/languages
   - Set output format
   - Configure preprocessing (automatic/manual/disabled)
   - (Optional) Customize prompts and schemas

4. Provide input:
   - Upload images directly, or
   - Enter a folder path containing images

5. Click "Run Extraction" and download results

## 🔧 Processing Modes Explained

### LLM-based Mode
- Uses vision-capable LLMs to directly analyze images
- Best for: Complex layouts, handwriting, mixed content
- Requires: Vision model (e.g., LLaVA)

### Standard OCR Mode
- Traditional text extraction without interpretation
- Best for: Simple text extraction, high-quality scans
- Output: Raw text in JSON or Markdown format

### OCR + LLM Extraction Mode
- First extracts text, then uses LLM for structuring
- Best for: When you need both raw text and structured data
- Useful for: Forms, invoices, documents with specific schemas

## 🎯 Smart Preprocessing

The application now includes intelligent preprocessing with automatic detection:

### Automatic Mode
- Analyzes image quality metrics
- Detects issues like blur, low contrast, skew
- Applies only necessary corrections
- Shows before/after preview

### Manual Mode
- Choose specific preprocessing steps
- Available options:
  - Grayscale conversion
  - Brightness/contrast adjustment
  - Denoising
  - Sharpening
  - Skew correction
  - Adaptive thresholding

### Quality Metrics
- Blur detection (Laplacian variance)
- Contrast measurement
- Brightness analysis
- Noise estimation
- Text confidence scoring

## 📋 Custom Schemas

For structured extraction, provide a JSON schema:
```json
{
  "invoice_number": "string",
  "date": "string",
  "total_amount": "number",
  "items": [
    {
      "description": "string",
      "quantity": "number",
      "price": "number"
    }
  ]
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"Tesseract not found"**:
   - Ensure Tesseract is installed and in PATH
   - Update the path in `config.yaml` if needed

2. **"Cannot connect to Ollama"**:
   - Check if Ollama is running: `ollama list`
   - Verify endpoint in `config.yaml`

3. **"Model not found"**:
   - Pull the model: `ollama pull [model-name]`
   - Update `config.yaml` with available models

4. **Poor OCR results**:
   - Enable automatic preprocessing
   - Check preprocessing preview
   - Try different OCR languages if applicable

## 🚀 Performance Tips

- Use automatic preprocessing for best results
- For batch processing, adjust `max_images` in config
- Choose appropriate models:
  - LLaVA: Best quality but slower
  - Mistral/Phi3: Faster for text-only processing
- Enable parallel processing for large batches (experimental)

## 🔒 Security Note

This application runs entirely locally with no cloud dependencies. Your images and data never leave your machine.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is provided as-is for local use. Ensure you comply with the licenses of the underlying tools (Tesseract, Ollama, etc.).
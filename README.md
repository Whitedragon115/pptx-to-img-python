# PPTX to PDF/Image Converter API

A powerful web-based API server that converts PowerPoint (.pptx) files to PDF and images, with support for hidden slides.

## ✨ Features

- **PPTX to PDF conversion** using LibreOffice
- **PDF to image conversion** with customizable DPI
- **Hidden slides support** - Option to include or exclude hidden slides
- **Web-based interface** - Easy-to-use HTML frontend
- **REST API** - Programmatic access
- **Docker support** - Easy deployment
- **Automatic cleanup** - Temporary files management
- **Storage monitoring** - Disk usage tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- LibreOffice (for PDF conversion)
- poppler-utils (for image conversion)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pptx-to-img-python
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install LibreOffice**
   - **Windows**: Download from [LibreOffice.org](https://www.libreoffice.org/)
   - **Ubuntu/Debian**: `sudo apt-get install libreoffice`
   - **CentOS/RHEL**: `sudo yum install libreoffice`

4. **Install poppler-utils** (for pdf2image)
   - **Windows**: Download from [poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases)
   - **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
   - **CentOS/RHEL**: `sudo yum install poppler-utils`

### Running the Server

```bash
python api-server.py
```

The server will start on `http://localhost:5000`

## 🐳 Docker Deployment

```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up
```

## 📖 API Usage

### Convert PPTX File

**POST** `/convert`

**Parameters:**
- `file`: PPTX file (multipart/form-data)
- `include_hidden_slides`: Include hidden slides (boolean, default: true)
- `dpi`: Image resolution (integer, default: 200)

**Response:**
```json
{
  "request_time": "2025-01-01T12:00:00",
  "done_time": "2025-01-01T12:00:05",
  "total_pages": 10,
  "pdf_download_url": "/download/temp_123/presentation.pdf",
  "image_download_urls": [
    "/download/temp_123/page_001.jpg",
    "/download/temp_123/page_002.jpg"
  ],
  "temp_folder": "temp_123",
  "cleanup_scheduled": "20 minutes from request time"
}
```

### Health Check

**GET** `/health`

### Storage Information

**GET** `/storage/info`

### Cleanup Operations

**POST** `/cleanup/old` - Clean old temporary files
**POST** `/cleanup/all` - Clean all temporary files

## 🔧 Configuration

Environment variables can be set to customize the behavior:

- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)
- `LIBREOFFICE_PATH`: Path to LibreOffice executable
- `MAX_STORAGE_GB`: Maximum storage limit (default: 10)
- `DEFAULT_CLEANUP_MINUTES`: Auto cleanup delay (default: 20)
- `CONVERSION_TIMEOUT_SECONDS`: Conversion timeout (default: 300)

## 📁 Project Structure

```
├── api-server.py           # Main application server
├── index.html             # Web interface
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── modules/
│   ├── __init__.py
│   ├── config.py         # Configuration settings
│   ├── converter.py      # PPTX conversion logic
│   ├── file_manager.py   # File management utilities
│   └── routes.py         # API route handlers
├── temp/                 # Temporary files directory
├── uploads/              # File uploads directory
└── nginx/               # Nginx configuration (for production)
```

## 🛠️ Development

The codebase is organized into modular components:

- **converter.py**: Core conversion logic with XML manipulation for hidden slides
- **file_manager.py**: Handles file operations and cleanup scheduling
- **routes.py**: Flask route definitions and request handling
- **config.py**: Centralized configuration management

## 📄 License & Usage

This project is open source and free to use, modify, and distribute.

**Terms:**
- ✅ **Free to use** for personal and commercial projects
- ✅ **Free to modify** and adapt to your needs
- ✅ **Free to redistribute** and share
- ❌ **Cannot be sold** as a standalone product for profit

**Attribution:**
Please mention the original author when using or redistributing this code.

**Author:** Whitedragon

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## ⚠️ Disclaimer

This tool is provided as-is for educational and practical purposes. The author is not responsible for any misuse or damages caused by this software.

## 🔗 Dependencies

- **Flask**: Web framework
- **python-pptx**: PowerPoint file manipulation
- **pdf2image**: PDF to image conversion
- **Pillow**: Image processing
- **python-docx**: Document processing utilities

## 💡 Tips

1. **Performance**: Higher DPI values produce better quality images but larger file sizes
2. **Hidden Slides**: The tool can detect and include PowerPoint slides marked as hidden
3. **Storage**: Monitor the `/storage/info` endpoint to track disk usage
4. **Cleanup**: Files are automatically cleaned up after 20 minutes by default
5. **Docker**: Use Docker for consistent deployment across different environments

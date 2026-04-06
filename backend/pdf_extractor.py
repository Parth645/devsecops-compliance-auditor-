"""
PDF Extractor - Extract text from PDF policy documents
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

# Try to import PDF libraries
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not available, trying pdfplumber")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available")


class PDFExtractor:
    """Extract text content from PDF files"""
    
    def __init__(self):
        self.available_methods = []
        if PYPDF2_AVAILABLE:
            self.available_methods.append("pypdf2")
        if PDFPLUMBER_AVAILABLE:
            self.available_methods.append("pdfplumber")
        
        if not self.available_methods:
            logger.error("No PDF extraction libraries available!")
    
    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            return {
                "status": "error",
                "message": f"PDF file not found: {pdf_path}",
                "text": ""
            }
        
        # Try extraction methods in order of preference
        if PDFPLUMBER_AVAILABLE:
            result = self._extract_with_pdfplumber(pdf_file)
            if result["status"] == "success":
                return result
        
        if PYPDF2_AVAILABLE:
            result = self._extract_with_pypdf2(pdf_file)
            if result["status"] == "success":
                return result
        
        return {
            "status": "error",
            "message": "No PDF extraction method available",
            "text": ""
        }
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text using pdfplumber (preferred method)"""
        try:
            text_content = []
            metadata = {
                "pages": 0,
                "method": "pdfplumber"
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata["pages"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num}: {e}")
            
            full_text = "\n\n".join(text_content)
            
            # Clean up text
            full_text = self._clean_text(full_text)
            
            return {
                "status": "success",
                "text": full_text,
                "metadata": metadata,
                "word_count": len(full_text.split()),
                "char_count": len(full_text)
            }
            
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "text": ""
            }
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text using PyPDF2 (fallback method)"""
        try:
            text_content = []
            metadata = {
                "pages": 0,
                "method": "pypdf2"
            }
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num}: {e}")
            
            full_text = "\n\n".join(text_content)
            
            # Clean up text
            full_text = self._clean_text(full_text)
            
            return {
                "status": "success",
                "text": full_text,
                "metadata": metadata,
                "word_count": len(full_text.split()),
                "char_count": len(full_text)
            }
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "text": ""
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def is_available(self) -> bool:
        """Check if PDF extraction is available"""
        return len(self.available_methods) > 0
    
    def get_available_methods(self) -> list:
        """Get list of available extraction methods"""
        return self.available_methods

"""
Document Parser Module
Handles extraction of text from PDF and Word documents
"""
import io
import re
from typing import Optional, Tuple
import PyPDF2
import pdfplumber
from docx import Document
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentParser:
    """Parser for extracting text from PDF and Word documents"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s.,;:!()\-@#$%&]', '', text)
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_from_pdf_pypdf2(file_bytes: bytes) -> str:
        """
        Extract text from PDF using PyPDF2
        
        Args:
            file_bytes: PDF file content as bytes
            
        Returns:
            Extracted text
        """
        try:
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = '\n\n'.join(text_parts)
            logger.info(f"PyPDF2: Extracted {len(full_text)} characters from {len(pdf_reader.pages)} pages")
            return full_text
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return ""
    
    @staticmethod
    def extract_from_pdf_pdfplumber(file_bytes: bytes) -> str:
        """
        Extract text from PDF using pdfplumber (better for complex layouts)
        
        Args:
            file_bytes: PDF file content as bytes
            
        Returns:
            Extracted text
        """
        try:
            pdf_file = io.BytesIO(file_bytes)
            text_parts = []
            
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            full_text = '\n\n'.join(text_parts)
            logger.info(f"pdfplumber: Extracted {len(full_text)} characters from {len(text_parts)} pages")
            return full_text
            
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            return ""
    
    @staticmethod
    def extract_from_pdf(file_bytes: bytes) -> Tuple[str, str]:
        """
        Extract text from PDF using multiple methods and return best result
        
        Args:
            file_bytes: PDF file content as bytes
            
        Returns:
            Tuple of (extracted_text, method_used)
        """
        # Try pdfplumber first (better for complex layouts)
        text_pdfplumber = DocumentParser.extract_from_pdf_pdfplumber(file_bytes)
        
        # Try PyPDF2 as fallback
        text_pypdf2 = DocumentParser.extract_from_pdf_pypdf2(file_bytes)
        
        # Choose the method that extracted more text
        if len(text_pdfplumber) >= len(text_pypdf2):
            return DocumentParser.clean_text(text_pdfplumber), "pdfplumber"
        else:
            return DocumentParser.clean_text(text_pypdf2), "PyPDF2"
    
    @staticmethod
    def extract_from_docx(file_bytes: bytes) -> Tuple[str, str]:
        """
        Extract text from Word document
        
        Args:
            file_bytes: Word file content as bytes
            
        Returns:
            Tuple of (extracted_text, method_used)
        """
        try:
            docx_file = io.BytesIO(file_bytes)
            doc = Document(docx_file)
            
            text_parts = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(' | '.join(row_text))
            
            full_text = '\n\n'.join(text_parts)
            logger.info(f"python-docx: Extracted {len(full_text)} characters")
            
            return DocumentParser.clean_text(full_text), "python-docx"
            
        except Exception as e:
            logger.error(f"Word document extraction failed: {str(e)}")
            return "", "error"
    
    @staticmethod
    def parse_document(file_bytes: bytes, filename: str) -> Optional[dict]:
        """
        Parse document and extract text based on file type
        
        Args:
            file_bytes: Document file content as bytes
            filename: Name of the file (used to determine type)
            
        Returns:
            Dictionary with extraction results or None if failed
        """
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            text, method = DocumentParser.extract_from_pdf(file_bytes)
        elif file_ext in ['docx', 'doc']:
            text, method = DocumentParser.extract_from_docx(file_bytes)
        else:
            logger.error(f"Unsupported file type: {file_ext}")
            return None
        
        if not text:
            logger.error(f"No text extracted from {filename}")
            return None
        
        return {
            'text': text,
            'method': method,
            'filename': filename,
            'file_type': file_ext,
            'character_count': len(text),
            'word_count': len(text.split())
        }
    
    @staticmethod
    def validate_extraction(parsed_data: dict, min_words: int = 50) -> Tuple[bool, str]:
        """
        Validate that extracted text is sufficient for analysis
        
        Args:
            parsed_data: Dictionary from parse_document
            min_words: Minimum number of words required
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not parsed_data:
            return False, "Document parsing failed"
        
        if not parsed_data.get('text'):
            return False, "No text content found in document"
        
        word_count = parsed_data.get('word_count', 0)
        if word_count < min_words:
            return False, f"Document too short: {word_count} words (minimum {min_words} required)"
        
        return True, ""


# Create convenience functions
def parse_pdf(file_bytes: bytes, filename: str = "document.pdf") -> Optional[dict]:
    """Parse PDF file and extract text"""
    return DocumentParser.parse_document(file_bytes, filename)


def parse_docx(file_bytes: bytes, filename: str = "document.docx") -> Optional[dict]:
    """Parse Word document and extract text"""
    return DocumentParser.parse_document(file_bytes, filename)


def parse_file(file_bytes: bytes, filename: str) -> Optional[dict]:
    """Parse any supported document type"""
    return DocumentParser.parse_document(file_bytes, filename)

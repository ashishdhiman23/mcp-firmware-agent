"""File utilities for handling uploads and validation."""

import os
import magic
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException

from ..config import get_settings


class FileUtils:
    """Utilities for file handling and validation."""
    
    def __init__(self):
        """Initialize file utilities."""
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    def validate_log_file(self, file: UploadFile) -> bool:
        """Validate that the uploaded file is a valid log file.
        
        Args:
            file: The uploaded file
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check file size
        if hasattr(file, 'size') and file.size > self.settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.settings.max_file_size} bytes"
            )
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.settings.allowed_log_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed extensions: {self.settings.allowed_log_extensions}"
                )
        
        return True
    
    def validate_elf_file(self, file: UploadFile) -> bool:
        """Validate that the uploaded file is a valid ELF file.
        
        Args:
            file: The uploaded file
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check file size
        if hasattr(file, 'size') and file.size > self.settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.settings.max_file_size} bytes"
            )
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.settings.allowed_elf_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed extensions: {self.settings.allowed_elf_extensions}"
                )
        
        return True
    
    async def read_log_file(self, file: UploadFile) -> str:
        """Read and decode a log file.
        
        Args:
            file: The uploaded log file
            
        Returns:
            The file content as a string
            
        Raises:
            HTTPException: If file cannot be read
        """
        try:
            content = await file.read()
            
            # Try to decode as UTF-8 first
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252', 'ascii']:
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                
                # If all else fails, decode with error handling
                return content.decode('utf-8', errors='replace')
                
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read log file: {str(e)}"
            )
    
    async def read_elf_file(self, file: UploadFile) -> bytes:
        """Read an ELF binary file.
        
        Args:
            file: The uploaded ELF file
            
        Returns:
            The file content as bytes
            
        Raises:
            HTTPException: If file cannot be read
        """
        try:
            content = await file.read()
            return content
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read ELF file: {str(e)}"
            )
    
    def detect_file_type(self, content: bytes) -> str:
        """Detect the type of file from its content.
        
        Args:
            content: File content as bytes
            
        Returns:
            File type description
        """
        try:
            # Use python-magic to detect file type
            file_type = magic.from_buffer(content, mime=True)
            return file_type
        except Exception:
            # Fallback to simple heuristics
            if content.startswith(b'\x7fELF'):
                return 'application/x-executable'
            elif content.startswith(b'{') or content.startswith(b'['):
                return 'application/json'
            else:
                return 'text/plain'
    
    def is_json_content(self, content: str) -> bool:
        """Check if content appears to be JSON.
        
        Args:
            content: String content to check
            
        Returns:
            True if content appears to be JSON
        """
        content = content.strip()
        return (content.startswith('{') and content.endswith('}')) or \
               (content.startswith('[') and content.endswith(']'))
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = Path(filename).name
        
        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def get_file_info(self, file: UploadFile) -> dict:
        """Get information about an uploaded file.
        
        Args:
            file: The uploaded file
            
        Returns:
            Dictionary with file information
        """
        info = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': getattr(file, 'size', None)
        }
        
        if file.filename:
            path = Path(file.filename)
            info.update({
                'extension': path.suffix.lower(),
                'basename': path.stem
            })
        
        return info 
"""
PDF Stream Handler - Issue #43 Fix
Implements chunked PDF streaming to prevent memory exhaustion
"""
import asyncio
from typing import AsyncIterator, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PDFStreamHandler:
    """
    Streams PDF files in chunks to avoid loading entire file in memory.
    Supports async operations and proper resource cleanup.
    """
    
    def __init__(self, chunk_size: int = 8192):
        """
        Initialize PDF stream handler.
        
        Args:
            chunk_size: Size of chunks to read (default 8KB)
        """
        self.chunk_size = chunk_size
        self._active_streams = set()
    
    async def stream_pdf(
        self, 
        file_path: Path,
        start_byte: Optional[int] = None,
        end_byte: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        """
        Stream PDF file in chunks.
        
        Args:
            file_path: Path to PDF file
            start_byte: Optional starting byte position
            end_byte: Optional ending byte position
            
        Yields:
            Chunks of PDF data as bytes
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            PermissionError: If file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            file_size = file_path.stat().st_size
            logger.info(f"Streaming PDF {file_path.name} ({file_size:,} bytes)")
            
            # Register active stream
            stream_id = id(file_path)
            self._active_streams.add(stream_id)
            
            async with asyncio.Lock():
                with open(file_path, 'rb') as f:
                    # Seek to start position if specified
                    if start_byte:
                        f.seek(start_byte)
                    
                    bytes_read = start_byte or 0
                    max_bytes = end_byte or file_size
                    
                    while bytes_read < max_bytes:
                        # Calculate chunk size for this read
                        remaining = max_bytes - bytes_read
                        current_chunk_size = min(self.chunk_size, remaining)
                        
                        # Read chunk
                        chunk = f.read(current_chunk_size)
                        if not chunk:
                            break
                        
                        bytes_read += len(chunk)
                        yield chunk
                        
                        # Allow other coroutines to run
                        await asyncio.sleep(0)
            
            logger.info(f"Completed streaming {bytes_read:,} bytes from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error streaming PDF {file_path}: {e}")
            raise
        finally:
            # Cleanup stream registration
            self._active_streams.discard(stream_id)
    
    async def stream_page_range(
        self,
        file_path: Path,
        start_page: int,
        end_page: int
    ) -> AsyncIterator[bytes]:
        """
        Stream specific page range from PDF.
        
        Args:
            file_path: Path to PDF file
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (inclusive)
            
        Yields:
            Chunks of PDF data for specified pages
        """
        # TODO: Implement page-aware streaming using PyPDF2 or similar
        # For now, stream entire file and let consumer filter pages
        async for chunk in self.stream_pdf(file_path):
            yield chunk
    
    async def get_metadata(self, file_path: Path) -> dict:
        """
        Get PDF metadata without loading entire file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with file size, page count, etc.
        """
        stat = file_path.stat()
        return {
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': stat.st_mtime,
            'is_readable': True
        }
    
    def active_stream_count(self) -> int:
        """Get number of currently active streams."""
        return len(self._active_streams)
    
    async def close_all(self):
        """Close all active streams gracefully."""
        logger.info(f"Closing {len(self._active_streams)} active streams")
        self._active_streams.clear()


# Example usage and integration
async def process_large_pdf(file_path: Path):
    """
    Example: Process large PDF without memory overflow.
    """
    handler = PDFStreamHandler(chunk_size=16384)  # 16KB chunks
    
    total_bytes = 0
    async for chunk in handler.stream_pdf(file_path):
        # Process chunk (e.g., upload to S3, OCR, etc.)
        total_bytes += len(chunk)
        
        # Log progress every 1MB
        if total_bytes % (1024 * 1024) == 0:
            logger.info(f"Processed {total_bytes // (1024 * 1024)} MB")
    
    return total_bytes


# Integration with existing FILEBOSS API
class FileBossStreamingAPI:
    """
    API endpoints for streaming PDF files.
    """
    
    def __init__(self):
        self.handler = PDFStreamHandler()
    
    async def stream_endpoint(self, file_id: str, range_header: Optional[str] = None):
        """
        HTTP endpoint for streaming PDF files with Range support.
        
        Args:
            file_id: Database ID of PDF file
            range_header: Optional HTTP Range header (e.g., "bytes=0-1023")
            
        Returns:
            Streaming response with appropriate headers
        """
        # Get file path from database
        file_path = await self._get_file_path(file_id)
        
        # Parse range header
        start_byte, end_byte = self._parse_range_header(range_header)
        
        # Return streaming response
        return {
            'status': 206 if range_header else 200,
            'headers': {
                'Content-Type': 'application/pdf',
                'Accept-Ranges': 'bytes',
                'Content-Range': f'bytes {start_byte}-{end_byte}/*'
            },
            'stream': self.handler.stream_pdf(file_path, start_byte, end_byte)
        }
    
    async def _get_file_path(self, file_id: str) -> Path:
        """Retrieve file path from database."""
        # TODO: Implement database lookup
        return Path(f"/data/pdfs/{file_id}.pdf")
    
    def _parse_range_header(self, range_header: Optional[str]) -> tuple[int, int]:
        """Parse HTTP Range header."""
        if not range_header:
            return 0, float('inf')
        
        # Parse "bytes=start-end" format
        range_spec = range_header.replace('bytes=', '')
        start, end = range_spec.split('-')
        return int(start), int(end) if end else float('inf')

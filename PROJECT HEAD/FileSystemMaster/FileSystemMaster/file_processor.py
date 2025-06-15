"""
File processing module for extracting content from various file types
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

# File processing libraries
try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3NoHeaderError
except ImportError:
    MutagenFile = None

try:
    import cv2
except ImportError:
    cv2 = None

from multi_ai_analyzer import MultiAIAnalyzer
from utils import safe_filename, calculate_file_hash
from config import Config

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file scanning and content extraction"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ai_analyzer = MultiAIAnalyzer()
        self.supported_extensions = {
            'pdf': ['.pdf'],
            'doc': ['.doc', '.docx'],
            'text': ['.txt', '.md', '.rtf'],
            'audio': ['.mp3', '.wav', '.m4a', '.flac', '.ogg'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        }
    
    def scan_directory(self, directory: Path) -> List[Dict]:
        """Scan directory for supported file types"""
        files_found = []
        file_count = 0
        
        logger.info(f"Scanning directory: {directory}")
        
        for root, dirs, files in os.walk(directory):
            if file_count >= self.config.max_files:
                logger.warning(f"Reached maximum file limit: {self.config.max_files}")
                break
                
            for file in files:
                file_path = Path(root) / file
                file_ext = file_path.suffix.lower()
                
                # Check if file type is supported and requested
                if self._is_supported_file(file_ext):
                    try:
                        file_info = {
                            'path': file_path,
                            'name': file_path.name,
                            'extension': file_ext,
                            'size': file_path.stat().st_size,
                            'modified': file_path.stat().st_mtime,
                            'hash': calculate_file_hash(file_path),
                            'type': self._get_file_type(file_ext)
                        }
                        files_found.append(file_info)
                        file_count += 1
                        
                        if file_count >= self.config.max_files:
                            break
                            
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Could not access file {file_path}: {e}")
                        continue
        
        return files_found
    
    def process_files(self, files: List[Dict]) -> List[Dict]:
        """Process files and extract content for AI analysis"""
        processed_files = []
        
        for i, file_info in enumerate(files, 1):
            logger.info(f"Processing file {i}/{len(files)}: {file_info['name']}")
            
            try:
                # Extract content based on file type
                content = self._extract_content(file_info)
                
                # Analyze with AI
                analysis = self.ai_analyzer.analyze_document(
                    content, 
                    file_info['type'],
                    file_info['name']
                )
                
                # Combine file info with analysis
                processed_file = {
                    **file_info,
                    'content': content,
                    'analysis': analysis,
                    'suggested_name': analysis.get('suggested_name', file_info['name']),
                    'category': analysis.get('category', 'uncategorized'),
                    'confidence': analysis.get('confidence', 0.0)
                }
                
                processed_files.append(processed_file)
                
            except Exception as e:
                logger.error(f"Error processing {file_info['name']}: {str(e)}")
                # Add file with minimal processing
                processed_file = {
                    **file_info,
                    'content': {'text': '', 'metadata': {}},
                    'analysis': {
                        'suggested_name': file_info['name'],
                        'category': 'error',
                        'confidence': 0.0,
                        'error': str(e)
                    },
                    'suggested_name': file_info['name'],
                    'category': 'error',
                    'confidence': 0.0
                }
                processed_files.append(processed_file)
        
        return processed_files
    
    def _is_supported_file(self, extension: str) -> bool:
        """Check if file extension is supported"""
        for file_type in self.config.file_types:
            # Check if this specific type is requested
            if file_type in ['pdf'] and extension in self.supported_extensions['pdf']:
                return True
            elif file_type in ['doc', 'docx'] and extension in self.supported_extensions['doc']:
                return True
            elif file_type in ['txt', 'text'] and extension in self.supported_extensions['text']:
                return True
            elif file_type in ['mp3', 'audio'] and extension in self.supported_extensions['audio']:
                return True
            elif file_type in ['mp4', 'video', 'avi', 'mov'] and extension in self.supported_extensions['video']:
                return True
        return False
    
    def _get_file_type(self, extension: str) -> str:
        """Determine file type category"""
        if extension in self.supported_extensions['pdf']:
            return 'pdf'
        elif extension in self.supported_extensions['doc']:
            return 'document'
        elif extension in self.supported_extensions['text']:
            return 'text'
        elif extension in self.supported_extensions['audio']:
            return 'audio'
        elif extension in self.supported_extensions['video']:
            return 'video'
        return 'unknown'
    
    def _extract_content(self, file_info: Dict) -> Dict:
        """Extract content from file based on type"""
        file_type = file_info['type']
        file_path = file_info['path']
        
        content = {
            'text': '',
            'metadata': {},
            'error': None
        }
        
        try:
            if file_type == 'pdf':
                content = self._extract_pdf_content(file_path)
            elif file_type == 'document':
                content = self._extract_doc_content(file_path)
            elif file_type == 'text':
                content = self._extract_text_content(file_path)
            elif file_type == 'audio':
                content = self._extract_audio_metadata(file_path)
            elif file_type == 'video':
                content = self._extract_video_metadata(file_path)
            
        except Exception as e:
            content['error'] = str(e)
            logger.warning(f"Content extraction failed for {file_path}: {e}")
        
        return content
    
    def _extract_pdf_content(self, file_path: Path) -> Dict:
        """Extract text and metadata from PDF files"""
        content = {'text': '', 'metadata': {}, 'pages': 0}
        
        if not pdfplumber:
            raise ImportError("pdfplumber not available for PDF processing")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                content['pages'] = len(pdf.pages)
                content['metadata'] = pdf.metadata or {}
                
                # Extract text from first few pages
                text_parts = []
                for i, page in enumerate(pdf.pages[:5]):  # Limit to first 5 pages
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                content['text'] = '\n'.join(text_parts)
                
        except Exception as e:
            # Fallback to PyPDF2
            if PyPDF2:
                try:
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        content['pages'] = len(reader.pages)
                        
                        # Extract text from first few pages
                        text_parts = []
                        for i in range(min(5, len(reader.pages))):
                            page_text = reader.pages[i].extract_text()
                            if page_text:
                                text_parts.append(page_text)
                        
                        content['text'] = '\n'.join(text_parts)
                        content['metadata'] = reader.metadata or {}
                        
                except Exception as e2:
                    raise Exception(f"PDF extraction failed: {e}, {e2}")
            else:
                raise e
        
        return content
    
    def _extract_text_content(self, file_path: Path) -> Dict:
        """Extract text content from plain text files"""
        content = {'text': '', 'metadata': {}, 'lines': 0}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                
            content['text'] = text_content
            content['lines'] = len(text_content.splitlines())
            content['metadata'] = {
                'encoding': 'utf-8',
                'word_count': len(text_content.split()),
                'char_count': len(text_content)
            }
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    text_content = f.read()
                    
                content['text'] = text_content
                content['lines'] = len(text_content.splitlines())
                content['metadata'] = {
                    'encoding': 'latin-1',
                    'word_count': len(text_content.split()),
                    'char_count': len(text_content)
                }
            except Exception as e:
                raise Exception(f"Text file extraction failed: {e}")
        except Exception as e:
            raise Exception(f"Text file extraction failed: {e}")
        
        return content
    
    def _extract_doc_content(self, file_path: Path) -> Dict:
        """Extract text and metadata from Word documents"""
        content = {'text': '', 'metadata': {}, 'paragraphs': 0}
        
        if not Document:
            raise ImportError("python-docx not available for document processing")
        
        try:
            doc = Document(str(file_path))
            
            # Extract text from paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())
            
            content['text'] = '\n'.join(paragraphs)
            content['paragraphs'] = len(paragraphs)
            
            # Extract metadata
            props = doc.core_properties
            content['metadata'] = {
                'title': props.title or '',
                'author': props.author or '',
                'subject': props.subject or '',
                'created': str(props.created) if props.created else '',
                'modified': str(props.modified) if props.modified else ''
            }
            
        except Exception as e:
            raise Exception(f"Document extraction failed: {e}")
        
        return content
    
    def _extract_audio_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from audio files"""
        content = {'text': '', 'metadata': {}}
        
        if not MutagenFile:
            raise ImportError("mutagen not available for audio processing")
        
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is not None:
                # Extract common metadata
                metadata = {}
                
                # Common tags
                tag_mapping = {
                    'TIT2': 'title',
                    'TPE1': 'artist',
                    'TALB': 'album',
                    'TDRC': 'date',
                    'TCON': 'genre',
                    'TPE2': 'albumartist'
                }
                
                for tag, name in tag_mapping.items():
                    if tag in audio_file:
                        metadata[name] = str(audio_file[tag][0])
                
                # Also try alternative formats
                if hasattr(audio_file, 'info'):
                    metadata.update({
                        'length': getattr(audio_file.info, 'length', 0),
                        'bitrate': getattr(audio_file.info, 'bitrate', 0),
                        'channels': getattr(audio_file.info, 'channels', 0)
                    })
                
                content['metadata'] = metadata
                
                # Create text summary for AI analysis
                text_parts = []
                if 'title' in metadata:
                    text_parts.append(f"Title: {metadata['title']}")
                if 'artist' in metadata:
                    text_parts.append(f"Artist: {metadata['artist']}")
                if 'album' in metadata:
                    text_parts.append(f"Album: {metadata['album']}")
                if 'genre' in metadata:
                    text_parts.append(f"Genre: {metadata['genre']}")
                
                content['text'] = '\n'.join(text_parts)
                
        except Exception as e:
            raise Exception(f"Audio metadata extraction failed: {e}")
        
        return content
    
    def _extract_video_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from video files"""
        content = {'text': '', 'metadata': {}}
        
        # Try mutagen first for container metadata
        if MutagenFile:
            try:
                video_file = MutagenFile(file_path)
                if video_file is not None:
                    metadata = {}
                    
                    # Extract available metadata
                    for key, value in video_file.items():
                        if isinstance(value, list) and len(value) > 0:
                            metadata[key] = str(value[0])
                        else:
                            metadata[key] = str(value)
                    
                    if hasattr(video_file, 'info'):
                        metadata.update({
                            'length': getattr(video_file.info, 'length', 0),
                            'bitrate': getattr(video_file.info, 'bitrate', 0)
                        })
                    
                    content['metadata'] = metadata
                    
            except Exception:
                pass  # Continue to OpenCV fallback
        
        # Try OpenCV for basic video properties
        if cv2:
            try:
                cap = cv2.VideoCapture(str(file_path))
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    
                    content['metadata'].update({
                        'fps': fps,
                        'frame_count': frame_count,
                        'width': int(width),
                        'height': int(height),
                        'duration': frame_count / fps if fps > 0 else 0
                    })
                    
                cap.release()
                
            except Exception as e:
                logger.warning(f"OpenCV video analysis failed: {e}")
        
        # Create text summary
        metadata = content['metadata']
        text_parts = []
        
        if 'width' in metadata and 'height' in metadata:
            text_parts.append(f"Resolution: {int(metadata['width'])}x{int(metadata['height'])}")
        if 'duration' in metadata:
            duration = metadata['duration']
            if duration > 0:
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                text_parts.append(f"Duration: {minutes}:{seconds:02d}")
        
        content['text'] = '\n'.join(text_parts)
        
        return content

"""
File organization module for smart sorting and renaming
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List
import logging

from utils import safe_filename
from config import Config

logger = logging.getLogger(__name__)

class FileOrganizer:
    """Handles file organization and renaming based on AI analysis"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def organize_files(self, processed_files: List[Dict], output_dir: Path) -> Dict:
        """Organize files into structured directories with smart naming"""
        
        results = {
            'organized': 0,
            'errors': 0,
            'skipped': 0,
            'operations': []
        }
        
        logger.info(f"Organizing {len(processed_files)} files into {output_dir}")
        
        for file_info in processed_files:
            try:
                operation = self._organize_single_file(file_info, output_dir)
                results['operations'].append(operation)
                
                if operation['status'] == 'success':
                    results['organized'] += 1
                elif operation['status'] == 'skipped':
                    results['skipped'] += 1
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Error organizing {file_info['name']}: {str(e)}")
                results['errors'] += 1
                results['operations'].append({
                    'source': str(file_info['path']),
                    'destination': '',
                    'status': 'error',
                    'error': str(e)
                })
        
        # Log summary
        logger.info(f"Organization complete: {results['organized']} organized, "
                   f"{results['errors']} errors, {results['skipped']} skipped")
        
        return results
    
    def _organize_single_file(self, file_info: Dict, output_dir: Path) -> Dict:
        """Organize a single file"""
        
        source_path = file_info['path']
        analysis = file_info.get('analysis', {})
        
        # Determine target directory structure
        target_structure = self._get_target_structure(analysis, file_info)
        target_dir = output_dir / target_structure['category']
        
        if target_structure['subcategory']:
            target_dir = target_dir / target_structure['subcategory']
        
        # Generate new filename
        new_filename = self._generate_filename(file_info, analysis)
        target_path = target_dir / new_filename
        
        operation = {
            'source': str(source_path),
            'destination': str(target_path),
            'status': 'pending',
            'category': target_structure['category'],
            'subcategory': target_structure['subcategory'],
            'confidence': analysis.get('confidence', 0.0)
        }
        
        try:
            # Check if dry run
            if self.config.dry_run:
                operation['status'] = 'dry_run'
                logger.info(f"DRY RUN: Would move {source_path} -> {target_path}")
                return operation
            
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Handle file conflicts
            if target_path.exists():
                target_path = self._resolve_conflict(target_path, file_info)
                operation['destination'] = str(target_path)
            
            # Copy or move file
            if self.config.copy_files:
                shutil.copy2(source_path, target_path)
                operation['action'] = 'copied'
            else:
                shutil.move(str(source_path), str(target_path))
                operation['action'] = 'moved'
            
            operation['status'] = 'success'
            logger.info(f"Successfully {operation['action']} {source_path.name} -> {target_path}")
            
        except Exception as e:
            operation['status'] = 'error'
            operation['error'] = str(e)
            logger.error(f"Failed to organize {source_path}: {str(e)}")
        
        return operation
    
    def _get_target_structure(self, analysis: Dict, file_info: Dict) -> Dict:
        """Determine target directory structure based on analysis"""
        
        category = analysis.get('category', 'uncategorized')
        subcategory = analysis.get('subcategory', '')
        
        # Apply naming pattern rules
        if self.config.naming_pattern == 'timestamp':
            from datetime import datetime
            timestamp = datetime.fromtimestamp(file_info['modified'])
            year_month = timestamp.strftime('%Y/%m')
            return {
                'category': year_month,
                'subcategory': category
            }
        
        elif self.config.naming_pattern == 'category':
            return {
                'category': category,
                'subcategory': subcategory if subcategory else file_info['type']
            }
        
        elif self.config.naming_pattern == 'content':
            # Use AI-suggested structure
            return {
                'category': category,
                'subcategory': subcategory
            }
        
        else:  # smart (default)
            # Intelligent structure based on file type and content
            file_type = file_info['type']
            
            if file_type in ['pdf', 'document']:
                return {
                    'category': 'Documents',
                    'subcategory': category.title() if category != 'uncategorized' else 'General'
                }
            elif file_type in ['audio', 'video']:
                return {
                    'category': 'Media',
                    'subcategory': file_type.title()
                }
            else:
                return {
                    'category': category.title(),
                    'subcategory': subcategory.title() if subcategory else ''
                }
    
    def _generate_filename(self, file_info: Dict, analysis: Dict) -> str:
        """Generate new filename based on analysis and naming pattern"""
        
        original_name = file_info['name']
        extension = file_info['extension']
        suggested_name = analysis.get('suggested_name', '')
        
        # Clean and validate suggested name
        if suggested_name and suggested_name.strip():
            base_name = safe_filename(suggested_name)
        else:
            # Fallback to original name without extension
            base_name = safe_filename(original_name.rsplit('.', 1)[0])
        
        # Apply naming pattern modifications
        if self.config.naming_pattern == 'timestamp':
            from datetime import datetime
            timestamp = datetime.fromtimestamp(file_info['modified'])
            date_prefix = timestamp.strftime('%Y%m%d')
            base_name = f"{date_prefix}_{base_name}"
        
        # Add confidence indicator for low confidence results
        confidence = analysis.get('confidence', 0.0)
        if confidence < 0.3:
            base_name = f"unverified_{base_name}"
        
        # Ensure extension is included
        if not base_name.endswith(extension):
            new_filename = f"{base_name}{extension}"
        else:
            new_filename = base_name
        
        return new_filename
    
    def _resolve_conflict(self, target_path: Path, file_info: Dict) -> Path:
        """Resolve filename conflicts by adding suffix"""
        
        base_path = target_path.parent
        stem = target_path.stem
        suffix = target_path.suffix
        
        counter = 1
        while target_path.exists():
            # Check if files are identical
            if self._files_identical(file_info['path'], target_path):
                logger.info(f"Identical file already exists: {target_path}")
                raise Exception(f"Identical file already exists: {target_path.name}")
            
            # Generate new name with counter
            new_name = f"{stem}_{counter:03d}{suffix}"
            target_path = base_path / new_name
            counter += 1
            
            if counter > 999:
                raise Exception("Too many file conflicts, cannot resolve")
        
        return target_path
    
    def _files_identical(self, path1: Path, path2: Path) -> bool:
        """Check if two files are identical by comparing size and hash"""
        
        try:
            # Quick size check
            if path1.stat().st_size != path2.stat().st_size:
                return False
            
            # Hash comparison for same-size files
            from utils import calculate_file_hash
            hash1 = calculate_file_hash(path1)
            hash2 = calculate_file_hash(path2)
            
            return hash1 == hash2
            
        except Exception:
            return False
    
    def create_organization_report(self, results: Dict, output_dir: Path) -> None:
        """Create a detailed organization report"""
        
        report_path = output_dir / "organization_report.txt"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("FILE ORGANIZATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                # Summary
                f.write("SUMMARY:\n")
                f.write(f"Total files processed: {len(results['operations'])}\n")
                f.write(f"Successfully organized: {results['organized']}\n")
                f.write(f"Errors: {results['errors']}\n")
                f.write(f"Skipped: {results['skipped']}\n\n")
                
                # Category breakdown
                categories = {}
                for op in results['operations']:
                    if op['status'] == 'success' or op['status'] == 'dry_run':
                        category = op.get('category', 'unknown')
                        categories[category] = categories.get(category, 0) + 1
                
                if categories:
                    f.write("CATEGORIES:\n")
                    for category, count in sorted(categories.items()):
                        f.write(f"  {category}: {count} files\n")
                    f.write("\n")
                
                # Detailed operations
                f.write("DETAILED OPERATIONS:\n")
                f.write("-" * 30 + "\n")
                
                for op in results['operations']:
                    f.write(f"Source: {op['source']}\n")
                    f.write(f"Destination: {op['destination']}\n")
                    f.write(f"Status: {op['status']}\n")
                    
                    if 'category' in op:
                        f.write(f"Category: {op['category']}\n")
                    if 'subcategory' in op:
                        f.write(f"Subcategory: {op['subcategory']}\n")
                    if 'confidence' in op:
                        f.write(f"Confidence: {op['confidence']:.2f}\n")
                    if 'error' in op:
                        f.write(f"Error: {op['error']}\n")
                    
                    f.write("\n")
            
            logger.info(f"Organization report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to create organization report: {str(e)}")

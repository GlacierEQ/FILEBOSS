"""
AI content analysis module using OpenAI API
"""

import json
import os
import logging
from typing import Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI-powered content analysis for intelligent file naming and categorization"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
        # Enhanced AI context for legal and business intelligence
        self.legal_keywords = {
            'contracts': ['agreement', 'contract', 'terms', 'conditions', 'clause', 'amendment', 'addendum'],
            'compliance': ['compliance', 'regulation', 'policy', 'procedure', 'audit', 'certification'],
            'legal_docs': ['legal', 'lawsuit', 'litigation', 'court', 'judge', 'attorney', 'counsel'],
            'financial': ['financial', 'budget', 'revenue', 'profit', 'expense', 'invoice', 'receipt'],
            'hr_docs': ['employee', 'personnel', 'payroll', 'benefits', 'performance', 'review'],
            'confidential': ['confidential', 'private', 'restricted', 'classified', 'sensitive']
        }
        
        # Business document patterns
        self.document_patterns = {
            'meeting_minutes': ['meeting', 'minutes', 'attendees', 'agenda', 'action items'],
            'reports': ['report', 'analysis', 'summary', 'findings', 'recommendations'],
            'proposals': ['proposal', 'project', 'scope', 'timeline', 'deliverables'],
            'presentations': ['presentation', 'slides', 'deck', 'overview', 'executive summary']
        }
    
    def analyze_file_content(self, content: Dict, file_type: str, original_name: str) -> Dict:
        """Analyze file content and generate intelligent naming suggestions"""
        
        try:
            # Pre-analyze content for legal/business context
            content_classification = self._classify_content(content, original_name)
            
            # Prepare enhanced content for analysis
            analysis_text = self._prepare_enhanced_content_for_analysis(
                content, file_type, original_name, content_classification
            )
            
            # Get AI analysis with enhanced prompts
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_enhanced_system_prompt(file_type, content_classification)
                    },
                    {
                        "role": "user",
                        "content": analysis_text
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2  # Lower temperature for more consistent legal/business analysis
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Enhanced validation with legal context
            return self._validate_enhanced_analysis_result(result, original_name, content_classification)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._enhanced_fallback_analysis(original_name, file_type, content)
    
    def _prepare_content_for_analysis(self, content: Dict, file_type: str, original_name: str) -> str:
        """Prepare content text for AI analysis"""
        
        analysis_parts = [
            f"File Type: {file_type}",
            f"Original Name: {original_name}"
        ]
        
        # Add text content if available
        if content.get('text'):
            text_content = content['text'][:2000]  # Limit text length
            analysis_parts.append(f"Content Text:\n{text_content}")
        
        # Add metadata information
        if content.get('metadata'):
            metadata = content['metadata']
            metadata_text = []
            
            for key, value in metadata.items():
                if value and str(value).strip():
                    metadata_text.append(f"{key}: {value}")
            
            if metadata_text:
                analysis_parts.append("Metadata:\n" + "\n".join(metadata_text))
        
        # Add file-specific information
        if file_type == 'pdf' and content.get('pages'):
            analysis_parts.append(f"Page Count: {content['pages']}")
        elif file_type == 'document' and content.get('paragraphs'):
            analysis_parts.append(f"Paragraph Count: {content['paragraphs']}")
        elif file_type == 'audio' and content.get('metadata', {}).get('length'):
            length = content['metadata']['length']
            minutes = int(length // 60)
            seconds = int(length % 60)
            analysis_parts.append(f"Duration: {minutes}:{seconds:02d}")
        elif file_type == 'video' and content.get('metadata', {}).get('duration'):
            duration = content['metadata']['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            analysis_parts.append(f"Duration: {minutes}:{seconds:02d}")
        
        return "\n\n".join(analysis_parts)
    
    def _classify_content(self, content: Dict, original_name: str) -> Dict:
        """Pre-classify content for legal and business context"""
        text_content = content.get('text', '').lower()
        filename_lower = original_name.lower()
        
        classification = {
            'legal_category': None,
            'document_type': None,
            'sensitivity_level': 'standard',
            'business_context': [],
            'detected_patterns': [],
            'priority_level': 'normal'
        }
        
        # Check for legal document types
        for category, keywords in self.legal_keywords.items():
            if any(keyword in text_content or keyword in filename_lower for keyword in keywords):
                classification['legal_category'] = category
                if category == 'confidential':
                    classification['sensitivity_level'] = 'high'
                elif category in ['contracts', 'legal_docs']:
                    classification['sensitivity_level'] = 'medium'
        
        # Check for business document patterns
        for doc_type, patterns in self.document_patterns.items():
            if any(pattern in text_content or pattern in filename_lower for pattern in patterns):
                classification['document_type'] = doc_type
                classification['detected_patterns'].append(doc_type)
        
        # Determine business context
        business_indicators = {
            'financial': ['budget', 'revenue', 'profit', 'expense', 'financial', 'invoice'],
            'hr': ['employee', 'personnel', 'performance', 'review', 'benefits'],
            'legal': ['contract', 'agreement', 'legal', 'compliance', 'policy'],
            'strategy': ['strategy', 'planning', 'roadmap', 'vision', 'goals'],
            'operations': ['process', 'procedure', 'workflow', 'operations', 'manual']
        }
        
        for context, indicators in business_indicators.items():
            if any(indicator in text_content for indicator in indicators):
                classification['business_context'].append(context)
        
        # Set priority based on content type
        high_priority_terms = ['urgent', 'critical', 'deadline', 'asap', 'emergency']
        if any(term in text_content for term in high_priority_terms):
            classification['priority_level'] = 'high'
        
        return classification
    
    def _prepare_enhanced_content_for_analysis(self, content: Dict, file_type: str, 
                                             original_name: str, classification: Dict) -> str:
        """Prepare enhanced content with legal and business context"""
        
        analysis_parts = [
            f"File Type: {file_type}",
            f"Original Name: {original_name}",
            f"Legal Category: {classification.get('legal_category', 'none')}",
            f"Document Type: {classification.get('document_type', 'unknown')}",
            f"Sensitivity Level: {classification.get('sensitivity_level', 'standard')}",
            f"Business Context: {', '.join(classification.get('business_context', []))}"
        ]
        
        # Add text content with enhanced context
        if content.get('text'):
            text_content = content['text'][:3000]  # Increased limit for better analysis
            analysis_parts.append(f"Content Text:\n{text_content}")
        
        # Add metadata with business intelligence
        if content.get('metadata'):
            metadata = content['metadata']
            metadata_text = []
            
            for key, value in metadata.items():
                if value and str(value).strip():
                    metadata_text.append(f"{key}: {value}")
            
            if metadata_text:
                analysis_parts.append("Metadata:\n" + "\n".join(metadata_text))
        
        # Add file-specific enhanced information
        if file_type == 'pdf' and content.get('pages'):
            analysis_parts.append(f"Document Length: {content['pages']} pages")
        elif file_type == 'text' and content.get('metadata', {}).get('word_count'):
            word_count = content['metadata']['word_count']
            analysis_parts.append(f"Document Length: {word_count} words")
        
        return "\n\n".join(analysis_parts)
    
    def _get_enhanced_system_prompt(self, file_type: str, classification: Dict) -> str:
        """Get enhanced system prompt with legal and business intelligence"""
        
        legal_category = classification.get('legal_category')
        sensitivity = classification.get('sensitivity_level', 'standard')
        business_context = classification.get('business_context', [])
        
        base_prompt = f"""You are an expert legal and business document analyst with deep understanding of corporate governance, compliance, and document management best practices.

CURRENT ANALYSIS CONTEXT:
- Legal Category: {legal_category or 'General Business'}
- Sensitivity Level: {sensitivity.upper()}
- Business Context: {', '.join(business_context) if business_context else 'General'}

Your response must be valid JSON with the following enhanced structure:
{{
    "suggested_name": "intelligent_descriptive_filename_without_extension",
    "category": "primary_category",
    "subcategory": "specific_subcategory", 
    "confidence": 0.95,
    "reasoning": "Professional explanation of naming and categorization choice",
    "tags": ["business_tag1", "legal_tag2", "context_tag3"],
    "legal_classification": "contract/compliance/financial/hr/general",
    "sensitivity_level": "low/medium/high/confidential",
    "retention_period": "years_to_retain_or_permanent",
    "compliance_notes": "Any relevant compliance or legal considerations",
    "priority_level": "low/normal/high/urgent"
}}

ENHANCED NAMING GUIDELINES:
1. For legal documents: Include document type, parties, date, version
2. For financial documents: Include period, type, department if applicable  
3. For compliance documents: Include regulation/standard reference
4. For contracts: Include counterparty, effective date, contract type
5. For HR documents: Include employee category, review period, department
6. Use professional business naming conventions
7. Include date context when relevant (YYYY-MM-DD or YYYY-Q# format)
8. Avoid ambiguous abbreviations - spell out important terms
9. Consider document hierarchy and version control
10. Ensure names support audit trails and legal discovery

SECURITY AND COMPLIANCE CONSIDERATIONS:
- Mark sensitive documents appropriately
- Consider data retention requirements
- Flag documents requiring special handling
- Identify potential attorney-client privilege
- Note confidentiality requirements
- Consider regulatory compliance needs"""

Your response must be valid JSON with the following structure:
{
    "suggested_name": "meaningful_filename_without_extension",
    "category": "category_name",
    "subcategory": "subcategory_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of naming choice",
    "tags": ["tag1", "tag2", "tag3"]
}

Guidelines:
1. Create descriptive, searchable filenames
2. Use snake_case or kebab-case for filenames
3. Keep names under 50 characters
4. Include key identifying information
5. Avoid special characters except underscore and hyphen
6. Confidence should be 0.0-1.0 based on content quality
7. Categories should be broad (documents, media, reports, etc.)
8. Subcategories should be more specific
9. Tags should be relevant keywords"""

        type_specific = {
            'pdf': """
For PDF files, focus on:
- Document type (report, manual, invoice, etc.)
- Subject matter or topic
- Date if available
- Author or organization
- Version if applicable

Example: "quarterly_financial_report_2024_q1" or "user_manual_software_v2"
""",
            'document': """
For Word documents, focus on:
- Document purpose (letter, proposal, memo, etc.)
- Main topic or subject
- Date if available
- Author or recipient
- Project name if applicable

Example: "project_proposal_website_redesign" or "meeting_minutes_2024_03_15"
""",
            'audio': """
For audio files, focus on:
- Song title and artist for music
- Topic or subject for recordings
- Date for meetings or lectures
- Episode number for podcasts
- Genre or type

Example: "podcast_episode_42_ai_trends" or "meeting_recording_team_standup_2024_03_15"
""",
            'video': """
For video files, focus on:
- Content type (presentation, tutorial, movie, etc.)
- Main subject or title
- Date for recordings
- Episode or part number
- Quality or format info if relevant

Example: "tutorial_python_basics_part_01" or "presentation_quarterly_review_2024_q1"
"""
        }
        
        # Add file-type specific guidelines
        type_specific = {
            'pdf': "\nFor PDF files: Analyze for contracts, reports, presentations, or legal documents. Include document purpose and business context.",
            'document': "\nFor Word documents: Focus on document type (memo, policy, procedure, contract draft). Include authoring context.",
            'text': "\nFor text files: Determine if technical documentation, meeting notes, or business correspondence. Include purpose and audience.",
            'audio': "\nFor audio files: Consider if meeting recordings, training materials, or legal depositions. Note confidentiality.",
            'video': "\nFor video files: Assess if training content, presentations, or recorded meetings. Consider retention requirements."
        }
        
        return base_prompt + type_specific.get(file_type, "")
    
    def _validate_enhanced_analysis_result(self, result: Dict, original_name: str, classification: Dict) -> Dict:
        """Enhanced validation with legal and business context"""
        
        # Ensure all enhanced fields exist
        validated = {
            'suggested_name': result.get('suggested_name', original_name),
            'category': result.get('category', 'uncategorized'),
            'subcategory': result.get('subcategory', ''),
            'confidence': max(0.0, min(1.0, result.get('confidence', 0.5))),
            'reasoning': result.get('reasoning', ''),
            'tags': result.get('tags', []),
            'legal_classification': result.get('legal_classification', 'general'),
            'sensitivity_level': result.get('sensitivity_level', 'low'),
            'retention_period': result.get('retention_period', '7'),
            'compliance_notes': result.get('compliance_notes', ''),
            'priority_level': result.get('priority_level', 'normal')
        }
        
        # Clean and validate suggested name
        suggested_name = validated['suggested_name']
        if not suggested_name or suggested_name.strip() == '':
            suggested_name = original_name
        
        validated['suggested_name'] = self._clean_filename(suggested_name)
        
        # Validate legal classification
        valid_legal_classifications = ['contract', 'compliance', 'financial', 'hr', 'general']
        if validated['legal_classification'] not in valid_legal_classifications:
            validated['legal_classification'] = 'general'
        
        # Validate sensitivity level
        valid_sensitivity_levels = ['low', 'medium', 'high', 'confidential']
        if validated['sensitivity_level'] not in valid_sensitivity_levels:
            validated['sensitivity_level'] = 'low'
        
        # Validate priority level
        valid_priority_levels = ['low', 'normal', 'high', 'urgent']
        if validated['priority_level'] not in valid_priority_levels:
            validated['priority_level'] = 'normal'
        
        # Ensure tags is a list and limit to 10
        if not isinstance(validated['tags'], list):
            validated['tags'] = []
        validated['tags'] = validated['tags'][:10]
        
        # Add classification insights to tags
        if classification.get('legal_category'):
            validated['tags'].append(classification['legal_category'])
        if classification.get('document_type'):
            validated['tags'].append(classification['document_type'])
        
        return validated
    
    def _enhanced_fallback_analysis(self, original_name: str, file_type: str, content: Dict) -> Dict:
        """Enhanced fallback analysis with basic intelligence"""
        
        # Try to extract some intelligence from content even without AI
        text_content = content.get('text', '').lower()
        
        # Basic categorization
        category_map = {
            'pdf': 'documents',
            'document': 'documents', 
            'text': 'documents',
            'audio': 'media',
            'video': 'media'
        }
        
        # Basic legal/business detection
        legal_classification = 'general'
        sensitivity_level = 'low'
        
        if any(word in text_content for word in ['contract', 'agreement', 'legal']):
            legal_classification = 'contract'
            sensitivity_level = 'medium'
        elif any(word in text_content for word in ['financial', 'budget', 'revenue']):
            legal_classification = 'financial'
        elif any(word in text_content for word in ['employee', 'personnel', 'hr']):
            legal_classification = 'hr'
        elif any(word in text_content for word in ['compliance', 'policy', 'procedure']):
            legal_classification = 'compliance'
        
        # Basic tags from content
        tags = [file_type]
        if 'meeting' in text_content:
            tags.append('meeting')
        if 'report' in text_content:
            tags.append('report')
        if 'presentation' in text_content:
            tags.append('presentation')
        
        return {
            'suggested_name': self._clean_filename(original_name.rsplit('.', 1)[0]),
            'category': category_map.get(file_type, 'uncategorized'),
            'subcategory': file_type,
            'confidence': 0.3,
            'reasoning': 'AI analysis unavailable, using intelligent fallback categorization',
            'tags': tags,
            'legal_classification': legal_classification,
            'sensitivity_level': sensitivity_level,
            'retention_period': '7',
            'compliance_notes': 'Review manually for compliance requirements',
            'priority_level': 'normal'
        }
    
    def _validate_analysis_result(self, result: Dict, original_name: str) -> Dict:
        """Validate and clean AI analysis result"""
        
        # Ensure required fields exist
        validated = {
            'suggested_name': result.get('suggested_name', original_name),
            'category': result.get('category', 'uncategorized'),
            'subcategory': result.get('subcategory', ''),
            'confidence': max(0.0, min(1.0, result.get('confidence', 0.5))),
            'reasoning': result.get('reasoning', ''),
            'tags': result.get('tags', [])
        }
        
        # Clean suggested name
        suggested_name = validated['suggested_name']
        if not suggested_name or suggested_name.strip() == '':
            suggested_name = original_name
        
        # Remove invalid characters and limit length
        suggested_name = self._clean_filename(suggested_name)
        validated['suggested_name'] = suggested_name
        
        # Ensure tags is a list
        if not isinstance(validated['tags'], list):
            validated['tags'] = []
        
        # Limit tags
        validated['tags'] = validated['tags'][:10]
        
        return validated
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename to be filesystem-safe"""
        import re
        
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', '_', filename)  # Replace spaces with underscores
        filename = re.sub(r'[^\w\-_.]', '', filename)  # Keep only alphanumeric, hyphens, underscores, dots
        filename = re.sub(r'_+', '_', filename)  # Replace multiple underscores with single
        filename = filename.strip('._-')  # Remove leading/trailing special chars
        
        # Limit length
        if len(filename) > 50:
            filename = filename[:50].rsplit('_', 1)[0]  # Break at word boundary
        
        return filename or 'unnamed_file'
    
    def _fallback_analysis(self, original_name: str, file_type: str) -> Dict:
        """Provide fallback analysis when AI fails"""
        
        # Basic categorization based on file type
        category_map = {
            'pdf': 'documents',
            'document': 'documents',
            'audio': 'media',
            'video': 'media'
        }
        
        return {
            'suggested_name': self._clean_filename(original_name.rsplit('.', 1)[0]),
            'category': category_map.get(file_type, 'uncategorized'),
            'subcategory': file_type,
            'confidence': 0.1,
            'reasoning': 'AI analysis failed, using basic categorization',
            'tags': [file_type]
        }
    
    def generate_batch_summary(self, processed_files: list) -> Dict:
        """Generate a summary of batch processing results"""
        
        try:
            # Prepare summary data
            summary_data = {
                'total_files': len(processed_files),
                'categories': {},
                'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'file_types': {}
            }
            
            for file_info in processed_files:
                analysis = file_info.get('analysis', {})
                
                # Count categories
                category = analysis.get('category', 'uncategorized')
                summary_data['categories'][category] = summary_data['categories'].get(category, 0) + 1
                
                # Count confidence levels
                confidence = analysis.get('confidence', 0)
                if confidence >= 0.7:
                    summary_data['confidence_distribution']['high'] += 1
                elif confidence >= 0.4:
                    summary_data['confidence_distribution']['medium'] += 1
                else:
                    summary_data['confidence_distribution']['low'] += 1
                
                # Count file types
                file_type = file_info.get('type', 'unknown')
                summary_data['file_types'][file_type] = summary_data['file_types'].get(file_type, 0) + 1
            
            # Get AI insights
            summary_text = f"""
Batch Processing Summary:
- Total files processed: {summary_data['total_files']}
- Categories found: {', '.join(summary_data['categories'].keys())}
- File types: {', '.join(summary_data['file_types'].keys())}
- High confidence results: {summary_data['confidence_distribution']['high']}
- Medium confidence results: {summary_data['confidence_distribution']['medium']}
- Low confidence results: {summary_data['confidence_distribution']['low']}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a file organization expert. Analyze this batch processing summary and provide insights and recommendations in JSON format:
{
    "insights": ["insight1", "insight2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "organization_structure": {
        "folder1": ["subcategory1", "subcategory2"],
        "folder2": ["subcategory3"]
    }
}"""
                    },
                    {
                        "role": "user",
                        "content": summary_text
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            ai_insights = json.loads(response.choices[0].message.content)
            summary_data.update(ai_insights)
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Batch summary generation failed: {str(e)}")
            return {
                'total_files': len(processed_files),
                'error': str(e)
            }

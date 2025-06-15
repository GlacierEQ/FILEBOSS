"""
Multi-Provider AI Analysis Engine
Supports multiple AI providers and local processing for cost-effective document analysis
"""

import json
import os
import logging
import re
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class MultiAIAnalyzer:
    """Cost-effective AI analyzer with multiple provider support and local processing"""
    
    def __init__(self):
        self.available_providers = self._detect_available_providers()
        self.fallback_enabled = True
        
        # Enhanced pattern-based classification (no API required)
        self.document_patterns = {
            'legal_documents': {
                'contract': ['agreement', 'contract', 'terms', 'conditions', 'whereas', 'party', 'parties'],
                'motion': ['motion', 'petition', 'court', 'honorable', 'plaintiff', 'defendant'],
                'compliance': ['compliance', 'audit', 'sox', 'gdpr', 'hipaa', 'regulation'],
                'custody': ['custody', 'visitation', 'parenting', 'child', 'guardian', 'hrs 571'],
                'corporate': ['corporation', 'llc', 'board', 'shareholder', 'bylaws', 'resolution']
            },
            'business_documents': {
                'financial': ['revenue', 'profit', 'loss', 'balance', 'income', 'expense', 'budget'],
                'hr': ['employee', 'salary', 'benefits', 'performance', 'hiring', 'termination'],
                'strategy': ['strategic', 'planning', 'goals', 'objectives', 'roadmap', 'vision'],
                'operations': ['process', 'procedure', 'workflow', 'operations', 'sop', 'manual'],
                'marketing': ['marketing', 'campaign', 'brand', 'advertising', 'promotion', 'customer']
            },
            'technical_documents': {
                'code': ['function', 'class', 'import', 'def', 'return', 'variable'],
                'documentation': ['readme', 'documentation', 'guide', 'manual', 'instructions'],
                'api': ['api', 'endpoint', 'request', 'response', 'json', 'rest'],
                'database': ['database', 'sql', 'query', 'table', 'schema', 'migration']
            }
        }
        
        # Sensitivity indicators
        self.sensitivity_patterns = {
            'public': ['public', 'published', 'press release', 'announcement'],
            'internal': ['internal', 'company', 'staff', 'team'],
            'confidential': ['confidential', 'private', 'restricted', 'proprietary'],
            'classified': ['classified', 'top secret', 'eyes only', 'restricted access']
        }
        
        # Priority indicators
        self.priority_patterns = {
            'low': ['informational', 'reference', 'archive'],
            'normal': ['standard', 'routine', 'regular'],
            'high': ['important', 'urgent', 'priority', 'deadline'],
            'critical': ['critical', 'emergency', 'immediate', 'asap', 'urgent']
        }
        
    def _detect_available_providers(self) -> Dict[str, bool]:
        """Detect which AI providers are available"""
        providers = {
            'anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'local_ollama': self._check_ollama_available(),
            'huggingface': bool(os.getenv('HUGGINGFACE_API_KEY')),
            'pattern_based': True  # Always available
        }
        
        logger.info(f"Available AI providers: {[k for k, v in providers.items() if v]}")
        return providers
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running locally"""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def analyze_document(self, content: Dict, file_type: str, filename: str) -> Dict:
        """Analyze document using best available method"""
        
        # Start with pattern-based analysis (always available)
        base_analysis = self._pattern_based_analysis(content, file_type, filename)
        
        # Try to enhance with AI if available
        if self.available_providers.get('anthropic'):
            return self._enhance_with_anthropic(base_analysis, content, filename)
        elif self.available_providers.get('local_ollama'):
            return self._enhance_with_ollama(base_analysis, content, filename)
        elif self.available_providers.get('huggingface'):
            return self._enhance_with_huggingface(base_analysis, content, filename)
        else:
            logger.info("Using pattern-based analysis (no AI provider available)")
            return base_analysis
    
    def _pattern_based_analysis(self, content: Dict, file_type: str, filename: str) -> Dict:
        """Comprehensive pattern-based document analysis"""
        
        text_content = content.get('text', '').lower()
        filename_lower = filename.lower()
        combined_text = f"{text_content} {filename_lower}"
        
        # Document classification
        doc_category, doc_subcategory = self._classify_document(combined_text)
        
        # Sensitivity analysis
        sensitivity = self._determine_sensitivity(combined_text)
        
        # Priority analysis
        priority = self._determine_priority(combined_text)
        
        # Generate intelligent filename
        suggested_name = self._generate_smart_filename(
            content, filename, doc_category, doc_subcategory
        )
        
        # Extract key terms and tags
        tags = self._extract_tags(combined_text, doc_category)
        
        # Legal-specific analysis
        legal_info = self._analyze_legal_aspects(combined_text)
        
        # Business context analysis
        business_info = self._analyze_business_context(combined_text)
        
        return {
            'suggested_name': suggested_name,
            'category': doc_category,
            'subcategory': doc_subcategory,
            'confidence': self._calculate_confidence(combined_text, doc_category),
            'reasoning': f"Pattern-based analysis: Identified as {doc_category}/{doc_subcategory}",
            'tags': tags,
            'sensitivity_level': sensitivity,
            'business_priority': priority,
            'legal_classification': legal_info.get('classification', 'general'),
            'compliance_requirements': legal_info.get('compliance', []),
            'retention_period': legal_info.get('retention', '3'),
            'business_context': business_info,
            'analysis_method': 'pattern_based'
        }
    
    def _classify_document(self, text: str) -> tuple:
        """Classify document using pattern matching"""
        
        best_category = 'general'
        best_subcategory = 'document'
        best_score = 0
        
        for category, subcategories in self.document_patterns.items():
            for subcategory, patterns in subcategories.items():
                score = sum(1 for pattern in patterns if pattern in text)
                if score > best_score:
                    best_score = score
                    best_category = category.replace('_', ' ')
                    best_subcategory = subcategory
        
        return best_category, best_subcategory
    
    def _determine_sensitivity(self, text: str) -> str:
        """Determine document sensitivity level"""
        
        for level, patterns in self.sensitivity_patterns.items():
            if any(pattern in text for pattern in patterns):
                return level
        
        # Default sensitivity based on content type
        if any(term in text for term in ['legal', 'contract', 'agreement', 'confidential']):
            return 'confidential'
        elif any(term in text for term in ['financial', 'revenue', 'salary', 'budget']):
            return 'internal'
        else:
            return 'internal'
    
    def _determine_priority(self, text: str) -> str:
        """Determine document priority level"""
        
        for level, patterns in self.priority_patterns.items():
            if any(pattern in text for pattern in patterns):
                return level
        
        # Context-based priority
        if any(term in text for term in ['court', 'deadline', 'compliance', 'audit']):
            return 'high'
        elif any(term in text for term in ['contract', 'agreement', 'legal']):
            return 'high'
        else:
            return 'normal'
    
    def _generate_smart_filename(self, content: Dict, original_filename: str, 
                                category: str, subcategory: str) -> str:
        """Generate intelligent filename based on content analysis"""
        
        text = content.get('text', '')
        
        # Extract date if present
        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
        date_str = date_match.group(1).replace('/', '_') if date_match else None
        
        # Extract key entities
        entities = self._extract_key_entities(text)
        
        # Build filename components
        components = []
        
        # Add category prefix
        if subcategory != 'document':
            components.append(subcategory)
        
        # Add key entity
        if entities:
            components.append(entities[0][:20])  # Limit length
        
        # Add date
        if date_str:
            components.append(date_str)
        
        # Add document type suffix
        if any(term in text.lower() for term in ['draft', 'final', 'revised']):
            for term in ['draft', 'final', 'revised']:
                if term in text.lower():
                    components.append(term)
                    break
        
        # Fallback to cleaned original name
        if not components:
            base_name = Path(original_filename).stem
            components.append(re.sub(r'[^\w\s-]', '', base_name)[:30])
        
        # Clean and join
        filename = '_'.join(components)
        filename = re.sub(r'[^\w\s-]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('_')[:50]  # Limit total length
        
        return filename or 'document'
    
    def _extract_key_entities(self, text: str) -> List[str]:
        """Extract key entities from text using pattern matching"""
        
        entities = []
        
        # Company names (capitalized words followed by Inc, LLC, Corp, etc.)
        company_pattern = r'\b([A-Z][a-zA-Z\s&]{2,30}(?:Inc|LLC|Corp|Corporation|Company|Co)\.?)\b'
        companies = re.findall(company_pattern, text)
        entities.extend(companies[:2])
        
        # Person names (Title + Capitalized Name)
        name_pattern = r'\b(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        names = re.findall(name_pattern, text)
        entities.extend(names[:2])
        
        # Contract/Agreement types
        contract_pattern = r'\b([A-Z][a-zA-Z\s]{5,25}(?:Agreement|Contract|Motion|Petition))\b'
        contracts = re.findall(contract_pattern, text)
        entities.extend(contracts[:1])
        
        return [self._clean_entity(entity) for entity in entities]
    
    def _clean_entity(self, entity: str) -> str:
        """Clean extracted entity for filename use"""
        entity = re.sub(r'[^\w\s]', '', entity)
        entity = re.sub(r'\s+', '_', entity)
        return entity.strip('_')[:20]
    
    def _extract_tags(self, text: str, category: str) -> List[str]:
        """Extract relevant tags based on content and category"""
        
        tags = [category.replace(' ', '_')]
        
        # Legal tags
        if 'legal' in category:
            legal_tags = ['contract', 'motion', 'compliance', 'court', 'statute']
            tags.extend([tag for tag in legal_tags if tag in text])
        
        # Business tags
        if 'business' in category:
            business_tags = ['financial', 'strategic', 'operational', 'hr', 'marketing']
            tags.extend([tag for tag in business_tags if tag in text])
        
        # Date-based tags
        current_year = str(2024)
        if current_year in text:
            tags.append(current_year)
        
        # Urgency tags
        if any(urgent in text for urgent in ['urgent', 'asap', 'immediate', 'emergency']):
            tags.append('urgent')
        
        # Confidentiality tags
        if any(conf in text for conf in ['confidential', 'private', 'restricted']):
            tags.append('confidential')
        
        return list(set(tags))[:10]  # Limit to 10 unique tags
    
    def _analyze_legal_aspects(self, text: str) -> Dict:
        """Analyze legal aspects of the document"""
        
        legal_info = {
            'classification': 'general',
            'compliance': [],
            'retention': '3'
        }
        
        # Legal document classification
        if any(term in text for term in ['contract', 'agreement', 'terms']):
            legal_info['classification'] = 'contract'
            legal_info['retention'] = '7'
        elif any(term in text for term in ['motion', 'petition', 'court']):
            legal_info['classification'] = 'litigation'
            legal_info['retention'] = '10'
        elif any(term in text for term in ['compliance', 'audit', 'regulation']):
            legal_info['classification'] = 'compliance'
            legal_info['retention'] = '7'
        
        # Compliance requirements
        if 'sox' in text or 'sarbanes' in text:
            legal_info['compliance'].append('SOX')
        if 'gdpr' in text:
            legal_info['compliance'].append('GDPR')
        if 'hipaa' in text:
            legal_info['compliance'].append('HIPAA')
        
        return legal_info
    
    def _analyze_business_context(self, text: str) -> Dict:
        """Analyze business context of the document"""
        
        context = {
            'department': 'general',
            'process_type': 'standard',
            'stakeholders': []
        }
        
        # Department identification
        if any(term in text for term in ['finance', 'accounting', 'budget']):
            context['department'] = 'finance'
        elif any(term in text for term in ['hr', 'human resources', 'employee']):
            context['department'] = 'hr'
        elif any(term in text for term in ['legal', 'compliance', 'contract']):
            context['department'] = 'legal'
        elif any(term in text for term in ['marketing', 'sales', 'customer']):
            context['department'] = 'marketing'
        
        # Process type
        if any(term in text for term in ['strategic', 'planning', 'roadmap']):
            context['process_type'] = 'strategic'
        elif any(term in text for term in ['operational', 'process', 'workflow']):
            context['process_type'] = 'operational'
        
        return context
    
    def _calculate_confidence(self, text: str, category: str) -> float:
        """Calculate confidence score for classification"""
        
        if category == 'general':
            return 0.3
        
        # Count matching patterns
        pattern_matches = 0
        total_patterns = 0
        
        for cat, subcats in self.document_patterns.items():
            if category.replace(' ', '_') == cat:
                for patterns in subcats.values():
                    total_patterns += len(patterns)
                    pattern_matches += sum(1 for pattern in patterns if pattern in text)
        
        if total_patterns == 0:
            return 0.5
        
        confidence = min(0.95, 0.4 + (pattern_matches / total_patterns) * 0.5)
        return round(confidence, 2)
    
    def _enhance_with_anthropic(self, base_analysis: Dict, content: Dict, filename: str) -> Dict:
        """Enhance analysis using Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            
            prompt = f"""
            Analyze this document and enhance the classification:
            
            Filename: {filename}
            Content: {content.get('text', '')[:2000]}
            
            Current analysis: {base_analysis}
            
            Provide enhanced analysis in JSON format with improved:
            - suggested_name
            - category/subcategory
            - confidence score
            - reasoning
            - tags
            """
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            enhanced = json.loads(response.content[0].text)
            base_analysis.update(enhanced)
            base_analysis['analysis_method'] = 'anthropic_enhanced'
            
        except Exception as e:
            logger.warning(f"Anthropic enhancement failed: {e}")
        
        return base_analysis
    
    def _enhance_with_ollama(self, base_analysis: Dict, content: Dict, filename: str) -> Dict:
        """Enhance analysis using local Ollama"""
        try:
            import requests
            
            prompt = f"""
            Document: {filename}
            Content: {content.get('text', '')[:1500]}
            
            Suggest a better filename and provide 3 relevant tags.
            Response format: filename|tag1,tag2,tag3
            """
            
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama2',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '')
                if '|' in result:
                    filename_part, tags_part = result.split('|', 1)
                    base_analysis['suggested_name'] = filename_part.strip()
                    base_analysis['tags'] = [tag.strip() for tag in tags_part.split(',')]
                    base_analysis['analysis_method'] = 'ollama_enhanced'
                    base_analysis['confidence'] = min(0.8, base_analysis['confidence'] + 0.1)
            
        except Exception as e:
            logger.warning(f"Ollama enhancement failed: {e}")
        
        return base_analysis
    
    def _enhance_with_huggingface(self, base_analysis: Dict, content: Dict, filename: str) -> Dict:
        """Enhance analysis using Hugging Face API"""
        try:
            import requests
            
            api_key = os.getenv('HUGGINGFACE_API_KEY')
            headers = {"Authorization": f"Bearer {api_key}"}
            
            # Use text classification model
            api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            
            candidate_labels = ["legal document", "business document", "technical document", 
                              "financial report", "contract", "meeting notes"]
            
            payload = {
                "inputs": content.get('text', '')[:500],
                "parameters": {"candidate_labels": candidate_labels}
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'labels' in result and result['labels']:
                    best_label = result['labels'][0]
                    confidence = result['scores'][0]
                    
                    base_analysis['category'] = best_label
                    base_analysis['confidence'] = min(0.9, confidence)
                    base_analysis['analysis_method'] = 'huggingface_enhanced'
            
        except Exception as e:
            logger.warning(f"Hugging Face enhancement failed: {e}")
        
        return base_analysis
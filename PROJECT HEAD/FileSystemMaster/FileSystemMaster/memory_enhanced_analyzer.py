"""
Memory-Enhanced AI Analyzer with Mem0 Integration
Advanced file analysis that learns and remembers user preferences
"""

import json
import os
import logging
from typing import Dict, Optional, List
from openai import OpenAI
from mem0 import Memory

logger = logging.getLogger(__name__)

class MemoryEnhancedAnalyzer:
    """AI analyzer with persistent memory capabilities using Mem0"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        
        # Initialize Mem0 for persistent learning
        self.memory = Memory()
        
        # Enhanced pattern recognition with memory integration
        self.legal_intelligence = {
            'contract_types': ['service_agreement', 'nda', 'employment', 'licensing', 'partnership'],
            'compliance_frameworks': ['sox', 'gdpr', 'hipaa', 'pci_dss', 'iso_27001'],
            'legal_entities': ['corporation', 'llc', 'partnership', 'trust', 'government'],
            'jurisdictions': ['federal', 'state', 'international', 'regulatory']
        }
        
        # Business context patterns
        self.business_intelligence = {
            'document_categories': ['strategic', 'operational', 'financial', 'legal', 'hr'],
            'urgency_indicators': ['urgent', 'critical', 'deadline', 'time_sensitive'],
            'confidentiality_markers': ['confidential', 'proprietary', 'restricted', 'classified'],
            'stakeholder_types': ['board', 'executives', 'legal', 'compliance', 'audit']
        }
        
        # Load user preferences from memory
        self.user_preferences = self._load_user_preferences()
        
    def _load_user_preferences(self) -> Dict:
        """Load user naming and organization preferences from Mem0"""
        try:
            memories = self.memory.search("file organization preferences")
            preferences = {
                'naming_style': 'professional',
                'category_structure': 'hierarchical',
                'retention_awareness': True,
                'compliance_priority': 'high'
            }
            
            # Extract preferences from memory
            for memory in memories:
                if 'naming_style' in memory.get('text', ''):
                    # Parse memory for specific preferences
                    pass
                    
            return preferences
        except Exception as e:
            logger.warning(f"Could not load preferences from memory: {e}")
            return {'naming_style': 'professional', 'category_structure': 'hierarchical'}
    
    def analyze_with_memory(self, content: Dict, file_type: str, original_name: str, 
                           user_context: Optional[Dict] = None) -> Dict:
        """Enhanced analysis with memory-powered intelligence"""
        
        try:
            # Pre-analysis with memory context
            memory_context = self._get_memory_context(content, original_name)
            classification = self._classify_with_intelligence(content, original_name, memory_context)
            
            # Enhanced analysis with learned preferences
            analysis_prompt = self._create_memory_enhanced_prompt(
                content, file_type, original_name, classification, memory_context
            )
            
            # AI analysis with memory context
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_memory_enhanced_system_prompt(classification, memory_context)
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and enhance with memory insights
            validated_result = self._validate_with_memory(result, original_name, classification, memory_context)
            
            # Store learning for future use
            self._store_analysis_learning(validated_result, content, user_context)
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Memory-enhanced analysis failed: {str(e)}")
            return self._intelligent_fallback_with_memory(original_name, file_type, content)
    
    def _get_memory_context(self, content: Dict, original_name: str) -> Dict:
        """Retrieve relevant context from Mem0 based on file content"""
        
        memory_context = {
            'similar_files': [],
            'user_patterns': [],
            'organization_rules': [],
            'learned_preferences': {}
        }
        
        try:
            # Search for similar files processed before
            text_content = content.get('text', '')[:1000]  # First 1000 chars for search
            search_query = f"file analysis {original_name} {text_content[:100]}"
            
            similar_memories = self.memory.search(search_query, limit=5)
            memory_context['similar_files'] = similar_memories
            
            # Get user organization patterns
            pattern_memories = self.memory.search("organization patterns naming conventions")
            memory_context['user_patterns'] = pattern_memories
            
            # Get specific rules for this type of document
            file_type_query = f"file type {content.get('type', 'document')} organization rules"
            rule_memories = self.memory.search(file_type_query)
            memory_context['organization_rules'] = rule_memories
            
        except Exception as e:
            logger.warning(f"Memory context retrieval failed: {e}")
        
        return memory_context
    
    def _classify_with_intelligence(self, content: Dict, original_name: str, memory_context: Dict) -> Dict:
        """Advanced classification with memory-enhanced intelligence"""
        
        text_content = content.get('text', '').lower()
        filename_lower = original_name.lower()
        
        classification = {
            'legal_category': None,
            'business_category': None,
            'document_type': None,
            'sensitivity_level': 'internal',
            'urgency_level': 'normal',
            'stakeholder_access': 'team',
            'compliance_requirements': [],
            'retention_period': 3,
            'memory_insights': [],
            'learned_patterns': []
        }
        
        # Enhanced legal pattern detection
        for category, types in self.legal_intelligence.items():
            for pattern in types:
                if pattern in text_content or pattern in filename_lower:
                    classification['legal_category'] = pattern
                    classification['memory_insights'].append(f"Legal pattern: {pattern}")
        
        # Business intelligence classification
        for category, indicators in self.business_intelligence.items():
            for indicator in indicators:
                if indicator in text_content or indicator in filename_lower:
                    if category == 'urgency_indicators':
                        classification['urgency_level'] = 'high'
                    elif category == 'confidentiality_markers':
                        classification['sensitivity_level'] = 'confidential'
                    classification['memory_insights'].append(f"Business indicator: {indicator}")
        
        # Apply learned patterns from memory
        if memory_context.get('similar_files'):
            for memory in memory_context['similar_files']:
                memory_text = memory.get('text', '').lower()
                if 'classification:' in memory_text:
                    classification['learned_patterns'].append(memory_text)
        
        return classification
    
    def _create_memory_enhanced_prompt(self, content: Dict, file_type: str, original_name: str,
                                     classification: Dict, memory_context: Dict) -> str:
        """Create analysis prompt enhanced with memory context"""
        
        prompt_parts = [
            "ENHANCED FILE ANALYSIS WITH MEMORY CONTEXT",
            f"File: {original_name}",
            f"Type: {file_type}",
            f"Legal Category: {classification.get('legal_category', 'general')}",
            f"Business Category: {classification.get('business_category', 'general')}",
            f"Sensitivity: {classification.get('sensitivity_level', 'internal')}",
            ""
        ]
        
        # Add memory insights
        if classification.get('memory_insights'):
            prompt_parts.append("MEMORY INSIGHTS:")
            prompt_parts.extend([f"- {insight}" for insight in classification['memory_insights']])
            prompt_parts.append("")
        
        # Add learned patterns
        if classification.get('learned_patterns'):
            prompt_parts.append("LEARNED PATTERNS:")
            prompt_parts.extend([f"- {pattern}" for pattern in classification['learned_patterns'][:3]])
            prompt_parts.append("")
        
        # Add similar file context
        if memory_context.get('similar_files'):
            prompt_parts.append("SIMILAR FILES PROCESSED:")
            for memory in memory_context['similar_files'][:3]:
                prompt_parts.append(f"- {memory.get('text', '')[:100]}...")
            prompt_parts.append("")
        
        # Add file content
        if content.get('text'):
            prompt_parts.append("DOCUMENT CONTENT:")
            prompt_parts.append(content['text'][:3000])
        
        return "\n".join(prompt_parts)
    
    def _get_memory_enhanced_system_prompt(self, classification: Dict, memory_context: Dict) -> str:
        """Generate system prompt with memory-enhanced intelligence"""
        
        base_prompt = """You are an advanced AI legal and business document analyst with persistent memory capabilities. You learn from previous analyses and user preferences to provide increasingly intelligent file organization.

MEMORY-ENHANCED ANALYSIS CAPABILITIES:
- Learn from user feedback and corrections
- Remember successful naming conventions  
- Adapt to organizational preferences
- Maintain consistency across similar documents
- Apply legal and compliance intelligence

OUTPUT FORMAT (JSON):
{
    "suggested_name": "intelligent_memory_informed_filename",
    "category": "primary_category_based_on_learning",
    "subcategory": "specific_subcategory",
    "confidence": 0.95,
    "reasoning": "Memory-enhanced rationale with learned insights",
    "tags": ["memory_tag1", "legal_tag2", "business_tag3"],
    "legal_classification": "contract|compliance|litigation|corporate|ip|employment|financial|general",
    "sensitivity_level": "public|internal|confidential|restricted|classified",
    "retention_period": "years_or_permanent_based_on_legal_requirements",
    "compliance_requirements": ["sox", "gdpr", "hipaa", "etc"],
    "stakeholder_access": "public|team|department|executive|legal_only",
    "business_priority": "low|normal|high|critical",
    "memory_score": "0.0_to_1.0_based_on_learned_patterns",
    "recommended_workflow": "specific_process_recommendations",
    "audit_trail": "retention_and_compliance_guidance"
}

MEMORY-INFORMED NAMING CONVENTIONS:
- Apply learned user preferences for naming style
- Use consistent patterns from similar documents
- Incorporate legal and business intelligence
- Consider stakeholder access requirements
- Apply retention and compliance standards

INTELLIGENT PATTERN RECOGNITION:
- Contract analysis: parties, terms, effective dates, renewal clauses
- Compliance documents: regulations, audit requirements, remediation plans
- Financial documents: periods, departments, materiality, sox requirements
- Strategic documents: confidentiality, board approval, implementation timelines
- Operational documents: process improvements, efficiency metrics, stakeholder impact"""

        # Add memory-specific context
        if memory_context.get('user_patterns'):
            base_prompt += "\n\nLEARNED USER PATTERNS:"
            for pattern in memory_context['user_patterns'][:3]:
                base_prompt += f"\n- {pattern.get('text', '')[:100]}"
        
        return base_prompt
    
    def _validate_with_memory(self, result: Dict, original_name: str, 
                            classification: Dict, memory_context: Dict) -> Dict:
        """Validate analysis result with memory-enhanced intelligence"""
        
        # Standard validation with memory enhancements
        validated = {
            'suggested_name': result.get('suggested_name', original_name),
            'category': result.get('category', 'business_documents'),
            'subcategory': result.get('subcategory', 'general'),
            'confidence': max(0.0, min(1.0, result.get('confidence', 0.5))),
            'reasoning': result.get('reasoning', 'Memory-enhanced analysis'),
            'tags': result.get('tags', []),
            'legal_classification': result.get('legal_classification', 'general'),
            'sensitivity_level': result.get('sensitivity_level', 'internal'),
            'retention_period': result.get('retention_period', '3'),
            'compliance_requirements': result.get('compliance_requirements', []),
            'stakeholder_access': result.get('stakeholder_access', 'team'),
            'business_priority': result.get('business_priority', 'normal'),
            'memory_score': result.get('memory_score', 0.0),
            'recommended_workflow': result.get('recommended_workflow', 'standard_processing'),
            'audit_trail': result.get('audit_trail', 'standard_retention_policy')
        }
        
        # Apply memory-learned preferences
        if memory_context.get('similar_files'):
            # Boost confidence if similar patterns found
            validated['confidence'] = min(1.0, validated['confidence'] + 0.1)
            validated['memory_score'] = min(1.0, len(memory_context['similar_files']) * 0.2)
        
        # Clean filename with learned conventions
        validated['suggested_name'] = self._clean_filename_with_memory(
            validated['suggested_name'], memory_context
        )
        
        # Add memory insights to tags
        validated['tags'].extend(['memory_enhanced', 'ai_learned'])
        validated['tags'] = list(set(validated['tags']))[:15]
        
        return validated
    
    def _clean_filename_with_memory(self, filename: str, memory_context: Dict) -> str:
        """Clean filename using learned naming conventions"""
        import re
        
        # Apply standard cleaning
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = re.sub(r'[^\w\-_.]', '', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('._-')
        
        # Apply learned conventions from memory
        # This would incorporate user preferences from memory
        
        if len(filename) > 100:
            filename = filename[:100].rsplit('_', 1)[0]
        
        return filename or 'memory_enhanced_document'
    
    def _store_analysis_learning(self, result: Dict, content: Dict, user_context: Optional[Dict]):
        """Store analysis results in Mem0 for future learning"""
        
        try:
            # Create learning entry
            learning_text = f"""
            File Analysis Learning:
            Name: {result['suggested_name']}
            Category: {result['category']}
            Legal Classification: {result['legal_classification']}
            Sensitivity: {result['sensitivity_level']}
            Confidence: {result['confidence']}
            Business Priority: {result['business_priority']}
            Tags: {', '.join(result['tags'])}
            """
            
            # Store in memory with metadata
            self.memory.add(
                learning_text,
                metadata={
                    "type": "file_analysis",
                    "category": result['category'],
                    "legal_class": result['legal_classification'],
                    "confidence": result['confidence']
                }
            )
            
            # Store specific patterns for future recognition
            if result['confidence'] > 0.8:
                pattern_text = f"High confidence pattern: {result['category']} files should use {result['suggested_name']} naming style"
                self.memory.add(pattern_text, metadata={"type": "naming_pattern"})
                
        except Exception as e:
            logger.warning(f"Could not store learning in memory: {e}")
    
    def _intelligent_fallback_with_memory(self, original_name: str, file_type: str, content: Dict) -> Dict:
        """Intelligent fallback analysis enhanced with memory"""
        
        # Try to get insights from memory even in fallback
        try:
            search_results = self.memory.search(f"file type {file_type}")
            learned_category = 'business_documents'
            
            if search_results:
                # Extract category from most relevant memory
                memory_text = search_results[0].get('text', '')
                if 'category:' in memory_text.lower():
                    learned_category = memory_text.split('category:')[1].split()[0]
        except:
            learned_category = 'business_documents'
        
        return {
            'suggested_name': self._clean_filename_with_memory(original_name.rsplit('.', 1)[0], {}),
            'category': learned_category,
            'subcategory': file_type,
            'confidence': 0.4,
            'reasoning': 'Memory-enhanced fallback analysis with learned patterns',
            'tags': [file_type, 'memory_fallback'],
            'legal_classification': 'general',
            'sensitivity_level': 'internal',
            'retention_period': '3',
            'compliance_requirements': [],
            'stakeholder_access': 'team',
            'business_priority': 'normal',
            'memory_score': 0.2,
            'recommended_workflow': 'review_and_classify',
            'audit_trail': 'requires_manual_review'
        }
    
    def get_user_feedback(self, file_id: str, user_corrections: Dict):
        """Process user feedback to improve future analyses"""
        
        try:
            feedback_text = f"""
            User Feedback Learning:
            File ID: {file_id}
            Corrections: {json.dumps(user_corrections)}
            User prefers: {user_corrections.get('preferred_name', 'N/A')}
            Category correction: {user_corrections.get('correct_category', 'N/A')}
            """
            
            self.memory.add(
                feedback_text,
                metadata={
                    "type": "user_feedback",
                    "file_id": file_id,
                    "correction_type": "naming_preference"
                }
            )
            
        except Exception as e:
            logger.error(f"Could not store user feedback: {e}")
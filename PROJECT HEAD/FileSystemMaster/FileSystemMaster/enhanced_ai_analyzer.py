"""
Enhanced AI content analysis module with legal and business intelligence
"""

import json
import os
import logging
from typing import Dict, Optional
from openai import OpenAI
from legal_research_integration import LegalResearchIntegration

logger = logging.getLogger(__name__)

class EnhancedAIAnalyzer:
    """Advanced AI-powered content analysis with legal understanding and business intelligence"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
        # Legal document classification patterns
        self.legal_patterns = {
            'contracts': ['agreement', 'contract', 'terms', 'conditions', 'party', 'whereas', 'covenant'],
            'compliance': ['compliance', 'regulation', 'policy', 'procedure', 'audit', 'sox', 'gdpr'],
            'litigation': ['lawsuit', 'litigation', 'court', 'deposition', 'discovery', 'motion'],
            'corporate': ['board', 'resolution', 'bylaws', 'articles', 'incorporation', 'governance'],
            'intellectual_property': ['patent', 'trademark', 'copyright', 'license', 'proprietary'],
            'employment': ['employment', 'termination', 'non-disclosure', 'confidentiality', 'non-compete'],
            'financial_legal': ['securities', 'debt', 'loan', 'mortgage', 'collateral', 'guarantee']
        }
        
        # Business intelligence patterns
        self.business_patterns = {
            'strategic_planning': ['strategy', 'roadmap', 'vision', 'goals', 'objectives', 'kpi'],
            'financial_analysis': ['budget', 'forecast', 'revenue', 'profit', 'cash flow', 'balance sheet'],
            'operational': ['process', 'workflow', 'procedure', 'manual', 'sop', 'operations'],
            'hr_management': ['employee', 'performance', 'review', 'benefits', 'payroll', 'recruitment'],
            'risk_management': ['risk', 'mitigation', 'assessment', 'contingency', 'insurance'],
            'market_research': ['market', 'research', 'analysis', 'competitor', 'customer', 'survey']
        }
        
        # Document retention guidelines (in years)
        self.retention_guidelines = {
            'contracts': 7,
            'financial': 7,
            'tax_records': 7,
            'employment': 7,
            'litigation': 'permanent',
            'intellectual_property': 'permanent',
            'corporate_governance': 'permanent',
            'compliance': 5,
            'marketing': 3,
            'general_business': 3
        }
    
    def analyze_file_content(self, content: Dict, file_type: str, original_name: str) -> Dict:
        """Enhanced analysis with legal and business intelligence"""
        
        try:
            # Pre-classify content for context
            classification = self._classify_content_advanced(content, original_name)
            
            # Prepare enhanced analysis prompt
            analysis_text = self._prepare_legal_business_analysis(
                content, file_type, original_name, classification
            )
            
            # Get enhanced AI analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_legal_business_prompt(file_type, classification)
                    },
                    {
                        "role": "user", 
                        "content": analysis_text
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Very low for consistent legal analysis
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Enhanced validation with legal context
            return self._validate_legal_business_result(result, original_name, classification)
            
        except Exception as e:
            logger.error(f"Enhanced AI analysis failed: {str(e)}")
            return self._intelligent_fallback_analysis(original_name, file_type, content)
    
    def _classify_content_advanced(self, content: Dict, original_name: str) -> Dict:
        """Advanced content classification with legal and business intelligence"""
        
        text_content = content.get('text', '').lower()
        filename_lower = original_name.lower()
        
        classification = {
            'legal_category': None,
            'business_category': None,
            'document_type': None,
            'sensitivity_level': 'standard',
            'confidentiality_level': 'internal',
            'retention_period': 3,
            'compliance_flags': [],
            'business_context': [],
            'legal_context': [],
            'priority_indicators': [],
            'risk_level': 'low'
        }
        
        # Legal pattern detection
        for category, patterns in self.legal_patterns.items():
            if any(pattern in text_content or pattern in filename_lower for pattern in patterns):
                classification['legal_category'] = category
                classification['legal_context'].append(category)
                
                # Set appropriate retention and sensitivity
                if category in ['litigation', 'intellectual_property', 'corporate']:
                    classification['retention_period'] = 'permanent'
                    classification['sensitivity_level'] = 'high'
                elif category in ['contracts', 'employment', 'financial_legal']:
                    classification['retention_period'] = 7
                    classification['sensitivity_level'] = 'medium'
        
        # Business pattern detection
        for category, patterns in self.business_patterns.items():
            if any(pattern in text_content or pattern in filename_lower for pattern in patterns):
                classification['business_category'] = category
                classification['business_context'].append(category)
        
        # Confidentiality detection
        confidential_indicators = ['confidential', 'proprietary', 'restricted', 'classified', 'sensitive']
        if any(indicator in text_content or indicator in filename_lower for indicator in confidential_indicators):
            classification['confidentiality_level'] = 'confidential'
            classification['sensitivity_level'] = 'high'
        
        # Compliance flag detection
        compliance_terms = {
            'sox': 'Sarbanes-Oxley compliance required',
            'gdpr': 'GDPR data protection compliance',
            'hipaa': 'HIPAA healthcare privacy compliance',
            'pci': 'PCI DSS payment card compliance',
            'iso': 'ISO standard compliance'
        }
        
        for term, flag in compliance_terms.items():
            if term in text_content:
                classification['compliance_flags'].append(flag)
        
        # Priority and risk assessment
        urgent_terms = ['urgent', 'critical', 'emergency', 'deadline', 'asap']
        high_risk_terms = ['lawsuit', 'violation', 'breach', 'investigation', 'audit']
        
        if any(term in text_content for term in urgent_terms):
            classification['priority_indicators'].append('urgent')
        
        if any(term in text_content for term in high_risk_terms):
            classification['risk_level'] = 'high'
            classification['priority_indicators'].append('high_risk')
        
        return classification
    
    def _prepare_legal_business_analysis(self, content: Dict, file_type: str, 
                                       original_name: str, classification: Dict) -> str:
        """Prepare comprehensive analysis with legal and business context"""
        
        analysis_parts = [
            f"DOCUMENT ANALYSIS REQUEST",
            f"File Type: {file_type}",
            f"Original Name: {original_name}",
            f"Legal Category: {classification.get('legal_category', 'general business')}",
            f"Business Category: {classification.get('business_category', 'general')}",
            f"Sensitivity Level: {classification.get('sensitivity_level', 'standard')}",
            f"Confidentiality: {classification.get('confidentiality_level', 'internal')}",
            f"Risk Level: {classification.get('risk_level', 'low')}",
            "",
            "CONTENT FOR ANALYSIS:"
        ]
        
        # Enhanced content analysis
        if content.get('text'):
            text_content = content['text'][:4000]  # Expanded for better legal analysis
            analysis_parts.append(f"Document Text:\n{text_content}")
        
        # Metadata analysis
        if content.get('metadata'):
            metadata_text = []
            for key, value in content['metadata'].items():
                if value and str(value).strip():
                    metadata_text.append(f"{key}: {value}")
            
            if metadata_text:
                analysis_parts.append(f"Document Metadata:\n" + "\n".join(metadata_text))
        
        # Legal and compliance context
        if classification.get('compliance_flags'):
            analysis_parts.append(f"Compliance Requirements: {'; '.join(classification['compliance_flags'])}")
        
        if classification.get('legal_context'):
            analysis_parts.append(f"Legal Context: {', '.join(classification['legal_context'])}")
        
        if classification.get('business_context'):
            analysis_parts.append(f"Business Context: {', '.join(classification['business_context'])}")
        
        return "\n\n".join(analysis_parts)
    
    def _get_legal_business_prompt(self, file_type: str, classification: Dict) -> str:
        """Generate comprehensive legal and business analysis prompt"""
        
        legal_category = classification.get('legal_category', 'general')
        business_category = classification.get('business_category', 'general')
        sensitivity = classification.get('sensitivity_level', 'standard')
        
        prompt = f"""You are a senior legal counsel and business analyst with expertise in corporate law, compliance, and document management. You understand the nuances of legal document classification, retention requirements, and business intelligence.

ANALYSIS CONTEXT:
- Legal Category: {legal_category}
- Business Category: {business_category}  
- Sensitivity Level: {sensitivity}
- Document Type: {file_type}

ANALYSIS REQUIREMENTS:
Provide a comprehensive analysis in this exact JSON structure:

{{
    "suggested_name": "professional_descriptive_filename_without_extension",
    "category": "primary_business_category",
    "subcategory": "specific_document_subcategory",
    "confidence": 0.95,
    "reasoning": "Professional explanation of naming and categorization rationale",
    "tags": ["relevant_tag1", "legal_tag2", "business_tag3"],
    "legal_classification": "contract|compliance|litigation|corporate|ip|employment|financial|general",
    "sensitivity_level": "public|internal|confidential|restricted|classified",
    "retention_period": "number_of_years_or_permanent",
    "compliance_requirements": ["applicable_regulations_or_standards"],
    "business_priority": "low|normal|high|critical",
    "risk_assessment": "low|medium|high|critical",
    "recommended_access": "public|team|department|executive|legal_only",
    "legal_review_required": true_or_false,
    "data_classification": "public|internal|confidential|restricted",
    "archival_instructions": "specific_retention_and_disposal_guidance"
}}

PROFESSIONAL NAMING CONVENTIONS:
1. Legal documents: [DocumentType]_[Parties]_[Date]_[Version] (e.g., "service_agreement_acme_corp_2024_03_15_v2")
2. Financial documents: [Period]_[Department]_[DocumentType] (e.g., "2024_q1_financial_report_operations")
3. Compliance documents: [Regulation]_[DocumentType]_[Date] (e.g., "sox_compliance_assessment_2024_annual")
4. Corporate governance: [Entity]_[DocumentType]_[Date] (e.g., "board_resolution_quarterly_meeting_2024_03")
5. HR documents: [DocumentType]_[Category]_[Period] (e.g., "performance_review_senior_management_2024_q1")

LEGAL AND COMPLIANCE INTELLIGENCE:
- Apply appropriate retention schedules based on document type and jurisdiction
- Identify potential attorney-client privilege considerations
- Flag documents requiring legal review or compliance oversight
- Assess data privacy and confidentiality requirements
- Consider litigation hold implications
- Evaluate regulatory compliance requirements (SOX, GDPR, HIPAA, etc.)

BUSINESS INTELLIGENCE FACTORS:
- Strategic importance to organization
- Operational impact and dependencies  
- Financial materiality and implications
- Risk exposure and mitigation requirements
- Stakeholder access and distribution needs
- Decision-making support value"""

        return prompt
    
    def _validate_legal_business_result(self, result: Dict, original_name: str, classification: Dict) -> Dict:
        """Enhanced validation with legal and business logic"""
        
        # Comprehensive validation structure
        validated = {
            'suggested_name': result.get('suggested_name', original_name),
            'category': result.get('category', 'general_business'),
            'subcategory': result.get('subcategory', 'miscellaneous'),
            'confidence': max(0.0, min(1.0, result.get('confidence', 0.5))),
            'reasoning': result.get('reasoning', 'Standard business document classification'),
            'tags': result.get('tags', []),
            'legal_classification': result.get('legal_classification', 'general'),
            'sensitivity_level': result.get('sensitivity_level', 'internal'),
            'retention_period': result.get('retention_period', '3'),
            'compliance_requirements': result.get('compliance_requirements', []),
            'business_priority': result.get('business_priority', 'normal'),
            'risk_assessment': result.get('risk_assessment', 'low'),
            'recommended_access': result.get('recommended_access', 'team'),
            'legal_review_required': result.get('legal_review_required', False),
            'data_classification': result.get('data_classification', 'internal'),
            'archival_instructions': result.get('archival_instructions', 'Standard retention policy applies')
        }
        
        # Clean and validate filename
        suggested_name = validated['suggested_name']
        if not suggested_name or suggested_name.strip() == '':
            suggested_name = original_name
        
        validated['suggested_name'] = self._clean_legal_filename(suggested_name)
        
        # Validate against legal standards
        valid_legal_classifications = ['contract', 'compliance', 'litigation', 'corporate', 'ip', 'employment', 'financial', 'general']
        if validated['legal_classification'] not in valid_legal_classifications:
            validated['legal_classification'] = 'general'
        
        valid_sensitivity_levels = ['public', 'internal', 'confidential', 'restricted', 'classified']
        if validated['sensitivity_level'] not in valid_sensitivity_levels:
            validated['sensitivity_level'] = 'internal'
        
        # Enhance tags with classification insights
        if not isinstance(validated['tags'], list):
            validated['tags'] = []
        
        # Add classification-based tags
        if classification.get('legal_category'):
            validated['tags'].append(f"legal_{classification['legal_category']}")
        if classification.get('business_category'):
            validated['tags'].append(f"business_{classification['business_category']}")
        
        # Limit tags and ensure uniqueness
        validated['tags'] = list(set(validated['tags']))[:12]
        
        return validated
    
    def _clean_legal_filename(self, filename: str) -> str:
        """Clean filename according to legal document standards"""
        import re
        
        # Professional legal document naming
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = re.sub(r'[^\w\-_.]', '', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('._-')
        
        # Ensure professional length
        if len(filename) > 80:  # Legal documents often need longer names
            filename = filename[:80].rsplit('_', 1)[0]
        
        return filename or 'legal_document'
    
    def _intelligent_fallback_analysis(self, original_name: str, file_type: str, content: Dict) -> Dict:
        """Intelligent fallback with legal and business awareness"""
        
        text_content = content.get('text', '').lower()
        
        # Intelligent categorization based on content
        legal_classification = 'general'
        sensitivity_level = 'internal'
        retention_period = '3'
        business_priority = 'normal'
        
        # Basic legal detection
        if any(term in text_content for term in ['contract', 'agreement', 'terms']):
            legal_classification = 'contract'
            sensitivity_level = 'confidential'
            retention_period = '7'
        elif any(term in text_content for term in ['financial', 'budget', 'revenue']):
            legal_classification = 'financial'
            retention_period = '7'
        elif any(term in text_content for term in ['policy', 'procedure', 'compliance']):
            legal_classification = 'compliance'
            retention_period = '5'
        elif any(term in text_content for term in ['employee', 'hr', 'personnel']):
            legal_classification = 'employment'
            retention_period = '7'
        
        # Priority assessment
        if any(term in text_content for term in ['urgent', 'critical', 'deadline']):
            business_priority = 'high'
        
        return {
            'suggested_name': self._clean_legal_filename(original_name.rsplit('.', 1)[0]),
            'category': 'business_documents',
            'subcategory': file_type,
            'confidence': 0.4,
            'reasoning': 'Intelligent fallback analysis based on content patterns and legal best practices',
            'tags': [file_type, legal_classification],
            'legal_classification': legal_classification,
            'sensitivity_level': sensitivity_level,
            'retention_period': retention_period,
            'compliance_requirements': [],
            'business_priority': business_priority,
            'risk_assessment': 'low',
            'recommended_access': 'team',
            'legal_review_required': legal_classification in ['contract', 'compliance'],
            'data_classification': sensitivity_level,
            'archival_instructions': f'Retain for {retention_period} years per standard policy'
        }
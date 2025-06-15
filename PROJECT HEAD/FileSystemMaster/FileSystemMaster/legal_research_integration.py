"""
Legal Research API Integration Module
Integrates CourtListener API and legal research capabilities into file automation
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LegalResearchIntegration:
    """Advanced legal research integration using CourtListener API and Hawaii statutes"""
    
    def __init__(self):
        self.courtlistener_token = os.getenv("COURTLISTENER_API_TOKEN", "27cb3521fc97253116933795c20d3987b11865e9")
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
        
        # Hawaii Revised Statutes (HRS) key provisions for file analysis
        self.hrs_provisions = {
            '571-46': 'Best interests of the child - custody and visitation',
            '571-46(9)': 'Sanctions for interference with court-ordered visitation',
            '571-61': 'Enforcement of custody and visitation orders',
            '571-84': 'Uniform Child Custody Jurisdiction and Enforcement Act',
            '571-91': 'Parenting education requirements',
            '580-41': 'No-fault divorce provisions',
            '584-1': 'Uniform Parentage Act definitions',
            '584-15': 'Paternity establishment procedures'
        }
        
        # Legal document classification patterns
        self.legal_patterns = {
            'custody_documents': [
                'custody', 'visitation', 'parenting plan', 'time sharing',
                'child support', 'best interests', 'parental rights'
            ],
            'divorce_documents': [
                'divorce', 'dissolution', 'separation', 'marital property',
                'alimony', 'spousal support', 'asset division'
            ],
            'court_filings': [
                'motion', 'petition', 'complaint', 'answer', 'affidavit',
                'declaration', 'order', 'judgment', 'decree'
            ],
            'compliance_documents': [
                'parenting education', 'mediation', 'evaluation',
                'guardian ad litem', 'custody evaluator'
            ]
        }
        
        # Federal and state court jurisdictions
        self.jurisdictions = {
            'hawaii_state': 'Hawaii State Courts',
            'hawaii_family': 'Hawaii Family Court',
            'federal_district': 'US District Court - District of Hawaii',
            'ninth_circuit': 'US Court of Appeals - Ninth Circuit'
        }
        
    def analyze_legal_document(self, content: Dict, filename: str) -> Dict:
        """Enhanced legal document analysis with API integration"""
        
        analysis = {
            'legal_type': None,
            'jurisdiction': None,
            'statute_references': [],
            'case_law_relevance': [],
            'compliance_requirements': [],
            'retention_period': 7,  # Default 7 years for legal documents
            'sensitivity_level': 'confidential',
            'legal_priority': 'normal'
        }
        
        text_content = content.get('text', '').lower()
        filename_lower = filename.lower()
        
        # Classify legal document type
        for doc_type, patterns in self.legal_patterns.items():
            for pattern in patterns:
                if pattern in text_content or pattern in filename_lower:
                    analysis['legal_type'] = doc_type
                    break
        
        # Identify Hawaii statute references
        analysis['statute_references'] = self._identify_statute_references(text_content)
        
        # Determine jurisdiction
        analysis['jurisdiction'] = self._determine_jurisdiction(text_content, filename_lower)
        
        # Set compliance requirements based on document type
        analysis['compliance_requirements'] = self._get_compliance_requirements(analysis['legal_type'])
        
        # Determine priority and sensitivity
        if any(urgent in text_content for urgent in ['emergency', 'ex parte', 'temporary restraining']):
            analysis['legal_priority'] = 'critical'
            analysis['sensitivity_level'] = 'restricted'
        elif any(sensitive in text_content for sensitive in ['custody', 'child welfare', 'domestic violence']):
            analysis['legal_priority'] = 'high'
            analysis['sensitivity_level'] = 'confidential'
        
        # Search for relevant case law if CourtListener API is available
        if self.courtlistener_token:
            try:
                relevant_cases = self._search_relevant_cases(text_content, analysis['legal_type'])
                analysis['case_law_relevance'] = relevant_cases
            except Exception as e:
                logger.warning(f"Case law search failed: {e}")
        
        return analysis
    
    def _identify_statute_references(self, text: str) -> List[str]:
        """Identify Hawaii Revised Statute references in document text"""
        
        references = []
        
        # Look for HRS references
        for statute_num, description in self.hrs_provisions.items():
            if statute_num in text or statute_num.replace('-', '.') in text:
                references.append(f"HRS {statute_num}: {description}")
        
        # Look for Hawaii Family Court Rules
        hfcr_patterns = ['hfcr', 'hawaii family court rule', 'family court rule']
        for pattern in hfcr_patterns:
            if pattern in text:
                references.append("Hawaii Family Court Rules (HFCR)")
        
        # Look for federal references
        federal_patterns = ['28 u.s.c.', 'fed. r. civ. p.', 'frcp', 'federal rules']
        for pattern in federal_patterns:
            if pattern in text:
                references.append("Federal Rules and Statutes")
        
        return references
    
    def _determine_jurisdiction(self, text: str, filename: str) -> str:
        """Determine appropriate jurisdiction based on document content"""
        
        # Hawaii state court indicators
        if any(indicator in text for indicator in ['hawaii family court', 'first circuit', 'honolulu']):
            return self.jurisdictions['hawaii_family']
        
        # Federal court indicators  
        if any(indicator in text for indicator in ['federal', 'u.s. district', 'ninth circuit']):
            return self.jurisdictions['federal_district']
        
        # Default to Hawaii state for family law matters
        return self.jurisdictions['hawaii_state']
    
    def _get_compliance_requirements(self, legal_type: str) -> List[str]:
        """Get compliance requirements based on legal document type"""
        
        compliance_map = {
            'custody_documents': [
                'Parenting Education Class (HRS 571-91)',
                'Best Interests Evaluation',
                'Guardian ad Litem Appointment'
            ],
            'divorce_documents': [
                'Financial Disclosure Requirements',
                'Asset Valuation Documentation',
                'Parenting Plan Submission'
            ],
            'court_filings': [
                'Court Filing Deadlines',
                'Service of Process Requirements',
                'Response Time Limits'
            ],
            'compliance_documents': [
                'Continuing Education Requirements',
                'Certification Maintenance',
                'Professional Standards Compliance'
            ]
        }
        
        return compliance_map.get(legal_type, ['Standard Legal Document Retention'])
    
    def _search_relevant_cases(self, text: str, legal_type: str) -> List[Dict]:
        """Search CourtListener API for relevant case law"""
        
        if not self.courtlistener_token:
            return []
        
        # Create search query based on document content and type
        search_terms = self._generate_search_terms(text, legal_type)
        
        headers = {
            'Authorization': f'Token {self.courtlistener_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Search for relevant opinions
            search_url = f"{self.base_url}/search/"
            params = {
                'q': ' AND '.join(search_terms[:3]),  # Limit to top 3 terms
                'type': 'o',  # Opinions
                'court': 'haw hawapp',  # Hawaii courts
                'order_by': 'score desc'
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                cases = []
                
                for result in results.get('results', [])[:5]:  # Top 5 relevant cases
                    cases.append({
                        'case_name': result.get('caseName', 'Unknown'),
                        'court': result.get('court', 'Unknown Court'),
                        'date_filed': result.get('dateFiled', 'Unknown Date'),
                        'relevance_score': result.get('score', 0),
                        'url': f"https://www.courtlistener.com{result.get('absolute_url', '')}"
                    })
                
                return cases
            
        except Exception as e:
            logger.error(f"CourtListener API search failed: {e}")
        
        return []
    
    def _generate_search_terms(self, text: str, legal_type: str) -> List[str]:
        """Generate search terms for case law research"""
        
        # Base terms by legal document type
        base_terms = {
            'custody_documents': ['child custody', 'visitation rights', 'best interests'],
            'divorce_documents': ['divorce', 'marital dissolution', 'property division'],
            'court_filings': ['motion practice', 'civil procedure', 'court rules'],
            'compliance_documents': ['legal compliance', 'professional standards']
        }
        
        terms = base_terms.get(legal_type, ['legal document'])
        
        # Add Hawaii-specific terms
        terms.extend(['Hawaii', 'HRS', 'family court'])
        
        # Extract key legal concepts from text
        legal_concepts = [
            'parental rights', 'child welfare', 'domestic relations',
            'custody modification', 'enforcement', 'contempt'
        ]
        
        for concept in legal_concepts:
            if concept in text.lower():
                terms.append(concept)
        
        return terms[:10]  # Limit to top 10 terms
    
    def get_statute_details(self, statute_reference: str) -> Dict:
        """Get detailed information about a specific Hawaii statute"""
        
        statute_info = {
            'reference': statute_reference,
            'title': self.hrs_provisions.get(statute_reference, 'Unknown Statute'),
            'chapter': statute_reference.split('-')[0] if '-' in statute_reference else 'Unknown',
            'effective_date': 'Check current HRS for effective date',
            'amendments': 'Verify current version in Hawaii Revised Statutes',
            'related_statutes': []
        }
        
        # Add related statute information for common family law provisions
        if statute_reference.startswith('571'):
            statute_info['related_statutes'] = [
                'HRS 571-84 (UCCJEA)',
                'HRS 571-91 (Parenting Education)',
                'HRS 584 (Uniform Parentage Act)'
            ]
        
        return statute_info
    
    def create_legal_summary(self, analysis_results: List[Dict]) -> Dict:
        """Create comprehensive legal analysis summary"""
        
        summary = {
            'total_documents': len(analysis_results),
            'legal_categories': {},
            'jurisdictions': {},
            'statute_references': {},
            'high_priority_items': [],
            'compliance_alerts': []
        }
        
        for analysis in analysis_results:
            # Count legal categories
            legal_type = analysis.get('legal_type', 'unknown')
            summary['legal_categories'][legal_type] = summary['legal_categories'].get(legal_type, 0) + 1
            
            # Count jurisdictions
            jurisdiction = analysis.get('jurisdiction', 'unknown')
            summary['jurisdictions'][jurisdiction] = summary['jurisdictions'].get(jurisdiction, 0) + 1
            
            # Track statute references
            for statute in analysis.get('statute_references', []):
                summary['statute_references'][statute] = summary['statute_references'].get(statute, 0) + 1
            
            # Identify high priority items
            if analysis.get('legal_priority') in ['high', 'critical']:
                summary['high_priority_items'].append({
                    'type': legal_type,
                    'priority': analysis.get('legal_priority'),
                    'sensitivity': analysis.get('sensitivity_level')
                })
            
            # Track compliance requirements
            for requirement in analysis.get('compliance_requirements', []):
                if requirement not in [alert['requirement'] for alert in summary['compliance_alerts']]:
                    summary['compliance_alerts'].append({
                        'requirement': requirement,
                        'applicable_documents': 1
                    })
                else:
                    # Increment count for existing requirement
                    for alert in summary['compliance_alerts']:
                        if alert['requirement'] == requirement:
                            alert['applicable_documents'] += 1
        
        return summary
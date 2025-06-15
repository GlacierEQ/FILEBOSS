#!/usr/bin/env python3
"""
Enhanced Legal File Analysis Demo
Demonstrates the legal research integration and document classification capabilities
"""

import os
import json
from pathlib import Path
from legal_research_integration import LegalResearchIntegration

def demo_legal_analysis():
    """Demonstrate enhanced legal document analysis capabilities"""
    
    print("=" * 70)
    print("ENHANCED LEGAL FILE AUTOMATION SYSTEM DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Initialize legal research integration
    legal_research = LegalResearchIntegration()
    
    # Test files directory
    test_dir = Path("./test_files")
    
    if not test_dir.exists():
        print("Test files directory not found. Creating sample analysis...")
        return demo_with_sample_content()
    
    print(f"Analyzing files in: {test_dir}")
    print()
    
    # Analyze each file
    results = []
    
    for file_path in test_dir.glob("*.txt"):
        print(f"Analyzing: {file_path.name}")
        print("-" * 50)
        
        try:
            # Read file content
            content = {'text': file_path.read_text()}
            
            # Perform legal analysis
            analysis = legal_research.analyze_legal_document(content, file_path.name)
            
            # Display results
            print(f"Legal Type: {analysis.get('legal_type', 'Unknown')}")
            print(f"Jurisdiction: {analysis.get('jurisdiction', 'Unknown')}")
            print(f"Sensitivity: {analysis.get('sensitivity_level', 'Internal')}")
            print(f"Priority: {analysis.get('legal_priority', 'Normal')}")
            print(f"Retention: {analysis.get('retention_period', 3)} years")
            
            if analysis.get('statute_references'):
                print("Statute References:")
                for ref in analysis['statute_references']:
                    print(f"  • {ref}")
            
            if analysis.get('compliance_requirements'):
                print("Compliance Requirements:")
                for req in analysis['compliance_requirements']:
                    print(f"  • {req}")
            
            if analysis.get('case_law_relevance'):
                print("Relevant Case Law:")
                for case in analysis['case_law_relevance']:
                    print(f"  • {case.get('case_name', 'Unknown Case')}")
                    print(f"    Court: {case.get('court', 'Unknown')}")
                    print(f"    Relevance Score: {case.get('relevance_score', 0)}")
            
            results.append({
                'filename': file_path.name,
                'analysis': analysis
            })
            
        except Exception as e:
            print(f"Error analyzing {file_path.name}: {e}")
        
        print()
    
    # Create comprehensive summary
    if results:
        print("=" * 70)
        print("LEGAL ANALYSIS SUMMARY")
        print("=" * 70)
        
        summary = legal_research.create_legal_summary([r['analysis'] for r in results])
        
        print(f"Total Documents Analyzed: {summary['total_documents']}")
        print()
        
        print("Legal Categories:")
        for category, count in summary['legal_categories'].items():
            print(f"  • {category}: {count} documents")
        print()
        
        print("Jurisdictions:")
        for jurisdiction, count in summary['jurisdictions'].items():
            print(f"  • {jurisdiction}: {count} documents")
        print()
        
        if summary['statute_references']:
            print("Most Referenced Statutes:")
            sorted_statutes = sorted(summary['statute_references'].items(), 
                                   key=lambda x: x[1], reverse=True)
            for statute, count in sorted_statutes[:5]:
                print(f"  • {statute}: {count} references")
            print()
        
        if summary['high_priority_items']:
            print(f"High Priority Items: {len(summary['high_priority_items'])}")
            for item in summary['high_priority_items'][:3]:
                print(f"  • {item['type']} - Priority: {item['priority']}")
            print()
        
        if summary['compliance_alerts']:
            print("Compliance Requirements:")
            for alert in summary['compliance_alerts'][:5]:
                print(f"  • {alert['requirement']} ({alert['applicable_documents']} docs)")

def demo_with_sample_content():
    """Demo with sample legal document content"""
    
    legal_research = LegalResearchIntegration()
    
    # Sample legal documents
    sample_docs = [
        {
            'filename': 'custody_motion_2024.txt',
            'content': {
                'text': """
                MOTION FOR MODIFICATION OF CUSTODY ORDER
                
                TO THE HONORABLE COURT:
                
                Petitioner respectfully requests this Court modify the existing custody order 
                pursuant to HRS 571-46 regarding the best interests of the child. The current 
                arrangement is no longer serving the child's welfare due to significant changes 
                in circumstances.
                
                This motion seeks enforcement of visitation rights under HRS 571-61 and 
                requests sanctions for continued interference with court-ordered visitation 
                as provided in HRS 571-46(9).
                
                The Hawaii Family Court has jurisdiction over this matter pursuant to the 
                Uniform Child Custody Jurisdiction and Enforcement Act (HRS 571-84).
                
                Respectfully submitted,
                [Attorney Name]
                """
            }
        },
        {
            'filename': 'compliance_audit_report.txt',
            'content': {
                'text': """
                CONFIDENTIAL - COMPLIANCE AUDIT REPORT
                
                Internal Audit Report - SOX Section 404 Assessment
                Company: TechFlow Industries Inc.
                Audit Period: Q4 2024
                Report Date: March 20, 2025
                
                EXECUTIVE SUMMARY:
                This report presents findings from our Sarbanes-Oxley Section 404 compliance 
                assessment of internal controls over financial reporting.
                
                KEY FINDINGS:
                1. CRITICAL DEFICIENCY - Revenue Recognition Controls
                2. SIGNIFICANT DEFICIENCY - IT General Controls
                3. MINOR DEFICIENCY - Expense Authorization
                
                RETENTION: This document must be retained for 7 years per SOX requirements.
                CONFIDENTIALITY: Restricted to Audit Committee, Senior Management, and External Auditors.
                """
            }
        }
    ]
    
    print("Analyzing Sample Legal Documents:")
    print("=" * 50)
    
    results = []
    
    for doc in sample_docs:
        print(f"Document: {doc['filename']}")
        print("-" * 30)
        
        analysis = legal_research.analyze_legal_document(doc['content'], doc['filename'])
        
        print(f"Legal Type: {analysis.get('legal_type', 'Unknown')}")
        print(f"Jurisdiction: {analysis.get('jurisdiction', 'Unknown')}")
        print(f"Sensitivity: {analysis.get('sensitivity_level', 'Internal')}")
        print(f"Priority: {analysis.get('legal_priority', 'Normal')}")
        print(f"Retention: {analysis.get('retention_period', 3)} years")
        
        if analysis.get('statute_references'):
            print("Statute References:")
            for ref in analysis['statute_references']:
                print(f"  • {ref}")
        
        if analysis.get('compliance_requirements'):
            print("Compliance Requirements:")
            for req in analysis['compliance_requirements']:
                print(f"  • {req}")
        
        results.append(analysis)
        print()
    
    # Summary
    summary = legal_research.create_legal_summary(results)
    print("ANALYSIS SUMMARY:")
    print(f"Documents: {summary['total_documents']}")
    print(f"Legal Categories: {list(summary['legal_categories'].keys())}")
    print(f"High Priority Items: {len(summary['high_priority_items'])}")

if __name__ == "__main__":
    demo_legal_analysis()
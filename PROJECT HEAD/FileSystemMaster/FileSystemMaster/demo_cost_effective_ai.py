#!/usr/bin/env python3
"""
Demo: Cost-Effective AI Analysis
Shows how the multi-provider system works without expensive API calls
"""

from multi_ai_analyzer import MultiAIAnalyzer
import json

def demo_cost_effective_analysis():
    """Demonstrate cost-effective document analysis"""
    
    print("=== Cost-Effective AI File Analysis Demo ===\n")
    
    # Initialize the analyzer
    analyzer = MultiAIAnalyzer()
    
    print(f"Available AI providers: {[k for k, v in analyzer.available_providers.items() if v]}")
    print("Note: Using pattern-based analysis (no API costs!)\n")
    
    # Sample documents for testing
    test_documents = [
        {
            'filename': 'service_agreement_draft.txt',
            'content': {
                'text': """
                SERVICE AGREEMENT
                
                This Service Agreement ("Agreement") is entered into on January 15, 2024,
                between ABC Corporation ("Company") and XYZ Services LLC ("Service Provider").
                
                WHEREAS, Company desires to engage Service Provider for professional consulting services;
                WHEREAS, Service Provider agrees to provide such services under the terms herein;
                
                NOW, THEREFORE, the parties agree as follows:
                
                1. SCOPE OF SERVICES
                Service Provider shall provide business consulting and strategic planning services
                as detailed in Exhibit A, attached hereto and incorporated by reference.
                
                2. COMPENSATION
                Company shall pay Service Provider $50,000 for the services described herein,
                payable in monthly installments of $10,000.
                
                3. CONFIDENTIALITY
                Both parties acknowledge that confidential information may be disclosed during
                the performance of this Agreement and agree to maintain strict confidentiality.
                
                4. TERM
                This Agreement shall commence on February 1, 2024, and continue for six (6) months
                unless terminated earlier pursuant to the terms herein.
                
                IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.
                """
            }
        },
        {
            'filename': 'compliance_audit_report.txt',
            'content': {
                'text': """
                COMPLIANCE AUDIT REPORT
                Q4 2024 SOX Compliance Review
                
                EXECUTIVE SUMMARY
                This report presents the findings of our Sarbanes-Oxley Act (SOX) compliance audit
                conducted for the fourth quarter of 2024.
                
                SCOPE OF AUDIT
                - Internal controls over financial reporting
                - IT general controls and access management
                - Revenue recognition processes
                - Expense approval workflows
                
                KEY FINDINGS
                1. CRITICAL: Inadequate segregation of duties in accounts payable
                2. HIGH: Missing documentation for journal entry approvals
                3. MEDIUM: Outdated user access reviews in financial systems
                
                COMPLIANCE STATUS
                Overall compliance rating: 78% (Needs Improvement)
                
                RECOMMENDATIONS
                1. Implement additional controls in AP process
                2. Establish formal documentation requirements
                3. Quarterly access reviews for all financial systems
                4. Enhanced monitoring of high-risk transactions
                
                RETENTION REQUIREMENT
                This audit report must be retained for seven (7) years per SOX requirements.
                
                Prepared by: Internal Audit Department
                Review Date: December 15, 2024
                Next Audit: March 2025
                """
            }
        },
        {
            'filename': 'financial_report_q4.txt',
            'content': {
                'text': """
                QUARTERLY FINANCIAL REPORT
                Fourth Quarter 2024
                
                REVENUE SUMMARY
                Total Revenue: $2,450,000 (up 12% from Q3)
                - Product Sales: $1,800,000
                - Service Revenue: $650,000
                
                EXPENSES
                Operating Expenses: $1,200,000
                - Salaries and Benefits: $800,000
                - Marketing: $200,000
                - Technology: $150,000
                - Other: $50,000
                
                NET INCOME
                Gross Profit: $1,250,000
                Operating Income: $1,050,000
                Net Income: $950,000
                
                KEY METRICS
                - Gross Margin: 51%
                - Operating Margin: 43%
                - Net Margin: 39%
                
                BUDGET COMPARISON
                Revenue exceeded budget by 8%
                Expenses were 3% under budget
                Net income exceeded forecast by 15%
                
                STRATEGIC INITIATIVES
                - Expansion into new markets progressing on schedule
                - Digital transformation project 75% complete
                - Customer retention improved to 94%
                
                CONFIDENTIAL - For internal use only
                Prepared by: Finance Department
                """
            }
        }
    ]
    
    # Analyze each document
    for i, doc in enumerate(test_documents, 1):
        print(f"\n--- Analyzing Document {i}: {doc['filename']} ---")
        
        # Run the cost-effective analysis
        result = analyzer.analyze_document(
            doc['content'], 
            'text', 
            doc['filename']
        )
        
        # Display results
        print(f"✓ Suggested filename: {result['suggested_name']}")
        print(f"✓ Category: {result['category']}")
        print(f"✓ Subcategory: {result['subcategory']}")
        print(f"✓ Confidence: {result['confidence']}")
        print(f"✓ Priority: {result['business_priority']}")
        print(f"✓ Sensitivity: {result['sensitivity_level']}")
        print(f"✓ Legal classification: {result['legal_classification']}")
        print(f"✓ Retention period: {result['retention_period']} years")
        print(f"✓ Analysis method: {result['analysis_method']}")
        print(f"✓ Tags: {', '.join(result['tags'])}")
        
        if result['compliance_requirements']:
            print(f"✓ Compliance: {', '.join(result['compliance_requirements'])}")
        
        print(f"\nReasoning: {result['reasoning']}")

if __name__ == "__main__":
    demo_cost_effective_analysis()
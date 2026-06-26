"""
Test Script for 4-Stage Groq Pipeline Integration
Tests pipeline components and end-to-end execution
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add AI engine to path
current_dir = Path(__file__).parent
ai_engine_path = current_dir / "ai engine"
sys.path.append(str(ai_engine_path))

# ============================================================================
# TEST SECTION 1: Component Initialization
# ============================================================================

def test_component_initialization():
    """Test that all pipeline components initialize correctly"""
    logger.info("="*60)
    logger.info("TEST 1: Component Initialization")
    logger.info("="*60)
    
    try:
        from ai_engine.compliance_analyzer import ComplianceAnalyzer
        
        logger.info("Creating ComplianceAnalyzer...")
        analyzer = ComplianceAnalyzer()
        
        # Check components
        components = {
            "groq_pipeline": analyzer.groq_pipeline,
            "policy_manager": analyzer.policy_manager,
            "semgrep_executor": analyzer.semgrep_executor
        }
        
        print("\nComponent Status:")
        for name, component in components.items():
            status = "✓ AVAILABLE" if component else "✗ UNAVAILABLE"
            print(f"  {name}: {status}")
        
        # Get pipeline status
        pipeline_status = analyzer.get_pipeline_status()
        print(f"\nPipeline Status: {pipeline_status['status']}")
        print(f"Active Components: {', '.join(pipeline_status['active_components'])}")
        
        logger.info("✓ Component initialization test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Component initialization test FAILED: {e}\n")
        return False


# ============================================================================
# TEST SECTION 2: Code Analysis
# ============================================================================

async def test_code_analysis():
    """Test Stage 3 context analysis on sample code"""
    logger.info("="*60)
    logger.info("TEST 2: Code Analysis (Stage 3: Context Analysis)")
    logger.info("="*60)
    
    try:
        from ai_engine.compliance_analyzer import ComplianceAnalyzer
        
        analyzer = ComplianceAnalyzer()
        
        # Sample vulnerable code snippets
        test_cases = [
            {
                "name": "Hardcoded credentials",
                "code": """
password = "admin123"
api_key = "sk-12345678"
db_connection = "postgresql://user:pass@localhost/db"
                """,
                "file_type": "python"
            },
            {
                "name": "SQL injection",
                "code": """
user_input = request.args.get('username')
query = f"SELECT * FROM users WHERE username = '{user_input}'"
result = db.execute(query)
                """,
                "file_type": "python"
            },
            {
                "name": "Unencrypted data storage",
                "code": """
import json
data = {"ssn": "123-45-6789", "credit_card": "4532-1111-2222-3333"}
with open('data.json', 'w') as f:
    json.dump(data, f)  # No encryption!
                """,
                "file_type": "python"
            }
        ]
        
        print("\n")
        for test_case in test_cases:
            logger.info(f"Analyzing: {test_case['name']}")
            
            result = await analyzer.analyze_code(
                test_case['code'],
                test_case['file_type']
            )
            
            print(f"\n  {test_case['name']}:")
            print(f"  Status: {result.get('status')}")
            print(f"  Compliant: {result.get('is_compliant')}")
            print(f"  Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"  Risk: {result.get('risk_assessment')}")
            print(f"  Reasoning: {result.get('reasoning', 'N/A')[:80]}...")
        
        logger.info("✓ Code analysis test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Code analysis test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST SECTION 3: Policy Ingestion
# ============================================================================

async def test_policy_ingestion():
    """Test Stage 2 policy translation"""
    logger.info("="*60)
    logger.info("TEST 3: Policy Ingestion (Stage 2: Policy Translation)")
    logger.info("="*60)
    
    try:
        from ai_engine.compliance_analyzer import ComplianceAnalyzer
        
        analyzer = ComplianceAnalyzer()
        
        sample_policy = """
COMPANY DATA PROTECTION POLICY

1. Personal Data Handling
   - All personal data must be encrypted at rest
   - Data access requires authentication logs
   - Retention period maximum 1 year
   
2. API Security
   - All APIs must use HTTPS
   - Rate limiting: 100 requests per minute
   - API keys must be rotated quarterly
   
3. Code Security
   - No hardcoded credentials allowed
   - All dependencies must be scanned for vulnerabilities
   - SQL queries must use parameterized statements
        """
        
        logger.info("Ingesting sample compliance policy...")
        result = await analyzer.ingest_custom_policy(
            policy_name="Test Company Policy",
            policy_text=sample_policy,
            policy_type="compliance"
        )
        
        print("\n")
        print(f"Policy ID: {result.get('policy_id')}")
        print(f"Policy Name: {result.get('policy_name')}")
        print(f"Rules Generated: {result.get('rules_generated')}")
        print(f"Coverage: {result.get('coverage')}%")
        
        logger.info("✓ Policy ingestion test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Policy ingestion test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST SECTION 4: Data Handling Analysis (Full Pipeline)
# ============================================================================

async def test_data_handling_analysis():
    """Test full 4-stage pipeline on DPDP compliance"""
    logger.info("="*60)
    logger.info("TEST 4: Data Handling Analysis (Full 4-Stage Pipeline)")
    logger.info("="*60)
    
    try:
        from ai_engine.compliance_analyzer import ComplianceAnalyzer
        
        analyzer = ComplianceAnalyzer()
        
        data_handling_code = """
# DPDP Act Compliance Test
import hashlib
import json
from database import db

def process_user_data(user_id, personal_data):
    # Stage 1 would profile: data handling, potential risks
    # Stage 2 would translate policy to rules
    
    # Encrypt sensitive data (good practice)
    encrypted = hashlib.sha256(personal_data.encode()).hexdigest()
    
    # Log access for audit trail
    audit_log = {
        "user_id": user_id,
        "action": "data_processing",
        "timestamp": datetime.now().isoformat()
    }
    db.log_audit(audit_log)
    
    # Store encrypted data
    db.store_user_data(user_id, encrypted)
    
    return {"status": "success", "data_id": encrypted[:8]}
        """
        
        logger.info("Analyzing data handling with full pipeline...")
        context = {
            "repo_path": ".",
            "framework": "DPDP",
            "analysis_type": "data_handling"
        }
        
        result = await analyzer.analyze_data_handling(
            data_handling_code,
            context
        )
        
        print("\n")
        print(f"Status: {result.get('status')}")
        print(f"Framework: {result.get('framework')}")
        
        if result.get('project_profile'):
            profile = result['project_profile']
            print(f"\nProfile (Stage 1):")
            print(f"  Tech Stack: {profile.get('tech_stack', [])}")
            print(f"  Project Type: {profile.get('project_type')}")
            print(f"  Risk Level: {profile.get('identified_risks', [])}")
        
        if result.get('validation'):
            validation = result['validation']
            print(f"\nContext Analysis (Stage 3):")
            print(f"  Valid: {not validation.get('is_false_positive')}")
            print(f"  Confidence: {validation.get('confidence_score', 0):.2f}")
            print(f"  Risk Assessment: {validation.get('risk_assessment')}")
        
        if result.get('remediation'):
            remediation = result['remediation']
            print(f"\nRemediation (Stage 4):")
            if remediation:
                print(f"  Suggested Fix: {str(remediation).split('fixed_code')[0][:100]}...")
        
        logger.info("✓ Data handling analysis test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Data handling analysis test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST SECTION 5: RBI Compliance Check
# ============================================================================

async def test_rbi_compliance():
    """Test RBI compliance check"""
    logger.info("="*60)
    logger.info("TEST 5: RBI Compliance Check")
    logger.info("="*60)
    
    try:
        from ai_engine.compliance_analyzer import ComplianceAnalyzer
        
        analyzer = ComplianceAnalyzer()
        
        financial_code = """
# Payment Gateway Implementation (RBI Compliance)
import ssl
import logging
from fastapi import FastAPI, Depends

app = FastAPI()

# Secure TLS configuration
ssl_context = ssl.create_default_context()
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

def process_payment(payment_data):
    # Log all transactions for audit trail
    logging.info(f"Processing payment: {payment_data['amount']}")
    
    # Validate payment parameters
    if not payment_data.get('amount') or payment_data['amount'] <= 0:
        raise ValueError("Invalid amount")
    
    # Token-based transaction ID (no sensitive data logging)
    transaction_id = hashlib.sha256(str(payment_data).encode()).hexdigest()[:16]
    
    # Process through secure gateway
    result = gateway.process(payment_data)
    
    return {"transaction_id": transaction_id, "status": result}
        """
        
        logger.info("Checking RBI compliance for payment system...")
        result = await analyzer.check_rbi_compliance(
            financial_code,
            "payment_system"
        )
        
        print("\n")
        print(f"Status: {result.get('status')}")
        print(f"Framework: {result.get('framework')}")
        print(f"System Type: {result.get('system_type')}")
        print(f"RBI Compliant: {result.get('rbi_compliant')}")
        print(f"Confidence: {result.get('confidence_score', 0):.2f}")
        print(f"Risk Assessment: {result.get('risk_assessment')}")
        
        logger.info("✓ RBI compliance test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ RBI compliance test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST SECTION 6: Pipeline Status
# ============================================================================

def test_pipeline_status():
    """Test pipeline status endpoint"""
    logger.info("="*60)
    logger.info("TEST 6: Pipeline Status Check")
    logger.info("="*60)
    
    try:
        from ai_engine.compliance_analyzer import ComplianceAnalyzer
        
        analyzer = ComplianceAnalyzer()
        
        status = analyzer.get_pipeline_status()
        
        print("\nPipeline Status:")
        print(f"  Overall: {status.get('status')}")
        
        print("\nComponents:")
        for name, available in status.get('components', {}).items():
            symbol = "✓" if available else "✗"
            print(f"  {symbol} {name}: {available}")
        
        print("\nStages:")
        for stage, ready in status.get('stages', {}).items():
            symbol = "✓" if ready else "✗"
            print(f"  {symbol} {stage}: {ready}")
        
        compliance_status = analyzer.get_compliance_status()
        print(f"\nCompliance Status: {compliance_status.get('status')}")
        
        logger.info("✓ Pipeline status test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Pipeline status test FAILED: {e}\n")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all integration tests"""
    logger.info("\n" + "="*60)
    logger.info("4-STAGE GROQ PIPELINE - INTEGRATION TEST SUITE")
    logger.info("="*60 + "\n")
    
    test_results = {
        "Initialization": test_component_initialization(),
        "Code Analysis": await test_code_analysis(),
        "Policy Ingestion": await test_policy_ingestion(),
        "Data Handling": await test_data_handling_analysis(),
        "RBI Compliance": await test_rbi_compliance(),
        "Pipeline Status": test_pipeline_status()
    }
    
    # Summary
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print("\nTest Results:")
    for test_name, result in test_results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! 4-Stage pipeline is fully integrated.\n")
    else:
        logger.warning(f"\n⚠️  {total - passed} test(s) failed. Check logs above.\n")
    
    return passed == total


if __name__ == "__main__":
    # Run async tests
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

"""
Setup Indian Policies - Clear foreign policies and ingest Indian compliance policies
"""

import logging
import sys
from pathlib import Path
from policy_manager import PolicyManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main setup function"""
    print("=" * 80)
    print("Indian Compliance Policies Setup")
    print("=" * 80)
    print()
    
    # Initialize policy manager
    logger.info("Initializing Policy Manager...")
    policy_manager = PolicyManager(policies_dir="policies")
    
    # Step 1: Clear foreign policies
    print("\n[Step 1] Clearing foreign policies...")
    print("-" * 80)
    
    clear_result = policy_manager.clear_foreign_policies()
    
    if clear_result["status"] == "success":
        print(f"✓ Successfully cleared {len(clear_result['removed_files'])} foreign policy files")
        if clear_result['removed_files']:
            print("\nRemoved files:")
            for file_path in clear_result['removed_files']:
                print(f"  - {Path(file_path).name}")
    else:
        print(f"✗ Failed to clear foreign policies: {clear_result.get('message', 'Unknown error')}")
        return 1
    
    # Step 2: Ingest Indian policies from PDFs
    print("\n[Step 2] Ingesting Indian compliance policies from PDFs...")
    print("-" * 80)
    
    sample_policies_dir = Path("policies/sample_policies")
    
    if not sample_policies_dir.exists():
        print(f"✗ Sample policies directory not found: {sample_policies_dir}")
        return 1
    
    # Find PDF files
    pdf_files = list(sample_policies_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"✗ No PDF files found in {sample_policies_dir}")
        print("\nNote: Make sure you have Indian compliance PDFs in the sample_policies directory")
        return 1
    
    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    print("\nProcessing PDFs...")
    ingest_result = policy_manager.ingest_multiple_pdfs(str(sample_policies_dir))
    
    if ingest_result["status"] == "success":
        print(f"\n✓ Successfully processed {ingest_result['successful']}/{ingest_result['total_pdfs']} PDF files")
        
        if ingest_result['policies']:
            print("\nPolicy Processing Results:")
            for policy in ingest_result['policies']:
                status_icon = "✓" if policy['status'] in ['success', 'partial_success'] else "✗"
                print(f"  {status_icon} {policy['filename']}")
                print(f"     Status: {policy['status']}")
                if policy.get('policy_id'):
                    print(f"     Policy ID: {policy['policy_id']}")
                if policy.get('rules_generated'):
                    print(f"     Rules Generated: {policy['rules_generated']}")
                print()
    else:
        print(f"✗ Failed to ingest policies: {ingest_result.get('message', 'Unknown error')}")
        return 1
    
    # Step 3: Show summary
    print("\n[Step 3] Policy Summary")
    print("-" * 80)
    
    summary = policy_manager.get_policy_summary()
    
    if summary["status"] == "success":
        print(f"Total Policies: {summary.get('total_policies', 0)}")
        print(f"Total Compliance Rules: {summary.get('total_rules', 0)}")
        
        if summary.get('categories'):
            print("\nPolicy Categories:")
            for category, count in summary['categories'].items():
                print(f"  - {category}: {count}")
        
        print("\nFile Distribution:")
        for dir_name, counts in summary.get('directories', {}).items():
            print(f"  {dir_name}:")
            print(f"    Total: {counts['total']}")
            print(f"    PDFs: {counts['pdf']}")
            print(f"    Text: {counts['txt']}")
            print(f"    Markdown: {counts['md']}")
    
    print("\n" + "=" * 80)
    print("✓ Indian Compliance Policies Setup Complete!")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Start the backend server: python main.py")
    print("2. Use the /policies/summary endpoint to view policy details")
    print("3. Use the /policies/rules endpoint to see generated compliance rules")
    print("4. Run repository scans with Indian compliance rules")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

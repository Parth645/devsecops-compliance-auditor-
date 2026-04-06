"""
Policy Manager - Manage policy documents and ingestion
"""

import logging
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

# Add AI engine to path
current_dir = Path(__file__).parent
ai_engine_path = current_dir / "ai engine"
sys.path.append(str(ai_engine_path))

from pdf_extractor import PDFExtractor

try:
    from policy_processor import PolicyProcessor
    POLICY_PROCESSOR_AVAILABLE = True
except ImportError:
    POLICY_PROCESSOR_AVAILABLE = False
    logging.warning("PolicyProcessor not available")

logger = logging.getLogger(__name__)


class PolicyManager:
    """Manage policy documents and their ingestion"""
    
    def __init__(self, policies_dir: str = "policies"):
        self.policies_dir = Path(policies_dir)
        self.policies_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.sample_policies_dir = self.policies_dir / "sample_policies"
        self.my_policies_dir = self.policies_dir / "my_policies"
        self.indian_policies_dir = self.policies_dir / "indian_policies"
        
        for dir_path in [self.sample_policies_dir, self.my_policies_dir, self.indian_policies_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.pdf_extractor = PDFExtractor()
        
        if POLICY_PROCESSOR_AVAILABLE:
            self.policy_processor = PolicyProcessor(policies_dir=str(self.policies_dir))
        else:
            self.policy_processor = None
            logger.warning("Policy processor not available")
    
    def clear_foreign_policies(self) -> Dict[str, Any]:
        """
        Remove all non-Indian policies from the system
        
        Returns:
            Status of the clearing operation
        """
        try:
            removed_files = []
            
            # Clear sample_policies except Indian policies
            if self.sample_policies_dir.exists():
                for file_path in self.sample_policies_dir.iterdir():
                    # Keep only DPDPA and Indian-related files
                    if "dpdpa" not in file_path.name.lower() and "indian" not in file_path.name.lower():
                        if file_path.is_file():
                            removed_files.append(str(file_path))
                            file_path.unlink()
                            logger.info(f"Removed: {file_path}")
            
            # Clear my_policies (foreign policies)
            if self.my_policies_dir.exists():
                for file_path in self.my_policies_dir.iterdir():
                    # Remove GDPR, CCPA, and other foreign policies
                    if any(keyword in file_path.name.lower() for keyword in ["gdpr", "ccpa", "privacy", "security", "data_protection"]):
                        if file_path.is_file():
                            removed_files.append(str(file_path))
                            file_path.unlink()
                            logger.info(f"Removed: {file_path}")
            
            # Clear processed policies and rules
            processed_policies_path = self.policies_dir / "processed_policies.json"
            compliance_rules_path = self.policies_dir / "compliance_rules.json"
            
            if processed_policies_path.exists():
                processed_policies_path.unlink()
                logger.info("Cleared processed_policies.json")
            
            if compliance_rules_path.exists():
                compliance_rules_path.unlink()
                logger.info("Cleared compliance_rules.json")
            
            return {
                "status": "success",
                "message": f"Cleared {len(removed_files)} foreign policy files",
                "removed_files": removed_files,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to clear foreign policies: {e}")
            return {
                "status": "error",
                "message": str(e),
                "removed_files": []
            }
    
    def ingest_pdf_policy(self, pdf_path: str, policy_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest a PDF policy document
        
        Args:
            pdf_path: Path to PDF file
            policy_name: Optional custom name for the policy
            
        Returns:
            Ingestion result with processed policy data
        """
        try:
            pdf_file = Path(pdf_path)
            
            if not pdf_file.exists():
                return {
                    "status": "error",
                    "message": f"PDF file not found: {pdf_path}"
                }
            
            # Extract text from PDF
            logger.info(f"Extracting text from PDF: {pdf_file.name}")
            extraction_result = self.pdf_extractor.extract_text(pdf_path)
            
            if extraction_result["status"] != "success":
                return {
                    "status": "error",
                    "message": f"PDF extraction failed: {extraction_result.get('message', 'Unknown error')}"
                }
            
            extracted_text = extraction_result["text"]
            
            if not extracted_text or len(extracted_text.strip()) < 100:
                return {
                    "status": "error",
                    "message": "Extracted text is too short or empty"
                }
            
            # Save extracted text
            text_filename = pdf_file.stem + "_extracted.txt"
            text_path = self.indian_policies_dir / text_filename
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            logger.info(f"Saved extracted text to: {text_path}")
            
            # Process policy with AI
            if self.policy_processor:
                policy_id = policy_name or f"policy_{pdf_file.stem}"
                
                logger.info(f"Processing policy with AI: {policy_id}")
                processed_policy = self.policy_processor.process_policy(
                    policy_id=policy_id,
                    content=extracted_text,
                    file_path=str(pdf_path)
                )
                
                # Save policies
                self.policy_processor._save_policies()
                
                return {
                    "status": "success",
                    "message": f"Successfully ingested PDF policy: {pdf_file.name}",
                    "pdf_file": str(pdf_file),
                    "text_file": str(text_path),
                    "extraction_metadata": extraction_result.get("metadata", {}),
                    "word_count": extraction_result.get("word_count", 0),
                    "policy_id": policy_id,
                    "processing_status": processed_policy.get("processing_status"),
                    "compliance_rules_generated": len(processed_policy.get("compliance_rules", [])),
                    "categories": processed_policy.get("categories", []),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "partial_success",
                    "message": "PDF extracted but policy processor not available",
                    "pdf_file": str(pdf_file),
                    "text_file": str(text_path),
                    "extraction_metadata": extraction_result.get("metadata", {}),
                    "word_count": extraction_result.get("word_count", 0)
                }
                
        except Exception as e:
            logger.error(f"PDF ingestion failed: {e}")
            import traceback
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
    
    def ingest_multiple_pdfs(self, pdf_directory: str) -> Dict[str, Any]:
        """
        Ingest all PDF files from a directory
        
        Args:
            pdf_directory: Directory containing PDF files
            
        Returns:
            Batch ingestion results
        """
        try:
            pdf_dir = Path(pdf_directory)
            
            if not pdf_dir.exists():
                return {
                    "status": "error",
                    "message": f"Directory not found: {pdf_directory}"
                }
            
            pdf_files = list(pdf_dir.glob("*.pdf"))
            
            if not pdf_files:
                return {
                    "status": "error",
                    "message": f"No PDF files found in: {pdf_directory}"
                }
            
            results = {
                "status": "success",
                "total_pdfs": len(pdf_files),
                "successful": 0,
                "failed": 0,
                "policies": []
            }
            
            for pdf_file in pdf_files:
                logger.info(f"Processing PDF: {pdf_file.name}")
                result = self.ingest_pdf_policy(str(pdf_file))
                
                if result["status"] in ["success", "partial_success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                
                results["policies"].append({
                    "filename": pdf_file.name,
                    "status": result["status"],
                    "message": result.get("message", ""),
                    "policy_id": result.get("policy_id"),
                    "rules_generated": result.get("compliance_rules_generated", 0)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Batch PDF ingestion failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of all policies in the system"""
        try:
            summary = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "directories": {
                    "sample_policies": self._count_files(self.sample_policies_dir),
                    "my_policies": self._count_files(self.my_policies_dir),
                    "indian_policies": self._count_files(self.indian_policies_dir)
                }
            }
            
            if self.policy_processor:
                processor_summary = self.policy_processor.get_policy_summary()
                summary.update(processor_summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get policy summary: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _count_files(self, directory: Path) -> Dict[str, int]:
        """Count files by type in a directory"""
        if not directory.exists():
            return {"total": 0, "pdf": 0, "txt": 0, "md": 0}
        
        files = list(directory.iterdir())
        return {
            "total": len([f for f in files if f.is_file()]),
            "pdf": len(list(directory.glob("*.pdf"))),
            "txt": len(list(directory.glob("*.txt"))),
            "md": len(list(directory.glob("*.md")))
        }

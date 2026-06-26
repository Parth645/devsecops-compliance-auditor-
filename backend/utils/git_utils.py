import git
import os
import tempfile
import shutil
import logging
from git import Repo

logger = logging.getLogger(__name__)

def git_clone(git_repo_url: str):
    logger.info(f"Starting to clone repository: {git_repo_url}")
    
    # Create a temporary directory for cloning
    temp_dir = tempfile.mkdtemp()
    clone_path = os.path.join(temp_dir, "repo")
    
    try:
        # Validate URL format
        if not git_repo_url.startswith(('http://', 'https://', 'git@')):
            return {
                "status": "error",
                "message": "Invalid git URL format. Must start with http://, https://, or git@"
            }
        
        logger.info(f"Cloning to: {clone_path}")
        
        # Clone the repository using GitPython
        repo = Repo.clone_from(git_repo_url, clone_path)
        
        logger.info(f"Repository cloned successfully to: {clone_path}")
        
        # Get repository information
        repo_info = {
            "active_branch": repo.active_branch.name,
            "commit_count": len(list(repo.iter_commits())),
            "latest_commit": {
                "hash": repo.head.commit.hexsha,
                "message": repo.head.commit.message.strip(),
                "author": str(repo.head.commit.author),
                "date": repo.head.commit.committed_datetime.isoformat()
            }
        }
        
        # List files in the repository
        files = []
        for root, dirs, filenames in os.walk(clone_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), clone_path)
                files.append(rel_path)
        
        return {
            "status": "success",
            "repo": git_repo_url,
            "message": "Repository cloned and analyzed successfully",
            "clone_path": clone_path,
            "repo_info": repo_info,
            "files": files[:20],  # Show first 20 files
            "total_files": len(files)
        }
        
    except git.exc.GitCommandError as e:
        return {
            "status": "error",
            "message": f"Git command failed: {str(e)}"
        }
    except git.exc.InvalidGitRepositoryError:
        return {
            "status": "error",
            "message": "Invalid Git repository URL"
        }
    except git.exc.GitError as e:
        return {
            "status": "error",
            "message": f"Git error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }
    finally:
        # Optionally clean up the temporary directory
        # Uncomment the next line if you want to auto-delete after scanning
        # shutil.rmtree(temp_dir, ignore_errors=True)
        pass

def analyze_repository_files(clone_path: str, analysis_depth: str = "basic"):
    """Analyze files in the cloned repository for compliance issues"""
    try:
        compliance_issues = []
        
        # Define different analysis levels
        file_extensions = {
            "basic": ('.py', '.js', '.java', '.cpp'),
            "detailed": ('.py', '.js', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs'),
            "full": ('.py', '.js', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs', '.ts', '.jsx', '.tsx', '.vue', '.cs', '.swift', '.kt')
        }
        
        # Get file extensions based on analysis depth
        target_extensions = file_extensions.get(analysis_depth, file_extensions["basic"])
        
        for root, dirs, files in os.walk(clone_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, clone_path)
                
                # Check files based on analysis depth
                if file.endswith(target_extensions):
                    # Check for potential security issues
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Basic security checks
                            if 'password' in content.lower() and '=' in content:
                                line_num = _find_line_number(content, 'password')
                                compliance_issues.append({
                                    "file": rel_path,
                                    "issue": "Potential hardcoded password",
                                    "severity": "high",
                                    "line": line_num,
                                    "description": "Found potential hardcoded password in source code"
                                })
                                
                            if 'api_key' in content.lower() and '=' in content:
                                line_num = _find_line_number(content, 'api_key')
                                compliance_issues.append({
                                    "file": rel_path,
                                    "issue": "Potential hardcoded API key",
                                    "severity": "high",
                                    "line": line_num,
                                    "description": "Found potential hardcoded API key in source code"
                                })
                            
                            # Additional checks for detailed and full analysis
                            if analysis_depth in ["detailed", "full"]:
                                _perform_detailed_analysis(content, rel_path, compliance_issues)
                            
                            if analysis_depth == "full":
                                _perform_full_analysis(content, rel_path, compliance_issues)
                                
                    except Exception as file_error:
                        logger.warning(f"Could not analyze file {rel_path}: {file_error}")
                        continue
        
        return compliance_issues
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return [{"error": f"Analysis failed: {str(e)}"}]


def _find_line_number(content: str, search_term: str) -> int:
    """Find the line number where a search term appears"""
    try:
        lines = content.lower().split('\n')
        for i, line in enumerate(lines, 1):
            if search_term in line:
                return i
        return 1
    except:
        return 1


def _perform_detailed_analysis(content: str, file_path: str, compliance_issues: list):
    """Perform detailed analysis checks"""
    try:
        content_lower = content.lower()
        
        # Check for hardcoded secrets
        secret_patterns = ['secret', 'token', 'private_key', 'access_token']
        for pattern in secret_patterns:
            if pattern in content_lower and '=' in content:
                line_num = _find_line_number(content, pattern)
                compliance_issues.append({
                    "file": file_path,
                    "issue": f"Potential hardcoded {pattern.replace('_', ' ')}",
                    "severity": "high",
                    "line": line_num,
                    "description": f"Found potential hardcoded {pattern.replace('_', ' ')} in source code"
                })
        
        # Check for TODO/FIXME comments
        if 'todo' in content_lower or 'fixme' in content_lower:
            line_num = _find_line_number(content, 'todo' if 'todo' in content_lower else 'fixme')
            compliance_issues.append({
                "file": file_path,
                "issue": "Code contains TODO/FIXME comments",
                "severity": "low",
                "line": line_num,
                "description": "Code contains unresolved TODO or FIXME comments"
            })
            
    except Exception as e:
        logger.warning(f"Detailed analysis failed for {file_path}: {e}")


def _perform_full_analysis(content: str, file_path: str, compliance_issues: list):
    """Perform full analysis checks"""
    try:
        content_lower = content.lower()
        
        # Check for potential SQL injection patterns
        sql_patterns = ['select * from', 'drop table', 'delete from']
        for pattern in sql_patterns:
            if pattern in content_lower:
                line_num = _find_line_number(content, pattern)
                compliance_issues.append({
                    "file": file_path,
                    "issue": "Potential SQL injection vulnerability",
                    "severity": "medium",
                    "line": line_num,
                    "description": f"Found potential SQL injection pattern: {pattern}"
                })
        
        # Check for hardcoded URLs
        if 'http://' in content_lower:
            line_num = _find_line_number(content, 'http://')
            compliance_issues.append({
                "file": file_path,
                "issue": "Insecure HTTP URL found",
                "severity": "medium",
                "line": line_num,
                "description": "Found HTTP URL instead of HTTPS"
            })
            
    except Exception as e:
        logger.warning(f"Full analysis failed for {file_path}: {e}")
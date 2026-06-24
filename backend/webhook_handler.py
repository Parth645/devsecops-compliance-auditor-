"""
Webhook handler module for CI/CD platforms.
Supports GitHub, GitLab, and Bitbucket webhook verification and parsing.

References:
- GitHub: https://docs.github.com/en/developers/webhooks-and-events/webhooks/creating-webhooks
- GitLab: https://docs.gitlab.com/ee/user/project/integrations/webhooks.html
- Bitbucket: https://confluence.atlassian.com/bitbucket/manage-webhooks-735643732.html
"""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field
import logging

logger = logging.getLogger(__name__)


class WebhookProvider(str, Enum):
    """Supported webhook providers."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class WebhookPayload(BaseModel):
    """Normalized webhook payload structure."""
    provider: WebhookProvider
    repo_url: HttpUrl
    branch: str
    commit_sha: str
    event_type: str
    default_branch: Optional[str] = None
    push_timestamp: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class GitHub:
    """GitHub webhook handler and signature verifier."""
    
    SIGNATURE_HEADER = "X-Hub-Signature-256"
    EVENT_HEADER = "X-GitHub-Event"
    
    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify GitHub webhook signature.
        
        GitHub uses SHA256 HMAC format: sha256=<hash>
        
        Args:
            payload: Raw request body bytes
            signature: Signature from X-Hub-Signature-256 header
            secret: Webhook secret
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not signature or not signature.startswith("sha256="):
            logger.warning("Invalid GitHub signature format")
            return False
        
        try:
            expected_hash = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            provided_hash = signature.replace("sha256=", "")
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected_hash, provided_hash)
        except Exception as e:
            logger.error(f"Error verifying GitHub signature: {e}")
            return False
    
    @staticmethod
    def parse_push_event(payload: Dict[str, Any]) -> Optional[WebhookPayload]:
        """
        Parse GitHub push event webhook.
        
        Args:
            payload: GitHub webhook payload
            
        Returns:
            Normalized WebhookPayload or None if parsing fails
        """
        try:
            repo_url = payload.get("repository", {}).get("clone_url")
            ref = payload.get("ref", "")  # refs/heads/main
            branch = ref.replace("refs/heads/", "")
            commit_sha = payload.get("head_commit", {}).get("id")
            
            if not all([repo_url, branch, commit_sha]):
                logger.warning("Missing required fields in GitHub push event")
                return None
            
            return WebhookPayload(
                provider=WebhookProvider.GITHUB,
                repo_url=repo_url,
                branch=branch,
                commit_sha=commit_sha,
                event_type="push",
                default_branch=payload.get("repository", {}).get("default_branch"),
                push_timestamp=payload.get("head_commit", {}).get("timestamp"),
                raw_payload=payload
            )
        except Exception as e:
            logger.error(f"Error parsing GitHub push event: {e}")
            return None
    
    @staticmethod
    def parse_pull_request_event(payload: Dict[str, Any]) -> Optional[WebhookPayload]:
        """
        Parse GitHub pull request event webhook.
        
        Args:
            payload: GitHub webhook payload
            
        Returns:
            Normalized WebhookPayload or None if parsing fails
        """
        try:
            action = payload.get("action")
            # Only process opened, synchronize (new commits), and reopened actions
            if action not in ["opened", "synchronize", "reopened"]:
                return None
            
            pr = payload.get("pull_request", {})
            repo = payload.get("repository", {})
            
            repo_url = repo.get("clone_url")
            branch = pr.get("head", {}).get("ref")
            commit_sha = pr.get("head", {}).get("sha")
            
            if not all([repo_url, branch, commit_sha]):
                logger.warning("Missing required fields in GitHub PR event")
                return None
            
            return WebhookPayload(
                provider=WebhookProvider.GITHUB,
                repo_url=repo_url,
                branch=branch,
                commit_sha=commit_sha,
                event_type="pull_request",
                default_branch=repo.get("default_branch"),
                push_timestamp=pr.get("updated_at"),
                raw_payload=payload
            )
        except Exception as e:
            logger.error(f"Error parsing GitHub PR event: {e}")
            return None


class GitLab:
    """GitLab webhook handler and signature verifier."""
    
    SIGNATURE_HEADER = "X-Gitlab-Token"
    EVENT_HEADER = "X-Gitlab-Event"
    
    @staticmethod
    def verify_signature(payload: bytes, token: str, secret: str) -> bool:
        """
        Verify GitLab webhook signature using token validation.
        
        GitLab uses simple token comparison (X-Gitlab-Token header).
        
        Args:
            payload: Raw request body bytes (unused for GitLab token validation)
            token: Token from X-Gitlab-Token header
            secret: Webhook secret token
            
        Returns:
            True if token matches secret, False otherwise
        """
        if not token or not secret:
            logger.warning("Missing GitLab token or secret")
            return False
        
        # Use constant-time comparison
        return hmac.compare_digest(token, secret)
    
    @staticmethod
    def parse_push_event(payload: Dict[str, Any]) -> Optional[WebhookPayload]:
        """
        Parse GitLab push event webhook.
        
        Args:
            payload: GitLab webhook payload
            
        Returns:
            Normalized WebhookPayload or None if parsing fails
        """
        try:
            project = payload.get("project", {})
            repo_url = project.get("git_http_url") or project.get("git_ssh_url")
            ref = payload.get("ref", "")  # refs/heads/main
            branch = ref.replace("refs/heads/", "")
            commit_sha = payload.get("checkout_sha")
            
            if not all([repo_url, branch, commit_sha]):
                logger.warning("Missing required fields in GitLab push event")
                return None
            
            return WebhookPayload(
                provider=WebhookProvider.GITLAB,
                repo_url=repo_url,
                branch=branch,
                commit_sha=commit_sha,
                event_type="push",
                default_branch=project.get("default_branch"),
                push_timestamp=payload.get("created_at"),
                raw_payload=payload
            )
        except Exception as e:
            logger.error(f"Error parsing GitLab push event: {e}")
            return None
    
    @staticmethod
    def parse_merge_request_event(payload: Dict[str, Any]) -> Optional[WebhookPayload]:
        """
        Parse GitLab merge request event webhook.
        
        Args:
            payload: GitLab webhook payload
            
        Returns:
            Normalized WebhookPayload or None if parsing fails
        """
        try:
            action = payload.get("object_kind")
            if action != "merge_request":
                return None
            
            mr_action = payload.get("action")
            # Only process opened and update actions
            if mr_action not in ["open", "update"]:
                return None
            
            mr = payload.get("object_attributes", {})
            project = payload.get("project", {})
            
            repo_url = project.get("git_http_url") or project.get("git_ssh_url")
            branch = mr.get("source_branch")
            commit_sha = mr.get("last_commit", {}).get("id")
            
            if not all([repo_url, branch, commit_sha]):
                logger.warning("Missing required fields in GitLab MR event")
                return None
            
            return WebhookPayload(
                provider=WebhookProvider.GITLAB,
                repo_url=repo_url,
                branch=branch,
                commit_sha=commit_sha,
                event_type="merge_request",
                default_branch=project.get("default_branch"),
                push_timestamp=mr.get("updated_at"),
                raw_payload=payload
            )
        except Exception as e:
            logger.error(f"Error parsing GitLab MR event: {e}")
            return None


class Bitbucket:
    """Bitbucket webhook handler and signature verifier."""
    
    SIGNATURE_HEADER = "X-Hub-Signature"
    
    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify Bitbucket webhook signature.
        
        Bitbucket uses SHA256 HMAC format: sha256=<hash>
        
        Args:
            payload: Raw request body bytes
            signature: Signature from X-Hub-Signature header
            secret: Webhook secret
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not signature or not signature.startswith("sha256="):
            logger.warning("Invalid Bitbucket signature format")
            return False
        
        try:
            expected_hash = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            provided_hash = signature.replace("sha256=", "")
            
            # Use constant-time comparison
            return hmac.compare_digest(expected_hash, provided_hash)
        except Exception as e:
            logger.error(f"Error verifying Bitbucket signature: {e}")
            return False
    
    @staticmethod
    def parse_push_event(payload: Dict[str, Any]) -> Optional[WebhookPayload]:
        """
        Parse Bitbucket push event webhook.
        
        Args:
            payload: Bitbucket webhook payload
            
        Returns:
            Normalized WebhookPayload or None if parsing fails
        """
        try:
            repository = payload.get("repository", {})
            links = repository.get("links", {}).get("clone", [])
            
            # Find HTTPS clone URL
            repo_url = None
            for link in links:
                if link.get("name") == "http":
                    repo_url = link.get("href")
                    break
            
            # Fallback to first clone URL
            if not repo_url and links:
                repo_url = links[0].get("href")
            
            # Get push details
            push_data = payload.get("push", {}).get("changes", [])
            if not push_data:
                logger.warning("No push changes in Bitbucket event")
                return None
            
            change = push_data[0]
            new_data = change.get("new", {})
            
            branch = new_data.get("name")
            commit_sha = new_data.get("target", {}).get("hash")
            
            if not all([repo_url, branch, commit_sha]):
                logger.warning("Missing required fields in Bitbucket push event")
                return None
            
            return WebhookPayload(
                provider=WebhookProvider.BITBUCKET,
                repo_url=repo_url,
                branch=branch,
                commit_sha=commit_sha,
                event_type="push",
                default_branch=repository.get("mainbranch", {}).get("name"),
                push_timestamp=new_data.get("target", {}).get("date"),
                raw_payload=payload
            )
        except Exception as e:
            logger.error(f"Error parsing Bitbucket push event: {e}")
            return None


# Webhook dispatcher
class WebhookDispatcher:
    """Dispatches webhook processing based on provider."""
    
    HANDLERS = {
        WebhookProvider.GITHUB: GitHub,
        WebhookProvider.GITLAB: GitLab,
        WebhookProvider.BITBUCKET: Bitbucket,
    }
    
    @staticmethod
    def verify_webhook(
        provider: WebhookProvider,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify webhook signature for given provider."""
        handler = WebhookDispatcher.HANDLERS.get(provider)
        if not handler:
            logger.error(f"Unknown webhook provider: {provider}")
            return False
        
        if provider == WebhookProvider.GITLAB:
            # GitLab uses token verification, signature is the token
            return handler.verify_signature(payload, signature, secret)
        else:
            # GitHub and Bitbucket use HMAC
            return handler.verify_signature(payload, signature, secret)
    
    @staticmethod
    def parse_webhook(
        provider: WebhookProvider,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Optional[WebhookPayload]:
        """Parse webhook payload for given provider and event type."""
        handler = WebhookDispatcher.HANDLERS.get(provider)
        if not handler:
            logger.error(f"Unknown webhook provider: {provider}")
            return None
        
        if provider == WebhookProvider.GITHUB:
            if event_type == "push":
                return handler.parse_push_event(payload)
            elif event_type == "pull_request":
                return handler.parse_pull_request_event(payload)
        
        elif provider == WebhookProvider.GITLAB:
            if event_type == "push_events":
                return handler.parse_push_event(payload)
            elif event_type == "merge_requests_events":
                return handler.parse_merge_request_event(payload)
        
        elif provider == WebhookProvider.BITBUCKET:
            if event_type == "repo:push":
                return handler.parse_push_event(payload)
        
        logger.warning(f"Unsupported event type {event_type} for provider {provider}")
        return None

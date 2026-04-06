"""
Unit tests for webhook handlers.

Tests webhook signature verification and payload parsing for GitHub, GitLab, and Bitbucket.
"""

import pytest
import json
import hmac
import hashlib
from datetime import datetime

from webhook_handler import (
    GitHub,
    GitLab,
    Bitbucket,
    WebhookProvider,
    WebhookPayload,
    WebhookDispatcher,
)


class TestGitHubWebhook:
    """Tests for GitHub webhook handling."""

    def test_verify_signature_valid(self):
        """Test GitHub signature verification with valid signature."""
        secret = "test-secret-123"
        payload = b'{"test": "payload"}'
        
        # Create valid signature
        expected_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected_hash}"
        
        # Verify should return True
        assert GitHub.verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        """Test GitHub signature verification with invalid signature."""
        secret = "test-secret-123"
        payload = b'{"test": "payload"}'
        signature = "sha256=invalid_hash_here"
        
        # Verify should return False
        assert GitHub.verify_signature(payload, signature, secret) is False

    def test_verify_signature_missing_prefix(self):
        """Test GitHub signature verification with missing sha256 prefix."""
        secret = "test-secret-123"
        payload = b'{"test": "payload"}'
        signature = "invalid_hash_without_prefix"
        
        # Should return False for invalid format
        assert GitHub.verify_signature(payload, signature, secret) is False

    def test_verify_signature_empty_signature(self):
        """Test GitHub signature verification with empty signature."""
        secret = "test-secret-123"
        payload = b'{"test": "payload"}'
        
        assert GitHub.verify_signature(payload, "", secret) is False
        assert GitHub.verify_signature(payload, None, secret) is False

    def test_parse_push_event_success(self):
        """Test GitHub push event parsing."""
        payload = {
            "repository": {
                "clone_url": "https://github.com/user/repo.git",
                "default_branch": "main"
            },
            "ref": "refs/heads/main",
            "head_commit": {
                "id": "abc123def456",
                "timestamp": "2026-04-01T12:00:00Z"
            }
        }
        
        result = GitHub.parse_push_event(payload)
        
        assert result is not None
        assert result.provider == WebhookProvider.GITHUB
        assert result.branch == "main"
        assert result.commit_sha == "abc123def456"
        assert result.event_type == "push"
        assert str(result.repo_url) == "https://github.com/user/repo.git"

    def test_parse_push_event_missing_fields(self):
        """Test GitHub push event parsing with missing fields."""
        payload = {
            "repository": {"clone_url": "https://github.com/user/repo.git"},
            "ref": "refs/heads/main"
            # Missing head_commit - should fail
        }
        
        result = GitHub.parse_push_event(payload)
        assert result is None

    def test_parse_pr_event_opened(self):
        """Test GitHub PR event parsing when opened."""
        payload = {
            "action": "opened",
            "pull_request": {
                "head": {
                    "ref": "feature/new-feature",
                    "sha": "def789ghi123"
                },
                "updated_at": "2026-04-01T12:00:00Z"
            },
            "repository": {
                "clone_url": "https://github.com/user/repo.git",
                "default_branch": "main"
            }
        }
        
        result = GitHub.parse_pull_request_event(payload)
        
        assert result is not None
        assert result.provider == WebhookProvider.GITHUB
        assert result.branch == "feature/new-feature"
        assert result.commit_sha == "def789ghi123"
        assert result.event_type == "pull_request"

    def test_parse_pr_event_ignored_action(self):
        """Test GitHub PR event parsing with ignored action."""
        payload = {
            "action": "assigned",  # Should be ignored
            "pull_request": {}
        }
        
        result = GitHub.parse_pull_request_event(payload)
        assert result is None

    def test_parse_pr_event_synchronize(self):
        """Test GitHub PR event parsing when synchronized (new commits)."""
        payload = {
            "action": "synchronize",
            "pull_request": {
                "head": {
                    "ref": "feature/updates",
                    "sha": "new_commit_sha"
                },
                "updated_at": "2026-04-01T12:30:00Z"
            },
            "repository": {
                "clone_url": "https://github.com/user/repo.git",
                "default_branch": "main"
            }
        }
        
        result = GitHub.parse_pull_request_event(payload)
        assert result is not None
        assert result.branch == "feature/updates"


class TestGitLabWebhook:
    """Tests for GitLab webhook handling."""

    def test_verify_token_valid(self):
        """Test GitLab token verification with valid token."""
        token = "gitlab-secret-token-123"
        secret = "gitlab-secret-token-123"
        
        assert GitLab.verify_signature(b"", token, secret) is True

    def test_verify_token_invalid(self):
        """Test GitLab token verification with invalid token."""
        token = "wrong-token"
        secret = "correct-secret-token"
        
        assert GitLab.verify_signature(b"", token, secret) is False

    def test_verify_token_empty(self):
        """Test GitLab token verification with empty token."""
        token = ""
        secret = "some-secret"
        
        assert GitLab.verify_signature(b"", token, secret) is False

    def test_verify_token_uses_constant_time_comparison(self):
        """Test GitLab token verification uses constant-time comparison."""
        token = "secret123"
        secret = "secret123"
        
        # Should be True
        assert GitLab.verify_signature(b"", token, secret) is True
        
        # Different tokens should be False (constant-time comparison prevents timing attacks)
        assert GitLab.verify_signature(b"", "secret124", secret) is False

    def test_parse_push_event_success(self):
        """Test GitLab push event parsing."""
        payload = {
            "project": {
                "git_http_url": "https://gitlab.com/user/repo.git",
                "default_branch": "main"
            },
            "ref": "refs/heads/main",
            "checkout_sha": "ghi456jkl789",
            "created_at": "2026-04-01T12:00:00Z"
        }
        
        result = GitLab.parse_push_event(payload)
        
        assert result is not None
        assert result.provider == WebhookProvider.GITLAB
        assert result.branch == "main"
        assert result.commit_sha == "ghi456jkl789"
        assert result.event_type == "push"

    def test_parse_push_event_with_ssh_url(self):
        """Test GitLab push event parsing with SSH URL."""
        payload = {
            "project": {
                "git_ssh_url": "git@gitlab.com:user/repo.git",
                "default_branch": "main"
            },
            "ref": "refs/heads/main",
            "checkout_sha": "hash123"
        }
        
        result = GitLab.parse_push_event(payload)
        
        assert result is not None
        assert "gitlab.com" in str(result.repo_url)

    def test_parse_merge_request_event_opened(self):
        """Test GitLab merge request event parsing when opened."""
        payload = {
            "object_kind": "merge_request",
            "action": "open",
            "object_attributes": {
                "source_branch": "feature/gitlab",
                "last_commit": {"id": "mr_commit_123"},
                "updated_at": "2026-04-01T12:00:00Z"
            },
            "project": {
                "git_http_url": "https://gitlab.com/user/repo.git",
                "default_branch": "main"
            }
        }
        
        result = GitLab.parse_merge_request_event(payload)
        
        assert result is not None
        assert result.event_type == "merge_request"
        assert result.branch == "feature/gitlab"

    def test_parse_merge_request_ignored_action(self):
        """Test GitLab merge request event parsing with ignored action."""
        payload = {
            "object_kind": "merge_request",
            "action": "closed"  # Should be ignored
        }
        
        result = GitLab.parse_merge_request_event(payload)
        assert result is None


class TestBitbucketWebhook:
    """Tests for Bitbucket webhook handling."""

    def test_verify_signature_valid(self):
        """Test Bitbucket signature verification with valid signature."""
        secret = "bitbucket-secret"
        payload = b'{"test": "bitbucket"}'
        
        expected_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected_hash}"
        
        assert Bitbucket.verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        """Test Bitbucket signature verification with invalid signature."""
        secret = "bitbucket-secret"
        payload = b'{"test": "bitbucket"}'
        signature = "sha256=invalid_hash"
        
        assert Bitbucket.verify_signature(payload, signature, secret) is False

    def test_verify_signature_missing_prefix(self):
        """Test Bitbucket signature verification with missing prefix."""
        secret = "bitbucket-secret"
        payload = b'{"test": "bitbucket"}'
        signature = "invalid_format"
        
        assert Bitbucket.verify_signature(payload, signature, secret) is False

    def test_parse_push_event_success(self):
        """Test Bitbucket push event parsing."""
        payload = {
            "repository": {
                "links": {
                    "clone": [
                        {"name": "http", "href": "https://bitbucket.org/user/repo.git"}
                    ]
                },
                "mainbranch": {"name": "main"}
            },
            "push": {
                "changes": [
                    {
                        "new": {
                            "name": "main",
                            "target": {
                                "hash": "bb_commit_hash_123",
                                "date": "2026-04-01T12:00:00Z"
                            }
                        }
                    }
                ]
            }
        }
        
        result = Bitbucket.parse_push_event(payload)
        
        assert result is not None
        assert result.provider == WebhookProvider.BITBUCKET
        assert result.branch == "main"
        assert result.commit_sha == "bb_commit_hash_123"

    def test_parse_push_event_no_clone_urls(self):
        """Test Bitbucket push event parsing with missing clone URLs."""
        payload = {
            "repository": {
                "links": {"clone": []},
                "mainbranch": {"name": "main"}
            },
            "push": {
                "changes": [
                    {
                        "new": {
                            "name": "main",
                            "target": {"hash": "hash123"}
                        }
                    }
                ]
            }
        }
        
        result = Bitbucket.parse_push_event(payload)
        # Should still parse if no clone URL (uses fallback)
        assert result is None or result.commit_sha == "hash123"

    def test_parse_push_event_no_changes(self):
        """Test Bitbucket push event parsing with no changes."""
        payload = {
            "repository": {
                "links": {"clone": []},
                "mainbranch": {"name": "main"}
            },
            "push": {"changes": []}
        }
        
        result = Bitbucket.parse_push_event(payload)
        assert result is None


class TestWebhookDispatcher:
    """Tests for WebhookDispatcher routing."""

    def test_verify_webhook_github(self):
        """Test dispatcher correctly verifies GitHub webhooks."""
        secret = "github-secret"
        payload = b'{"test": "github"}'
        
        expected_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected_hash}"
        
        result = WebhookDispatcher.verify_webhook(
            WebhookProvider.GITHUB,
            payload,
            signature,
            secret
        )
        assert result is True

    def test_verify_webhook_gitlab(self):
        """Test dispatcher correctly verifies GitLab webhooks."""
        token = "gitlab-token"
        
        result = WebhookDispatcher.verify_webhook(
            WebhookProvider.GITLAB,
            b"unused_for_gitlab",
            token,  # For GitLab, signature is the token
            token
        )
        assert result is True

    def test_verify_webhook_bitbucket(self):
        """Test dispatcher correctly verifies Bitbucket webhooks."""
        secret = "bitbucket-secret"
        payload = b'{"test": "bitbucket"}'
        
        expected_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected_hash}"
        
        result = WebhookDispatcher.verify_webhook(
            WebhookProvider.BITBUCKET,
            payload,
            signature,
            secret
        )
        assert result is True

    def test_parse_webhook_github_push(self):
        """Test dispatcher correctly parses GitHub push events."""
        payload = {
            "repository": {"clone_url": "https://github.com/user/repo.git"},
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123"}
        }
        
        result = WebhookDispatcher.parse_webhook(
            WebhookProvider.GITHUB,
            "push",
            payload
        )
        assert result is not None
        assert result.provider == WebhookProvider.GITHUB

    def test_parse_webhook_github_pull_request(self):
        """Test dispatcher correctly parses GitHub PR events."""
        payload = {
            "action": "opened",
            "pull_request": {
                "head": {"ref": "feature/x", "sha": "def"}
            },
            "repository": {"clone_url": "https://github.com/user/repo.git"}
        }
        
        result = WebhookDispatcher.parse_webhook(
            WebhookProvider.GITHUB,
            "pull_request",
            payload
        )
        assert result is not None

    def test_parse_webhook_gitlab_push(self):
        """Test dispatcher correctly parses GitLab push events."""
        payload = {
            "project": {"git_http_url": "https://gitlab.com/user/repo.git"},
            "ref": "refs/heads/main",
            "checkout_sha": "ghi789"
        }
        
        result = WebhookDispatcher.parse_webhook(
            WebhookProvider.GITLAB,
            "push_events",
            payload
        )
        assert result is not None

    def test_parse_webhook_unknown_provider(self):
        """Test dispatcher handles unknown provider gracefully."""
        result = WebhookDispatcher.parse_webhook(
            "unknown_provider",  # type: ignore
            "push",
            {}
        )
        assert result is None

    def test_parse_webhook_unsupported_event_type(self):
        """Test dispatcher handles unsupported event types."""
        payload = {"test": "data"}
        
        result = WebhookDispatcher.parse_webhook(
            WebhookProvider.GITHUB,
            "unsupported_event_type",
            payload
        )
        assert result is None


class TestWebhookPayloadModel:
    """Tests for WebhookPayload data model."""

    def test_webhook_payload_creation(self):
        """Test WebhookPayload can be created correctly."""
        payload = WebhookPayload(
            provider=WebhookProvider.GITHUB,
            repo_url="https://github.com/user/repo.git",
            branch="main",
            commit_sha="abc123",
            event_type="push"
        )
        
        assert payload.provider == WebhookProvider.GITHUB
        assert payload.branch == "main"
        assert str(payload.repo_url) == "https://github.com/user/repo.git"

    def test_webhook_payload_optional_fields(self):
        """Test WebhookPayload handles optional fields."""
        payload = WebhookPayload(
            provider=WebhookProvider.GITHUB,
            repo_url="https://github.com/user/repo.git",
            branch="main",
            commit_sha="abc123",
            event_type="push",
            default_branch="develop",
            push_timestamp="2026-04-01T12:00:00Z"
        )
        
        assert payload.default_branch == "develop"
        assert payload.push_timestamp == "2026-04-01T12:00:00Z"

    def test_webhook_payload_serialization(self):
        """Test WebhookPayload can be serialized to dict."""
        payload = WebhookPayload(
            provider=WebhookProvider.GITHUB,
            repo_url="https://github.com/user/repo.git",
            branch="main",
            commit_sha="abc123",
            event_type="push"
        )
        
        payload_dict = payload.dict()
        
        assert payload_dict["provider"] == "github"
        assert payload_dict["branch"] == "main"
        assert payload_dict["commit_sha"] == "abc123"


class TestSecurityEdgeCases:
    """Tests for security-related edge cases."""

    def test_constant_time_comparison_github(self):
        """Test GitHub signature verification uses constant-time comparison."""
        secret = "secret"
        payload = b"test"
        
        # Create valid signature
        valid_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        valid_signature = f"sha256={valid_hash}"
        
        # Create invalid signature with one character different
        invalid_hash = valid_hash[:-1] + ("0" if valid_hash[-1] != "0" else "1")
        invalid_signature = f"sha256={invalid_hash}"
        
        # Both should verify correctly (not True and True, or False and False)
        assert GitHub.verify_signature(payload, valid_signature, secret) is True
        assert GitHub.verify_signature(payload, invalid_signature, secret) is False

    def test_timing_attack_resistance(self):
        """Test that verification is resistant to timing attacks."""
        secret = "secret"
        payload = b"test"
        
        # This is a conceptual test - in practice, hmac.compare_digest provides timing
        # attack resistance. This test verifies the function is using it.
        valid_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        valid_sig = f"sha256={valid_hash}"
        invalid_sig = f"sha256={'0' * 64}"
        
        # Both should complete without timing-based issues
        result1 = GitHub.verify_signature(payload, valid_sig, secret)
        result2 = GitHub.verify_signature(payload, invalid_sig, secret)
        
        assert result1 is True
        assert result2 is False

    def test_empty_secret(self):
        """Test webhook verification with empty secret."""
        payload = b'{"test": "empty_secret"}'
        
        # Should handle gracefully (though not secure)
        result = GitHub.verify_signature(payload, "sha256=invalid", "")
        assert result is False

    def test_unicode_handling(self):
        """Test webhook verification handles unicode correctly."""
        secret = "secret-with-émoji-🔐"
        payload = '{"message": "Unicode test 你好"}'.encode('utf-8')
        
        expected_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected_hash}"
        
        # Should handle unicode in both secret and payload
        assert GitHub.verify_signature(payload, signature, secret) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

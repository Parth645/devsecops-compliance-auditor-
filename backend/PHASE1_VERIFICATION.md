# Phase 1 Verification Checklist

Use this checklist to verify that Phase 1 has been properly implemented and is working correctly.

---

## 🔍 Pre-Flight Checks

Before running the system, verify dependencies are installed:

```bash
# Check Python version
python --version
# Expected: Python 3.8+

# Check pip packages
pip list | grep -E "celery|redis|fastapi|sqlalchemy"
# Should show recent versions

# Check Redis
redis-cli --version
# Expected: redis-cli x.x.x

# Check PostgreSQL connection
psql -U postgres -d compliance_auditor -c "SELECT 1"
# Expected: Connection successful
```

---

## ✅ System Setup Verification

### 1. Redis Running

```bash
# Check Redis is running
redis-cli ping
# Expected output: PONG

# Check Redis info
redis-cli INFO
# Should show:
# redis_version, redis_mode: standalone/cluster
# connected_clients, used_memory
```

**Status**: ☐ Verified  
**Expected**: Redis accepting connections

---

### 2. Database Migrations Applied

```bash
# Check migration status
cd backend
alembic current
# Expected: Shows the latest migration (001_add_webhook_tables)

alembic history
# Should show:
# <base> -> 001_add_webhook_tables

# Verify tables exist
psql -U postgres -d compliance_auditor -c "\dt"
# Should show:
# webhook_configs
# webhook_events
# scan_triggers
# scan_profiles
# (plus existing tables)

# Check table schemas
psql -U postgres -d compliance_auditor -c "\d webhook_configs"
# Should show columns: id, org_id, provider, webhook_url, etc.
```

**Status**: ☐ Verified  
**Expected**: All webhook tables created with correct schema

---

### 3. Environment Variables Configured

```bash
# Check .env file exists
ls -la backend/.env
# Expected: File exists

# Verify key variables
grep -E "DATABASE_URL|REDIS_HOST|CELERY_BROKER" backend/.env
# Should show values for all three

# Test database connection via env
python -c "from schema.database import SessionLocal; db = SessionLocal(); print('✓ DB Connected')"
# Expected: ✓ DB Connected

# Test Redis connection via env
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print('✓ Redis:', r.ping())"
# Expected: ✓ Redis: True
```

**Status**: ☐ Verified  
**Expected**: All critical environment variables configured

---

## 🚀 Service Verification

### 4. Redis Service Healthy

```bash
# Terminal: Redis CLI
redis-cli

> PING
PONG

> INFO memory
# Check used_memory is reasonable

> DBSIZE
# Should show numeric count (≥ 0)

> SET test "Phase1Works"
OK

> GET test
"Phase1Works"

> DEL test
1

exit
```

**Status**: ☐ Verified  
**Expected**: Redis responding to all commands

---

### 5. Celery Worker Running

```bash
# Terminal 1: Start Celery worker
cd backend
celery -A celery_app worker --loglevel=info

# Expected output:
# [config] celery@hostname ready to accept tasks
# [autoscale] Starting pool with max=8 min=2 processes
# celery worker online

# Keep this running in background for tests
```

**Status**: ☐ Running  
**Expected**: Worker shows "ready to accept tasks"

---

### 6. FastAPI Backend Running

```bash
# Terminal 2: Start backend
cd backend
uvicorn main:app --reload

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

**Status**: ☐ Running  
**Expected**: API accepting connections on port 8000

---

## 🧪 Component Verification

### 7. Health Check Endpoint

```bash
# Terminal 3: Test health
curl http://localhost:8000/health

# Expected response (should be valid JSON):
{
  "status": "healthy",
  "service": "compliance-auditor-backend",
  "version": "1.0.0",
  "ai_enabled": true,
  "ai_components": {
    "legal_bert": true,
    "spacy": true,
    "policy_processor": true,
    "repository_scanner": true
  }
}
```

**Status**: ☐ Verified  
**Expected**: HTTP 200, "status": "healthy"

---

### 8. Webhook Handler Parsing

```bash
# Test webhook handler directly
cd backend
python3 << 'EOF'
import json
from webhook_handler import GitHub, GitLab, Bitbucket

# Test GitHub parsing
github_payload = {
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

result = GitHub.parse_push_event(github_payload)
assert result.provider == "github"
assert result.branch == "main"
assert result.commit_sha == "abc123def456"
print("✓ GitHub webhook parsing works")

# Test GitLab parsing
gitlab_payload = {
    "project": {
        "git_http_url": "https://gitlab.com/user/repo.git",
        "default_branch": "main"
    },
    "ref": "refs/heads/main",
    "checkout_sha": "def789ghi123"
}

result = GitLab.parse_push_event(gitlab_payload)
assert result.provider == "gitlab"
assert result.branch == "main"
print("✓ GitLab webhook parsing works")

# Test Bitbucket parsing
bitbucket_payload = {
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
                        "hash": "ghi456jkl789",
                        "date": "2026-04-01T12:00:00Z"
                    }
                }
            }
        ]
    }
}

result = Bitbucket.parse_push_event(bitbucket_payload)
assert result.provider == "bitbucket"
assert result.branch == "main"
print("✓ Bitbucket webhook parsing works")

print("\n✓✓✓ All webhook handlers verified!")
EOF
```

**Status**: ☐ Verified  
**Expected**: All three parsers working correctly

---

### 9. Database Model Creation

```bash
# Test models are importable and functional
cd backend
python3 << 'EOF'
from schema.schema import WebhookConfig, WebhookEvent, ScanTrigger, ScanProfile
from schema.database import SessionLocal
import uuid

# Test model instantiation
org_id = uuid.uuid4()
webhook = WebhookConfig(
    id=uuid.uuid4(),
    org_id=org_id,
    provider="github",
    webhook_url="https://example.com/webhook",
    webhook_secret="test-secret",
    active=True
)
print(f"✓ WebhookConfig created: {webhook}")

trigger = ScanTrigger(
    id=uuid.uuid4(),
    scan_id=uuid.uuid4(),
    trigger_type="webhook",
    trigger_source="github"
)
print(f"✓ ScanTrigger created: {trigger}")

profile = ScanProfile(
    id=uuid.uuid4(),
    org_id=org_id,
    name="Production",
    environment="production",
    scan_on_push=True,
    scan_on_pr=True
)
print(f"✓ ScanProfile created: {profile}")

print("\n✓✓✓ All models verified!")
EOF
```

**Status**: ☐ Verified  
**Expected**: All models instantiate successfully

---

### 10. Celery Task Registration

```bash
# Verify Celery tasks are registered
cd backend
celery -A celery_app inspect registered

# Expected output:
# Should include:
# - background_tasks.scan_repository_async
# - background_tasks.process_webhook_event
# - background_tasks.cleanup_old_scans

# Check active queues
celery -A celery_app inspect active_queues

# Expected output:
# Shows available queues and workers
```

**Status**: ☐ Verified  
**Expected**: All background tasks registered and available

---

### 11. Test Async Task Execution

```bash
# Send a task to Celery and verify it processes
cd backend
python3 << 'EOF'
from background_tasks import cleanup_old_scans
from celery.result import AsyncResult

# Queue a simple task
result = cleanup_old_scans.delay(days=30)
print(f"Task ID: {result.id}")
print(f"Task state: {result.state}")

# Wait for result (up to 10 seconds)
import time
for i in range(10):
    if result.ready():
        print(f"✓ Task completed!")
        print(f"✓ Result: {result.result}")
        break
    print(f"  Waiting for task... ({i+1}/10)")
    time.sleep(1)
else:
    print("✓ Task queued and processing (may take a moment)")

print("\n✓✓✓ Celery task execution verified!")
EOF

# Monitor in Celery worker terminal - should see task execution
```

**Status**: ☐ Verified  
**Expected**: Task queued and executed by worker

---

## 🔌 API Endpoint Verification

### 12. Webhook Event Listing

```bash
# Assuming you have an org_id from your system
ORG_ID="your-org-id-here"

# List webhook events (will be empty initially)
curl -H "Authorization: Bearer test-token" \
  http://localhost:8000/webhooks/events/$ORG_ID

# Expected response:
{
  "status": "success",
  "org_id": "your-org-id",
  "events": [],
  "count": 0
}
```

**Status**: ☐ Verified  
**Expected**: HTTP 200, empty events list (no webhooks received yet)

---

### 13. Test Webhook Signature Verification

```bash
# Test GitHub signature verification
cd backend
python3 << 'EOF'
import hmac
import hashlib
from webhook_handler import GitHub

secret = "test-secret-123"
payload = b'{"test": "payload"}'

# Create valid signature
expected_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
signature = f"sha256={expected_hash}"

# Test verification
is_valid = GitHub.verify_signature(payload, signature, secret)
print(f"✓ Valid signature verified: {is_valid}")
assert is_valid, "Signature verification failed!"

# Test invalid signature
is_invalid = GitHub.verify_signature(payload, "sha256=invalid", secret)
print(f"✓ Invalid signature rejected: {not is_invalid}")
assert not is_invalid, "Invalid signature should be rejected!"

print("\n✓✓✓ Signature verification working correctly!")
EOF
```

**Status**: ☐ Verified  
**Expected**: Valid signatures accepted, invalid ones rejected

---

## 📊 Database Verification

### 14. Check Database Indexes

```bash
# Verify indexes were created
psql -U postgres -d compliance_auditor << 'EOF'
-- List indexes on webhook tables
SELECT indexname, tablename FROM pg_indexes 
WHERE tablename IN ('webhook_configs', 'webhook_events', 'scan_triggers', 'scan_profiles')
ORDER BY tablename;

-- Expected: Should see indexes on org_id, status, provider, etc.
EOF
```

**Status**: ☐ Verified  
**Expected**: All expected indexes exist

---

### 15. Foreign Key Constraints

```bash
# Verify foreign key constraints
psql -U postgres -d compliance_auditor << 'EOF'
-- Check constraints
SELECT constraint_name, table_name FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY' 
AND table_name IN ('webhook_events', 'scan_triggers', 'scans')
ORDER BY table_name;

-- Expected: Should see foreign keys linking tables correctly
EOF
```

**Status**: ☐ Verified  
**Expected**: Foreign keys properly configured

---

## 🧩 Integration Tests

### 16. End-to-End Webhook Flow (Local Test)

```bash
# This tests the complete flow without ngrok

cd backend
python3 << 'EOF'
from fastapi.testclient import TestClient
from main import app
import json
import hmac
import hashlib
import uuid

client = TestClient(app)

# 1. Create test webhook payload
webhook_payload = {
    "action": "opened",
    "pull_request": {
        "head": {
            "ref": "feature/test",
            "sha": "abc123def456"
        },
        "updated_at": "2026-04-01T12:00:00Z"
    },
    "repository": {
        "clone_url": "https://github.com/test/repo.git",
        "default_branch": "main",
        "owner": {"id": 1}
    },
    "organization": {"id": 1}
}

payload_bytes = json.dumps(webhook_payload).encode()

# 2. Create valid signature
secret = "test-secret-123"
signature = f"sha256={hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()}"

# 3. Send webhook request
response = client.post(
    "/webhooks/github",
    content=payload_bytes,
    headers={
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    }
)

print(f"Response status: {response.status_code}")
print(f"Response body: {response.json()}")

# Expected: 202 (Accepted)
assert response.status_code == 202, f"Expected 202, got {response.status_code}"
assert response.json()["status"] == "accepted"
print("\n✓✓✓ End-to-end webhook flow verified!")
EOF
```

**Status**: ☐ Verified  
**Expected**: Webhook accepted and queued for processing

---

## ✨ Final Verification Summary

Complete this checklist to confirm Phase 1 is fully functional:

| Component | Check | Status |
|-----------|-------|--------|
| Redis running | Port 6379 open, PING responds PONG | ☐ |
| PostgreSQL connected | Database exists, tables created | ☐ |
| Migrations applied | 001_add_webhook_tables applied | ☐ |
| Envi vars configured | DATABASE_URL, REDIS_HOST, etc. | ☐ |
| Celery worker running | Shows "ready to accept tasks" | ☐ |
| API server running | Listening on port 8000 | ☐ |
| Health endpoint | Returns healthy status | ☐ |
| Webhook parsing | All 3 platforms parse correctly | ☐ |
| Database models | Models instantiate successfully | ☐ |
| Celery tasks registered | inspect registered shows tasks | ☐ |
| Task execution | Tasks process through worker | ☐ |
| API endpoints | Webhook event listing works | ☐ |
| Signature verification | Valid/invalid sigs handled correctly | ☐ |
| Database schema | Tables, indexes, constraints exist | ☐ |
| End-to-end workflow | Full webhook → scan flow works | ☐ |

**Overall Status**: ☐ **Phase 1 Ready for Testing**

---

## 🎯 What to Test Next

If all checks pass:

1. **Manual Webhook Test** - Use ngrok to test real GitHub webhook
2. **Scan Execution** - Verify scan actually runs and creates violations
3. **Webhook Event Audit** - Check webhook_events table for records
4. **Task Persistence** - Verify failed tasks can be retried
5. **Multi-tenant Isolation** - Ensure orgs can't see each other's webhooks

See **PHASE1_QUICKSTART.md** for detailed webhook testing instructions.

---

## 📞 Troubleshooting

If any checks fail:

1. Review **PHASE1_IMPLEMENTATION.md** troubleshooting section
2. Check service logs for errors
3. Verify environment variables
4. Ensure all services are running
5. Check database connectivity
6. Review Celery worker output for task errors

**Debug command**:
```bash
# Show full error details
celery -A celery_app worker --loglevel=debug
```

# Phase 1 Implementation Guide - Foundation & Infrastructure

**Version**: 1.0  
**Started**: April 1, 2026  
**Status**: Partially Complete

## Overview

Phase 1 lays the foundation for the DevSecOps Compliance Auditor's async architecture and webhook support. This document guides you through implementing and testing Phase 1 components.

## What's Been Completed ✅

### 1.1 Backend Infrastructure Setup
- ✅ Added Celery (`celery==5.3.0`) to requirements.txt
- ✅ Added webhook dependencies (PyJWT, hmac) to requirements.txt
- ✅ Created `celery_app.py` with Redis broker/backend configuration
- ✅ Updated `.env.example` with all required environment variables

**Files Modified/Created**:
- `requirements.txt` - Added Celery and webhook dependencies
- `.env.example` - Added Redis and Celery variables
- `celery_app.py` - New Celery application configuration

### 1.2 Webhook Framework Development
- ✅ Created `webhook_handler.py` with support for:
  - GitHub webhook handling and SHA256 HMAC verification
  - GitLab webhook handling and token verification
  - Bitbucket webhook handling and HMAC verification
  - Normalized `WebhookPayload` model for provider abstraction
  - `WebhookDispatcher` for routing

**Files Created**:
- `webhook_handler.py` - Webhook handlers for all platforms

### 1.3 Background Task Queue
- ✅ Created `background_tasks.py` with:
  - `scan_repository_async()` - Main async scan task
  - `process_webhook_event()` - Process webhook events and queue scans
  - `cleanup_old_scans()` - Maintenance task for old records
  - Task retry logic, timeout handling, and progress tracking

**Files Created**:
- `background_tasks.py` - Async task definitions

### 1.4 Database Schema Updates
- ✅ Added new models to `schema/schema.py`:
  - `WebhookConfig` - Webhook configuration per org/provider
  - `WebhookEvent` - Individual webhook events received
  - `ScanTrigger` - Links scans to their trigger source
  - `ScanProfile` - Environment-specific scan configurations
  - Updated `Scan` model with `trigger_id`, `started_at`, `repo_url`, `violations_count`, `metadata`

- ✅ Created migration `001_add_webhook_tables.py` with:
  - All new table definitions
  - Foreign key constraints with cascade/set-null policies
  - Appropriate indexes for performance

**Files Modified/Created**:
- `schema/schema.py` - Added webhook and scan profile models
- `migrations/001_add_webhook_tables.py` - Database migration

### 1.5 Webhook Endpoints
- ✅ Created `webhook_routes.py` with endpoints:
  - `POST /webhooks/github` - GitHub webhook handler
  - `POST /webhooks/gitlab` - GitLab webhook handler
  - `POST /webhooks/bitbucket` - Bitbucket webhook handler
  - `GET /webhooks/events/{org_id}` - List webhook events (multi-tenant)
  - `GET /webhooks/events/{org_id}/{event_id}` - Get event details

- ✅ Integrated webhook routes into `main.py`

**Files Modified/Created**:
- `webhook_routes.py` - New webhook endpoints
- `main.py` - Added webhook router import and inclusion

## Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Redis (Local Development)

**Option A: Docker**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Option B: Windows (Chocolatey)**
```bash
choco install redis-64
redis-server
```

**Option C: Manual Installation**
Download from https://redis.io/download

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/compliance_auditor

# Redis & Celery
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Webhook Secrets (from your GitHub/GitLab/Bitbucket settings)
GITHUB_WEBHOOK_SECRET=ghp_xxxxxxxxxxxxxxx
GITLAB_WEBHOOK_SECRET=glpat-xxxxxxxxxxxxxxx
BITBUCKET_WEBHOOK_SECRET=your-bitbucket-secret
```

### 4. Apply Database Migrations

```bash
# Run migrations
alembic upgrade head

# To check migration status
alembic current
alembic history
```

### 5. Start Celery Worker

```bash
# Windows
celery -A celery_app worker --loglevel=info

# Linux/Mac
celery -A celery_app worker --loglevel=info
```

### 6. Start Backend API

```bash
uvicorn main:app --reload
```

## Testing & Validation

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "compliance-auditor-backend",
  "ai_enabled": true,
  "ai_components": { ... }
}
```

### 2. Test Webhook Parsing

Use `test_webhook_handlers.py` (to be created):

```bash
python -m pytest test_webhook_handlers.py -v
```

### 3. Manual Webhook Testing with ngrok

For local testing using real GitHub/GitLab webhooks:

```bash
# In one terminal: Start ngrok
ngrok http 8000

# Note the public URL (e.g., https://xxxx-xx-xxx-xxx-xx.ngrok.io)

# In GitHub/GitLab:
# Settings → Webhooks → Add webhook
# Payload URL: https://xxxx-xx-xxx-xxx-xx.ngrok.io/webhooks/github
# Secret: your-webhook-secret
# Events: Push events, Pull requests

# Test by pushing to the repository
git push
```

### 4. Test Async Tasks

```bash
# Check Celery flower monitoring (optional)
pip install flower
celery -A celery_app flower

# Access at http://localhost:5555
```

### 5. Monitor Webhook Events

```bash
# List webhook events for organization
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/webhooks/events/{org_id}

# Get specific webhook event
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/webhooks/events/{org_id}/{event_id}
```

## Database Schema Overview

### New Tables Created

#### webhook_configs
Stores webhook configuration for each organization/provider

```sql
- id: UUID (primary key)
- org_id: UUID (foreign key to organizations)
- provider: String ('github', 'gitlab', 'bitbucket')
- webhook_url: Text
- webhook_secret: String
- events: JSON (list of events to listen for)
- branches: JSON (list of branches to scan)
- active: Boolean (default: true)
- created_at, updated_at: Timestamps
```

#### webhook_events
Stores individual webhook events for audit trail and reprocessing

```sql
- id: UUID (primary key)
- webhook_config_id: UUID (foreign key to webhook_configs)
- org_id: UUID (foreign key to organizations)
- event_type: String ('push', 'pull_request', 'merge_request', etc.)
- repo_url: Text
- branch: String
- commit_sha: String (indexed)
- status: String ('received', 'processing', 'processed', 'failed')
- scan_id: UUID (foreign key to scans, nullable)
- payload: JSON (full webhook payload)
- error_message: Text (if failed)
- retry_count: Integer (default: 0)
- created_at, updated_at, processed_at: Timestamps
```

#### scan_triggers
Links scans to their origin events for audit trail

```sql
- id: UUID (primary key)
- scan_id: UUID (foreign key to scans)
- trigger_type: String ('webhook', 'scheduled', 'manual', 'api', 'ci_pipeline')
- trigger_source: String ('github', 'gitlab', 'jenkins', etc.)
- webhook_event_id: UUID (foreign key to webhook_events, nullable)
- ci_pipeline_id: String (for CI systems)
- metadata: JSON (trigger-specific data)
- created_at: Timestamp
```

#### scan_profiles
Environment-specific scan configurations

```sql
- id: UUID (primary key)
- org_id: UUID (foreign key to organizations)
- name: String (e.g., 'Production', 'Development')
- environment: String ('dev', 'staging', 'production')
- scan_on_push: Boolean (default: true)
- scan_on_pr: Boolean (default: true)
- auto_approve: Boolean (default: false)
- enforcement_level: String ('warning', 'block')
- policies: JSON (enabled compliance frameworks)
- max_violations: Integer (threshold for blocking)
- min_risk_score: Float
- created_at, updated_at: Timestamps
```

### Modified Tables

#### scans
Added new fields:
- `trigger_id`: UUID foreign key to scan_triggers
- `started_at`: Timestamp when scan execution began
- `repo_url`: Text (for non-project scans)
- `violations_count`: Integer (shorthand for total violations)
- `metadata`: JSON (flexible scan metadata)

## Webhook Flow

```
GitHub/GitLab/Bitbucket Push Event
           ↓
   [POST /webhooks/{provider}]
           ↓
   Verify Signature/Token
           ↓
   Parse Payload → WebhookPayload
           ↓
   Store WebhookEvent in DB
           ↓
   Queue process_webhook_event() Celery Task
           ↓
   [Celery Worker]
           ↓
   Create Scan Record
           ↓
   Create ScanTrigger Record
           ↓
   Queue scan_repository_async() Task
           ↓
   Clone Repository
           ↓
   Analyze Files
           ↓
   Store Violations
           ↓
   Update Scan Status
```

## Troubleshooting

### Celery Failed to Connect to Redis
```
Error: [Errno 111] Connection refused

Solution:
1. Verify Redis is running: redis-cli ping
2. Check Redis host/port in .env: REDIS_HOST, REDIS_PORT
3. Ensure correct broker URL: redis://host:port/db
```

### Webhook Signature Verification Failed
```
Error: Invalid webhook signature

Solutions:
1. Verify webhook secret matches in .env and GitHub/GitLab
2. Check that signature header is being sent correctly
3. Ensure request body is used in signature calculation (not parsed JSON)
4. Check for webhook delivery logs in GitHub/GitLab admin
```

### Database Migration Fails
```
Error: relation "scan_triggers" already exists

Solution:
# Check current migration
alembic current

# If already applied, downgrade and re-apply
alembic downgrade -1
alembic upgrade head
```

### Celery Tasks Not Processing
```
Error: Task appears queued but never executes

Solutions:
1. Verify Celery worker is running: celery -A celery_app worker
2. Check worker logs for errors
3. Monitor with flower: celery -A celery_app flower
4. Verify task is registered: celery -A celery_app inspect registered
```

## Next Steps (Phase 1 Continuation)

### Not Yet Implemented
- [ ] Tenant context middleware (1.5)
- [ ] ScanProfile API endpoints (1.6)
- [ ] Unit tests for webhook handlers
- [ ] Integration tests for async tasks
- [ ] Webhook testing guide with examples
- [ ] Docker Compose setup for Redis + Celery
- [ ] Deployment documentation

### Quick Wins to Add
1. **Webhook Configuration UI** - Allow orgs to configure webhooks via API
2. **Webhook Retry Logic** - Reprocess failed webhook events
3. **Scan Status Polling** - Frontend can poll `/scans/{id}/status`
4. **Webhook Health Monitor** - Dashboard showing webhook health

## API Endpoints Summary

### Webhook Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/github` | GitHub webhook receiver |
| POST | `/webhooks/gitlab` | GitLab webhook receiver |
| POST | `/webhooks/bitbucket` | Bitbucket webhook receiver |
| GET | `/webhooks/events/{org_id}` | List webhook events |
| GET | `/webhooks/events/{org_id}/{event_id}` | Get event details |

### Scan Endpoints (Existing)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/org/scans` | List organization scans |
| POST | `/git-scan-detailed` | Trigger manual scan |
| GET | `/scan-history` | Scan history |

## Configuration Reference

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DATABASE_ECHO=False

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_TIMEOUT=300
CELERY_TASK_MAX_RETRIES=3

# Webhooks
GITHUB_WEBHOOK_SECRET=your-secret
GITLAB_WEBHOOK_SECRET=your-secret
BITBUCKET_WEBHOOK_SECRET=your-secret

# Features
ENABLE_WEBHOOKS=True
```

## Files Summary

### Created Files
1. `celery_app.py` - Celery configuration
2. `webhook_handler.py` - Webhook handlers for all platforms
3. `background_tasks.py` - Async tasks
4. `webhook_routes.py` - Webhook API endpoints
5. `migrations/001_add_webhook_tables.py` - Database migration

### Modified Files
1. `requirements.txt` - Added Celery and dependencies
2. `.env.example` - Added environment variables
3. `schema/schema.py` - Added webhook models
4. `main.py` - Added webhook router

## Performance Considerations

### Database Indexes
The migration creates indexes on:
- `webhook_configs(org_id, provider)` - Fast webhook config lookup
- `webhook_events(webhook_config_id, org_id, status, commit_sha)` - Webhook event queries
- `scan_triggers(scan_id, trigger_type)` - Trigger lookup
- `scans(trigger_id)` - Relation queries

### Celery Optimization
- `worker_prefetch_multiplier=4` - Balance between throughput and responsiveness
- `task_soft_time_limit=300s` - Prevent hung tasks
- `task_time_limit=600s` - Force kill if stuck
- `result_expires=3600` - Clean old results

### Redis Configuration
For production, consider:
- Redis Sentinel for HA
- RDB snapshots for persistence
- Memory optimization settings
- Network configuration for security

## Production Checklist

- [ ] Configure Redis with persistence (RDB/AOF)
- [ ] Set up Redis replication/Sentinel for HA
- [ ] Configure Celery worker pool (prefork, gevent, etc.)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure webhook retry policy
- [ ] Test webhook signature verification
- [ ] Set up dead letter queues for failed tasks
- [ ] Configure Celery task routing per priority
- [ ] Set up rate limiting on webhook endpoints
- [ ] Document webhook debugging procedures

## Support & Questions

For issues or questions about Phase 1:
1. Check troubleshooting section above
2. Review webhook test cases
3. Check Celery logging and worker status
4. Monitor Redis connectivity
5. Review database migration status

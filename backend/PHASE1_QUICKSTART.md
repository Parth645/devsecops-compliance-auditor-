# Phase 1 Quick Start - 5 Minutes to Running

Get Phase 1 up and running in just a few minutes!

## Prerequisites
- Python 3.8+
- PostgreSQL (or connection string)
- Docker (for Redis)

## Quick Setup

### 1. Install Dependencies (1 min)
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Redis (1 min)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or Windows using WSL
wsl -- redis-server

# Or native Windows
redis-server
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 3. Configure Environment (1 min)

Create `.env` file:
```bash
cp .env.example .env
```

Update key values:
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/compliance_auditor
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
GITHUB_WEBHOOK_SECRET=test-secret-123
GITLAB_WEBHOOK_SECRET=test-secret-456
BITBUCKET_WEBHOOK_SECRET=test-secret-789
```

### 4. Run Database Migrations (1 min)
```bash
alembic upgrade head
```

### 5. Start Services (Open 3 terminals)

**Terminal 1: Celery Worker**
```bash
celery -A celery_app worker --loglevel=info
```

**Terminal 2: Backend API**
```bash
uvicorn main:app --reload
```

**Terminal 3: (Optional) Monitor**
```bash
pip install flower
celery -A celery_app flower
# Access at http://localhost:5555
```

## Verify It's Working

### Check API Health
```bash
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "service": "compliance-auditor-backend", ...}
```

### Test a Manual Scan
```bash
# Terminal 3 or new terminal
curl -X POST http://localhost:8000/git-scan-detailed \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "git_repo_url": "https://github.com/your-username/your-repo.git",
    "branch": "main",
    "analysis_depth": "basic"
  }'

# Expected response:
# {
#   "status": "success",
#   "repo": "...",
#   "scan_duration": 12.5,
#   "compliance_issues": [...]
# }
```

## Test Webhook Locally with ngrok

### 1. Install ngrok
```bash
# Download from https://ngrok.com/download
# Or: brew install ngrok (macOS)
```

### 2. Start ngrok Tunnel
```bash
ngrok http 8000
```

Keep note of the public URL (e.g., `https://abcd-1234-efgh-5678.ngrok.io`)

### 3. Configure GitHub Webhook

1. Go to your repo → Settings → Webhooks → Add webhook
2. **Payload URL**: `https://your-ngrok-url/webhooks/github`
3. **Secret**: `test-secret-123` (from .env)
4. **Events**: Select "Let me select individual events" → Check "Pushes" and "Pull requests"
5. Click "Add webhook"

### 4. Trigger Webhook

Make a push to your repository:
```bash
git commit --allow-empty -m "Test webhook"
git push origin main
```

### 5. Monitor Webhook Event

Check webhook delivery in GitHub:
- Settings → Webhooks → Click on webhook → Recent Deliveries
- Should see successful (200) delivery

Monitor backend API:
```bash
# List webhook events
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8000/webhooks/events/{org_id}
```

Watch Celery worker terminal for task execution:
```
[2026-04-01 12:00:00,000: INFO/MainProcess] Received task: process_webhook_event[...]
[2026-04-01 12:00:01,000: INFO/MainProcess] Received task: scan_repository_async[...]
[2026-04-01 12:00:15,000: INFO/MainProcess] Task succeeded: ...
```

## Common Issues

### Redis Connection Refused
```bash
# Check if Redis is running
redis-cli ping

# If not, start it:
docker run -d -p 6379:6379 redis:7-alpine
```

### Celery Can't Connect to Broker
```
celery.exceptions.OperationalError: Error 111 connecting to localhost:6379

# Solution:
# 1. Check REDIS_HOST in .env is correct
# 2. Verify Redis is actually running: redis-cli ping
# 3. Check firewall rules
```

### Webhook Signature Verification Failed
```
# In logs: "Webhook signature verification failed"

# Solutions:
# 1. Verify webhook secret matches exactly in GitHub and .env
# 2. Check that secret is being sent in X-Hub-Signature-256 header
# 3. In GitHub: Delete and recreate the webhook
# 4. Check ngrok is forwarding headers correctly
```

### Database Migration Failed
```bash
# Check what happened
alembic current
alembic history

# If stuck, reset (only for dev!)
alembic downgrade -1
alembic upgrade head
```

## Next: Configure Scan Profiles

After verifying the basics, create scan profiles per environment:

```bash
curl -X POST http://localhost:8000/scan-profiles \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production",
    "environment": "production",
    "scan_on_push": true,
    "scan_on_pr": true,
    "enforcement_level": "block",
    "max_violations": 5,
    "min_risk_score": 80
  }'
```

## Continue to Phase 1 Deep Dive

For detailed configuration and troubleshooting, see:
👉 [PHASE1_IMPLEMENTATION.md](PHASE1_IMPLEMENTATION.md)

## Need Help?

1. **Celery not processing tasks?**
   - Ensure worker is running and connected to Redis
   - Check `celery -A celery_app inspect active_queues`
   - Check worker logs for errors

2. **Webhook not triggering?**
   - Verify ngrok URL is correct
   - Check GitHub webhook delivery history
   - Verify webhook secret matches

3. **Database query errors?**
   - Run migrations: `alembic upgrade head`
   - Check PostgreSQL connection string
   - Verify database exists and is accessible

4. **Unsure what to do next?**
   - Read PHASE1_IMPLEMENTATION.md
   - Check webhook_routes.py for endpoint examples
   - Monitor Celery with flower at http://localhost:5555

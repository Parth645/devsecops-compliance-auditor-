# Startup Guide - Cache Issues Resolution

## ⚠️ Important: Clear Cache Before Running

Due to Python bytecode caching, you must clear all cached files before running the application after code updates.

---

## 🔄 Step-by-Step Startup Process

### Step 1: Clear Python Caches
```bash
cd backend
python clear_cache.py
```

This will:
- Remove all `__pycache__` directories
- Delete all `.pyc` files
- Delete all `.pyo` files
- Output total items cleared

**Output example:**
```
============================================================
CLEARING PYTHON CACHES
============================================================

Removing __pycache__ directories...
  Removed 47 __pycache__ directories
Removing .pyc files...
  Removed 2,341 .pyc files
Removing .pyo files...
  Removed 0 .pyo files

============================================================
✓ Total items cleared: 2,388
============================================================

NEXT STEPS:
1. Stop any running servers (Ctrl+C)
2. Restart the application: python main.py
3. The application will recompile with fresh bytecode
```

### Step 2: Stop Any Running Servers
- If a server is running, stop it with `Ctrl+C`
- Wait for process to fully terminate

### Step 3: Start the Application
```bash
python main.py
```

---

## ✅ Verification Checklist

After startup, verify in logs:

```
INFO:ai_engine.semgrep_detector:✓ Semgrep detected: 1.157.0
INFO:ai_engine.indian_rules_manager:✓ Loaded 18 Indian compliance rules
INFO:ai_engine.compliance_analyzer:✓ Loaded 18 Indian compliance rules
INFO:ai_engine.groq_semgrep_verifier:✓ GroqSemgrepVerifier initialized
```

**Expected startup sequence:**
1. ✓ Semgrep detector initialization
2. ✓ Indian compliance rules loaded (18 rules)
3. ✓ Groq components initialized
4. ✓ Pipeline ready

**Issues to watch for:**
- ❌ `GroqBusinessLogicScanner.__init__() got an unexpected keyword argument 'scan_raw_files'`
  - Solution: Run `python clear_cache.py` and restart
- ❌ `Semgrep not found`
  - Solution: Run `pip install semgrep`
- ❌ `GROQ_API_KEY not found`
  - Solution: Set environment variable in `.env`

---

## 🛠️ Complete Startup Command Sequence

### On Windows (PowerShell):
```powershell
cd .\backend
python clear_cache.py
python main.py
```

### On Linux/Mac (Bash):
```bash
cd backend
python clear_cache.py
python main.py
```

---

## 📋 Full Initialization Log Expected

```
INFO:main:Starting FastAPI server...
INFO:main:Step 1: Initializing components...
INFO:main:Step 2-5: Running 4-stage compliance pipeline...

INFO:ai_engine.semgrep_detector:✓ Semgrep detected: 1.157.0

INFO:ai_engine.indian_rules_manager:✓ Loaded 18 Indian compliance rules
INFO:ai_engine.indian_rules_manager:  Frameworks: DPDPA, RBI, SEBI, IT_ACT, ISO_8000, GENERAL_SECURITY
INFO:ai_engine.indian_rules_manager:  CRITICAL: 12 rules
INFO:ai_engine.indian_rules_manager:  HIGH: 6 rules

INFO:ai_engine.compliance_analyzer:✓ AI-Driven Compliance Analyzer initialized
INFO:ai_engine.compliance_analyzer:  ✓ Loaded 18 Indian compliance rules
INFO:ai_engine.compliance_analyzer:  ✓ Step 1: Repo Profiler
INFO:ai_engine.compliance_analyzer:  ✓ Step 2: Policy Translator
INFO:ai_engine.compliance_analyzer:  ✓ Step 3a: Semgrep Detector
INFO:ai_engine.compliance_analyzer:  ✓ Step 3.5: Semgrep Verifier
INFO:ai_engine.compliance_analyzer:  ✓ Step 3b: Business Logic Scanner (DISABLED)
INFO:ai_engine.compliance_analyzer:  ✓ Step 4: Batch Mapper
INFO:ai_engine.compliance_analyzer:  ✓ Step 5: Gap Analyzer

INFO:ai_engine.groq_semgrep_verifier:✓ GroqSemgrepVerifier initialized (Proof-checking Semgrep findings)

INFO:ai_engine.groq_repo_profiler:✓ GroqRepoProfiler initialized
INFO:ai_engine.groq_policy_translator:✓ GroqPolicyTranslator initialized
INFO:ai_engine.groq_batch_mapper:✓ GroqBatchMapper initialized
INFO:ai_engine.gap_analyzer:✓ GapAnalyzer initialized

INFO:main:✓ Groq analyzer initialized successfully
INFO:uvicorn.server:Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to exit)
```

---

## 🚀 Production Deployment

For production deployments, always:

1. **Before deploying code changes:**
   ```bash
   python clear_cache.py
   ```

2. **Restart the service/process**
   - This forces fresh bytecode compilation

3. **Monitor logs for initialization errors:**
   - Check for any `TypeError` or `AttributeError`
   - Verify all components initialized successfully

---

## 🔍 Troubleshooting

### Issue: Still getting `scan_raw_files` parameter error after cache clear

**Solution:**
1. Double-check the process terminated
2. Verify no zombie Python processes
3. Clear cache again
4. Restart with explicit Python path

**Windows:**
```powershell
Get-Process python | Stop-Process -Force
python clear_cache.py
python main.py
```

**Linux:**
```bash
pkill -f "python main.py"
python clear_cache.py
python main.py
```

### Issue: Semgrep command not found

**Solution:**
```bash
pip install semgrep
semgrep --version
```

### Issue: .env not loading GROQ_API_KEY

**Solution:**
1. Check `.env` file exists in backend directory
2. Verify `GROQ_API_KEY=your_actual_key` is set
3. Restart the application

---

## 📊 Pipeline Architecture (After Fixes)

```
┌───────────────────────────────────────┐
│  STEP 3a: Semgrep Detection           │
│  Pattern-based scanning               │
│  Raw findings: ~52                    │
└──────────────┬────────────────────────┘
               ↓
┌───────────────────────────────────────┐
│  STEP 3.5: Semgrep Verifier (NEW)    │
│  Groq proof-checking                  │
│  • Extract code_snippet + message     │
│  • Verify: "Is this real?"            │
│  • Filter false positives             │
│  • Verified findings: ~12             │
└──────────────┬────────────────────────┘
               ↓
┌───────────────────────────────────────┐
│  STEP 3b: Business Logic (DISABLED)   │
│  Raw file scanning: OFF               │
└──────────────┬────────────────────────┘
               ↓
┌───────────────────────────────────────┐
│  STEP 4: Framework Mapping            │
│  Map to compliance frameworks         │
└──────────────┬────────────────────────┘
               ↓
          FINAL REPORT
```

---

## ✅ Verification Commands

```bash
# Test 1: Clear cache
python clear_cache.py

# Test 2: Verify imports
python -c "from ai_engine.compliance_analyzer import ComplianceAnalyzer; print('OK')"

# Test 3: Test GroqBusinessLogicScanner parameter
python -c "import inspect; from ai_engine.groq_business_logic_scanner import GroqBusinessLogicScanner; sig=inspect.signature(GroqBusinessLogicScanner.__init__); print('scan_raw_files' in sig.parameters)"

# Test 4: Full initialization
python -c "import os; os.environ['GROQ_API_KEY']='test'; from ai_engine.compliance_analyzer import ComplianceAnalyzer; ComplianceAnalyzer(); print('PASS')"
```

---

## 📞 Support

If issues persist after following this guide:

1. **Check logs for specific errors**
2. **Run verification commands above**
3. **Ensure all dependencies installed:**
   ```bash
   pip install -r requirements.txt
   pip install semgrep
   ```
4. **Clear system Python cache (Windows):**
   ```powershell
   Get-ChildItem -Path $env:APPDATA\..\Local\Python -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
   ```

---

## 🎯 Summary

| Step | Action | Purpose |
|------|--------|---------|
| 1 | `python clear_cache.py` | Remove stale bytecode |
| 2 | Stop running server | Ensure fresh start |
| 3 | `python main.py` | Start with fresh bytecode |
| ✓ | Check logs | Verify all components loaded |

**Expected result**: Application starts with no `scan_raw_files` parameter errors!

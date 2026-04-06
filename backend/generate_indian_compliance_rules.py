"""
Generate Indian Compliance Rules in JSON Format
Covers: DPDPA 2023, RBI Guidelines, SEBI Regulations, IT Act 2000, ISO 8000, and more
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_indian_compliance_rules():
    """Generate comprehensive Indian compliance rules"""
    
    rules = {
        "metadata": {
            "generated_date": datetime.now().isoformat(),
            "version": "1.0",
            "frameworks": ["DPDPA", "RBI", "SEBI", "IT_ACT", "ISO_8000", "SPDI"],
            "country": "India",
            "description": "Comprehensive Indian compliance rules for code scanning"
        },
        "frameworks": {
            # ==================== DPDPA 2023 ====================
            "DPDPA": {
                "title": "Digital Personal Data Protection Act, 2023",
                "authority": "Ministry of Electronics and Information Technology (MeitY)",
                "rules": {
                    "dpdpa_001_consent_before_processing": {
                        "id": "dpdpa_001",
                        "title": "Consent Before Processing",
                        "description": "Personal data must not be processed without explicit consent",
                        "section": "DPDPA Section 7 - Consent",
                        "severity": "critical",
                        "patterns": [
                            "db.store(userData) without consent check",
                            "process(personalData) without consent.validate()",
                            "sendEmail(user.email) without marketing_consent",
                            "analytics.track(userData) without analytics_consent",
                            "thirdParty.share(userData) without consent",
                            "profile_user(data) without consent"
                        ],
                        "keywords": ["personal_data", "pii", "consent", "user_data"],
                        "fix_template": """
if (!user.consent.processing) {
    throw new UnauthorizedError('Consent required for data processing');
}
// Then process data
database.store(userData);
                        """,
                        "impact": "Violation penalty: ₹5 crore or 2% annual turnover, criminal liability"
                    },
                    "dpdpa_002_purpose_limitation": {
                        "id": "dpdpa_002",
                        "title": "Purpose Limitation",
                        "description": "Data must only be used for disclosed, consented purposes",
                        "section": "DPDPA - Purpose Limitation Principle",
                        "severity": "critical",
                        "patterns": [
                            "collect for X, use for Y",
                            "telemetry_data used for profiling",
                            "payment_info used for marketing",
                            "health_data used for insurance_prediction",
                            "location_data used for competitor_analysis"
                        ],
                        "keywords": ["purpose", "secondary_use", "data_flow", "usage_context"],
                        "fix_template": """
// Validate purpose before use
if (data.intended_purpose !== current_operation.purpose) {
    throw new PurposeViolation('Data purpose mismatch');
}
                        """,
                        "impact": "Data processing for unauthorized purpose = violation"
                    },
                    "dpdpa_003_data_minimization": {
                        "id": "dpdpa_003",
                        "title": "Data Minimization",
                        "description": "Only necessary personal data should be collected and processed",
                        "section": "DPDPA - Minimization Principle",
                        "severity": "high",
                        "patterns": [
                            "collect: [email, phone, address, ssn, dob]  // Too much data",
                            "SELECT * FROM users_pii",
                            "store_all_fields(userData)",
                            "return {...user, ssn, phone, address, dob}  // Excessive"
                        ],
                        "keywords": ["data_minimization", "excessive_collection", "unnecessary_fields"],
                        "fix_template": """
// Only collect necessary fields
const requiredFields = ['email', 'phone'];  // Just what's needed
const userData = {
    email: user.email,
    phone: user.phone
    // Remove ssn, dob, address, etc.
};
                        """,
                        "impact": "Unnecessary data collection = principle violation"
                    },
                    "dpdpa_004_breach_notification": {
                        "id": "dpdpa_004",
                        "title": "Data Breach Notification",
                        "description": "Notify users within 72 hours of discovering a breach",
                        "section": "DPDPA Section 8.1 - Breach Notification",
                        "severity": "critical",
                        "patterns": [
                            "catch(security_breach) { /* do nothing */ }",
                            "if (database_compromised) { log_only() }  // No notification",
                            "breach_detected = true; // No action",
                            "compromised = true; continue_operation()  // No alert"
                        ],
                        "keywords": ["breach", "notification", "data_leak", "unauthorized_access"],
                        "fix_template": """
try {
    protectDatabase();
} catch (BreachException e) {
    logger.critical('BREACH DETECTED');
    await notifyUsers(72_hours_deadline);
    await notifyAuthority();
    recordBreach();
}
                        """,
                        "impact": "No breach notification = ₹10 crore penalty"
                    },
                    "dpdpa_005_user_rights": {
                        "id": "dpdpa_005",
                        "title": "User Rights Implementation",
                        "description": "Implement right to access, rectification, erasure, portability",
                        "section": "DPDPA Sections 16-18 - User Rights",
                        "severity": "high",
                        "patterns": [
                            "No DELETE endpoint",
                            "No EXPORT endpoint",
                            "No data correction mechanism",
                            "No access log for user requests"
                        ],
                        "keywords": ["user_rights", "data_deletion", "data_portability", "right_to_access"],
                        "fix_template": """
// Implement user rights endpoints
@app.get('/api/user/data/access')
async def right_to_access(): 
    return user_personal_data

@app.delete('/api/user/data')
async def right_to_erasure():
    await delete_all_personal_data(user_id)
    
@app.get('/api/user/data/export')
async def right_to_portability():
    return export_personal_data_json(user_id)
                        """,
                        "impact": "Missing user rights = non-compliance"
                    }
                }
            },
            
            # ==================== RBI GUIDELINES ====================
            "RBI": {
                "title": "Reserve Bank of India Guidelines",
                "authority": "Reserve Bank of India",
                "rules": {
                    "rbi_001_authorization_control": {
                        "id": "rbi_001",
                        "title": "Authorization Control",
                        "description": "Authorization must be enforced on server-side, not client-provided",
                        "section": "RBI Information Security Guidelines",
                        "severity": "critical",
                        "patterns": [
                            "const role = req.body.role",
                            "const access_level = req.query.level",
                            "if (req.body.is_admin) { approve_transaction() }",
                            "user.role = req.body.role"
                        ],
                        "keywords": ["authorization", "role_check", "privilege", "admin"],
                        "fix_template": """
// WRONG:  const role = req.body.role
// RIGHT:  Extract from verified JWT/session
const role = extractFromJWT(req.headers.authorization);

if (role !== 'admin') {
    return 403;
}
                        """,
                        "impact": "Authorization bypass = unauthorized transactions"
                    },
                    "rbi_002_transaction_atomicity": {
                        "id": "rbi_002",
                        "title": "Transaction Atomicity",
                        "description": "Financial transactions must be atomic (all-or-nothing)",
                        "section": "RBI Guidelines - Transaction Integrity",
                        "severity": "critical",
                        "patterns": [
                            "balance = get_balance(); if balance > amount: debit();  // Race condition",
                            "check(balance); debit(); credit();  // Not atomic",
                            "await select(); // ... gap ... await update();  // Concurrent",
                            "read + write without transaction"
                        ],
                        "keywords": ["transaction", "atomic", "race_condition", "concurrency"],
                        "fix_template": """
// Use pessimistic locking or transactions
BEGIN TRANSACTION;
balance = SELECT balance FROM accounts WHERE id = ? FOR UPDATE;
IF balance >= amount THEN
    UPDATE accounts SET balance = balance - amount;
    UPDATE accounts SET balance = balance + amount WHERE id = target;
    COMMIT;
ELSE
    ROLLBACK;
END IF;
                        """,
                        "impact": "Race conditions = double charging, financial loss"
                    },
                    "rbi_003_encryption_enforcement": {
                        "id": "rbi_003",
                        "title": "Encryption in Transit and at Rest",
                        "description": "Use TLS 1.2+ for transit, AES-256 for rest",
                        "section": "RBI Guidelines - Encryption",
                        "severity": "critical",
                        "patterns": [
                            "http://api.bank.com/transfer  // Not HTTPS",
                            "store(plaintext_password)",
                            "send_over_http(card_details)",
                            "database without encryption"
                        ],
                        "keywords": ["encryption", "https", "tls", "aes", "plaintext"],
                        "fix_template": """
// Enforce TLS 1.2+ everywhere
const secureConnection = tls.createSecureContext({
    minVersion: 'TLSv1.2',
    maxVersion: 'TLSv1.3'
});

// Encrypt sensitive data at rest
const encrypted = encrypt(sensitiveData, 'AES-256');
                        """,
                        "impact": "Unencrypted transmission = data interception, fraud"
                    },
                    "rbi_004_audit_trail": {
                        "id": "rbi_004",
                        "title": "Immutable Audit Trails",
                        "description": "Maintain 3-year audit logs of all transactions",
                        "section": "RBI Guidelines - Audit Trail",
                        "severity": "high",
                        "patterns": [
                            "No transaction logging",
                            "Modifiable logs",
                            "In-memory logging only",
                            "Log retention < 3 years"
                        ],
                        "keywords": ["audit", "logging", "transaction_log", "trail"],
                        "fix_template": """
// Append-only audit log
async function logTransaction(txn) {
    const auditEntry = {
        timestamp: Date.now(),
        user_id: txn.user_id,
        action: txn.action,
        amount: txn.amount,
        status: txn.status,
        hash: sha256(JSON.stringify(txn))  // Immutable
    };
    
    await auditLog.append(auditEntry);  // Append-only database
    // Keep for 3+ years
}
                        """,
                        "impact": "Missing audit logs = non-compliance, cannot prove legitimacy"
                    },
                    "rbi_005_rate_limiting": {
                        "id": "rbi_005",
                        "title": "Rate Limiting and Brute-Force Protection",
                        "description": "Implement rate limiting on sensitive operations",
                        "section": "RBI Guidelines - Security Controls",
                        "severity": "high",
                        "patterns": [
                            "No rate limit on login",
                            "Unlimited transaction attempts",
                            "No CAPTCHA on suspicious activity",
                            "Unlimited API requests"
                        ],
                        "keywords": ["rate_limit", "brute_force", "throttle", "captcha"],
                        "fix_template": """
// Implement rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,  // 15 minutes
    max: 5  // Max 5 requests per IP
});

app.post('/login', limiter, handleLogin);
app.post('/transfer', limiter, handleTransfer);
                        """,
                        "impact": "No rate limiting = brute-force attacks, account takeover"
                    }
                }
            },
            
            # ==================== SEBI REGULATIONS ====================
            "SEBI": {
                "title": "Securities and Exchange Board of India",
                "authority": "SEBI",
                "rules": {
                    "sebi_001_market_manipulation": {
                        "id": "sebi_001",
                        "title": "Anti-Market Manipulation",
                        "description": "Prevent unfair trading practices and information asymmetry",
                        "section": "SEBI - Insider Trading Regulations",
                        "severity": "critical",
                        "patterns": [
                            "selective_disclosure(insider_info, special_user)",
                            "delay_public_info(news) { give_to_vip_first() }",
                            "front_running: execute_trade_before_client_order",
                            "paint_tape: fake_volume_trading"
                        ],
                        "keywords": ["insider_trading", "market_manipulation", "front_running"],
                        "fix_template": """
// Ensure simultaneous disclosure
async function announceInfo(info) {
    // Release to ALL users at same time
    await broadcast(info, ALL_USERS);
    
    // Log order of disclosure
    logSimultaneousDisclosure(info, timestamp);
}

// Prevent front-running
validateOrderSequence(client_order_timestamp, execution_timestamp);
                        """,
                        "impact": "Market manipulation penalty under SEBI Act"
                    },
                    "sebi_002_transparency": {
                        "id": "sebi_002",
                        "title": "Transparency in Trading",
                        "description": "Transparent pricing, no hidden charges",
                        "section": "SEBI - Investor Protection",
                        "severity": "high",
                        "patterns": [
                            "hidden_commission",
                            "undisclosed_fees",
                            "variable_pricing_by_user"
                        ],
                        "keywords": ["transparency", "fees", "charges", "pricing"],
                        "fix_template": """
// Transparent pricing
const quote = {
    symbol: 'RELIANCE',
    buy_price: 2500.00,
    sell_price: 2500.50,
    charges: {
        brokerage: 20,
        fee: 5,
        tax: 45
    },
    total: 2570.50
};
// Always SHOW all charges before confirmation
showFullBreakdown(quote, user);
                        """,
                        "impact": "Lack of transparency = investor protection violation"
                    }
                }
            },
            
            # ==================== IT ACT 2000 & SPDI ====================
            "IT_ACT": {
                "title": "Information Technology Act 2000 & Sensitive Personal Data/Information (SPDI) Rules",
                "authority": "Ministry of Electronics and Information Technology",
                "rules": {
                    "it_001_unauthorized_access": {
                        "id": "it_001",
                        "title": "Unauthorized Access Prevention",
                        "description": "Prevent unauthorized access under Section 43/66",
                        "section": "IT Act Section 43 - Unauthorized Access",
                        "severity": "critical",
                        "patterns": [
                            "No authentication on sensitive endpoints",
                            "@app.get('/admin/users')  // No auth check",
                            "SELECT * allowed without login",
                            "SQL injection vulnerability"
                        ],
                        "keywords": ["unauthorized_access", "authentication", "injection"],
                        "fix_template": """
@app.get('/admin/users')
@require_authentication  // Add auth middleware
@require_role('admin')   // Add authorization
async def get_users():
    return protected_data

// Validate all inputs
user_id = validate_integer(request.query.user_id)
query = select_prepared_statement(user_id)  // Use parameterized queries
                        """,
                        "impact": "Section 43 - damages up to ₹1 crore"
                    },
                    "it_002_data_protection": {
                        "id": "it_002",
                        "title": "Sensitive Data Protection",
                        "description": "Protect SPDI (Sensitive Personal Data/Information)",
                        "section": "SPDI Rules - Data Security",
                        "severity": "critical",
                        "patterns": [
                            "logger.info(f'User: {email}, {phone}, {ssn}')",
                            "console.log(sensitiveData)",
                            "send_via_email(ssn)",
                            "store_plaintext(password)"
                        ],
                        "keywords": ["spdi", "sensitive_data", "pii", "logging"],
                        "fix_template": """
// Never log PII
logger.info('User registration completed');  // ✓ Safe

// Mask sensitive data
masked_phone = phone.slice(-4).padStart(10, '*');  // ****345678
masked_ssn = ssn.slice(-2).padStart(12, '*');     // **********23

// Hash passwords
password_hash = bcrypt.hash(password, 10);

// Send only essential data
send_email(email, {
    // Only email address, no sensitive data
});
                        """,
                        "impact": "SPDI compromise = Section 66/72 - imprisonment + penalty"
                    },
                    "it_003_input_validation": {
                        "id": "it_003",
                        "title": "Input Validation",
                        "description": "Validate all inputs to prevent injection attacks",
                        "section": "IT Act Section 65 - Tampering with Computer Source",
                        "severity": "critical",
                        "patterns": [
                            "query = 'SELECT * FROM users WHERE id = ' + request.id",
                            "eval(request.code)",
                            "exec(user_input)",
                            "No input sanitization"
                        ],
                        "keywords": ["injection", "validation", "sanitization"],
                        "fix_template": """
// Use parameterized queries
query = 'SELECT * FROM users WHERE id = ?';
result = execute(query, [user_id]);

// Validate and sanitize
if (!isValidEmail(email)) throw new ValidationError();
sanitized_input = sanitize(request.comment);
                        """,
                        "impact": "Section 65 - Tampering = imprisonment up to 3 years"
                    }
                }
            },
            
            # ==================== ISO 8000 ====================
            "ISO_8000": {
                "title": "ISO 8000 - Data Quality",
                "authority": "International Standards Organization",
                "rules": {
                    "iso_001_data_accuracy": {
                        "id": "iso_001",
                        "title": "Data Accuracy",
                        "description": "Data must be accurate and verified",
                        "section": "ISO 8000 - Data Quality",
                        "severity": "high",
                        "patterns": [
                            "store without validation",
                            "No verification mechanism",
                            "Accept unvalidated user input directly"
                        ],
                        "keywords": ["accuracy", "validation", "verification"],
                        "fix_template": """
// Verify data before storage
if (validatePhoneNumber(phone) && validateEmail(email)) {
    await database.store(userData);
} else {
    throw new ValidationError('Invalid data format');
}

// Use checksums
data_hash = sha256(data);
store_with_hash(data, data_hash);
                        """,
                        "impact": "Poor data quality affects business decisions"
                    }
                }
            },
            
            # ==================== GENERAL SECURITY ====================
            "GENERAL_SECURITY": {
                "title": "General Security Best Practices",
                "authority": "Industry Standard",
                "rules": {
                    "sec_001_credentials_in_code": {
                        "id": "sec_001",
                        "title": "No Hardcoded Credentials",
                        "description": "Never store API keys, passwords in code",
                        "severity": "critical",
                        "patterns": [
                            'api_key = "sk_live_abcd1234"',
                            'password = "admin123"',
                            'db_password = "mysql_root"',
                            'aws_secret = "aws_secret_access_key"'
                        ],
                        "keywords": ["credentials", "api_key", "password", "secret"],
                        "fix_template": """
// Use environment variables
const api_key = process.env.GROQ_API_KEY;
const db_password = process.env.DB_PASSWORD;

// Or use secrets manager
const secret = await secretsManager.get('db-password');
                        """,
                        "impact": "Hardcoded secrets = account compromise"
                    },
                    "sec_002_sql_injection": {
                        "id": "sec_002",
                        "title": "SQL Injection Prevention",
                        "description": "Always use parameterized queries",
                        "severity": "critical",
                        "patterns": [
                            "f\"SELECT * FROM users WHERE id = {user_id}\"",
                            "query = f'UPDATE {table} SET {column} = {value}'",
                            "Non-parameterized SQL queries"
                        ],
                        "keywords": ["sql_injection", "query", "parameterized"],
                        "fix_template": """
// WRONG:
query = f"SELECT * FROM users WHERE id = {user_id}"

// RIGHT:
query = "SELECT * FROM users WHERE id = ?"
database.execute(query, [user_id])
                        """,
                        "impact": "SQL injection = database compromise"
                    }
                }
            }
        }
    }
    
    return rules


def flatten_rules_for_scanning(rules_dict):
    """Flatten nested rules for easier scanning"""
    
    flattened = []
    
    for framework, framework_data in rules_dict["frameworks"].items():
        for rule_id, rule_data in framework_data.get("rules", {}).items():
            flattened_rule = {
                "id": rule_data["id"],
                "framework": framework,
                "title": rule_data["title"],
                "description": rule_data["description"],
                "severity": rule_data["severity"],
                "section": rule_data.get("section", ""),
                "patterns": rule_data.get("patterns", []),
                "keywords": rule_data.get("keywords", []),
                "fix_template": rule_data.get("fix_template", ""),
                "impact": rule_data.get("impact", "")
            }
            flattened.append(flattened_rule)
    
    return flattened


def save_rules_to_file(rules_dict, flattened_rules, output_file="policies/indian_compliance_rules.json"):
    """Save rules to JSON file"""
    
    # Ensure directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create output structure
    output = {
        "metadata": rules_dict["metadata"],
        "total_rules": len(flattened_rules),
        "rules_by_framework": {
            framework: len([r for r in flattened_rules if r["framework"] == framework])
            for framework in rules_dict["frameworks"].keys()
        },
        "rules": flattened_rules,
        "frameworks": rules_dict["frameworks"]
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Rules saved to: {output_file}")
    return output


def print_summary(rules_dict, flattened_rules):
    """Print summary of generated rules"""
    
    print("\n" + "="*80)
    print("INDIAN COMPLIANCE RULES GENERATION SUMMARY")
    print("="*80 + "\n")
    
    print("📋 Generated Rules by Framework:")
    for framework, framework_data in rules_dict["frameworks"].items():
        count = len(framework_data.get("rules", {}))
        print(f"   {framework:15} - {count:3} rules")
    
    print(f"\n📊 Total Rules:     {len(flattened_rules)}")
    print("\n🔍 Rule IDs Generated:")
    for rule in flattened_rules[:10]:
        print(f"   ✓ {rule['id']:20} - {rule['title']}")
    if len(flattened_rules) > 10:
        print(f"   ... and {len(flattened_rules) - 10} more rules")
    
    print("\n"*1)


def main():
    """Main function"""
    
    logger.info("Generating Indian Compliance Rules...")
    
    # Generate rules
    rules_dict = generate_indian_compliance_rules()
    flattened_rules = flatten_rules_for_scanning(rules_dict)
    
    # Save to file
    output = save_rules_to_file(rules_dict, flattened_rules)
    
    # Print summary
    print_summary(rules_dict, flattened_rules)
    
    logger.info("✓ Rule generation complete!")
    
    return output


if __name__ == "__main__":
    main()

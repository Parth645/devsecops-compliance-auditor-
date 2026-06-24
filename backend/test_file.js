// Test file for compliance scanning

// This should trigger: hardcoded secret
const API_KEY = 'sk_live_1234567890abcdef';

// This should trigger: no input validation
app.post('/user', (req, res) => {
    const userId = req.body.id;  // No validation!
    db.query('SELECT * FROM users WHERE id = ' + userId);  // SQL injection!
});

// This should trigger: missing consent check
function collectUserData(email, phone) {
    database.store({
        email: email,
        phone: phone
    });
    // No consent check!
}

// This should trigger: weak password policy
const passwordConfig = {
    minLength: 4  // Too short!
};

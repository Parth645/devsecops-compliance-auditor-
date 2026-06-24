
// Sample JavaScript with compliance issues
const API_KEY = 'pk_live_abcd1234';  // ISSUE: Hardcoded API key

class DataHandler {
    constructor() {
        this.personalData = [];
    }
    
    // ISSUE: No encryption for personal data
    storePersonalInfo(userData) {
        this.personalData.push({
            ssn: userData.ssn,
            creditCard: userData.creditCard,
            email: userData.email
        });
    }
    
    // GOOD: Audit logging
    logAccess(userId, action) {
        console.log(`Audit: ${userId} performed ${action} at ${new Date()}`);
    }
    
    // ISSUE: No proper authentication
    authenticateUser(username, password) {
        return username === 'admin' && password === 'admin';
    }
}

// ISSUE: Sensitive data in localStorage
localStorage.setItem('user_token', 'sensitive_token_value');

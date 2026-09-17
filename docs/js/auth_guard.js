// Auth Guard
function checkAuth() {
    const token = localStorage.getItem('techmart_token');
    if (!token) {
        window.location.href = 'login.html';
        return null;
    }
    
    try {
        const payloadBase64 = token.split('.')[1];
        const payloadDecoded = atob(payloadBase64);
        const payload = JSON.parse(payloadDecoded);
        
        // Check expiration
        const currentTime = Math.floor(Date.now() / 1000);
        if (payload.exp && payload.exp < currentTime) {
            // Token expired
            localStorage.removeItem('techmart_token');
            window.location.href = 'login.html';
            return null;
        }
        
        return payload;
    } catch (e) {
        // Invalid token
        localStorage.removeItem('techmart_token');
        window.location.href = 'login.html';
        return null;
    }
}

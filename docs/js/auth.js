const API_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : (window.location.origin.includes('onrender.com')
        ? window.location.origin
        : 'https://multi-agent-customer-support-pi1h.onrender.com');


function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = document.querySelector(`#${inputId} ~ button i`);
    if (input.type === 'password') {
        input.type = 'text';
        if(icon) { icon.classList.remove('bi-eye'); icon.classList.add('bi-eye-slash'); }
    } else {
        input.type = 'password';
        if(icon) { icon.classList.remove('bi-eye-slash'); icon.classList.add('bi-eye'); }
    }
}

async function login(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const btn = document.getElementById('loginBtn');
    const spinner = document.getElementById('loginSpinner');
    const errorAlert = document.getElementById('loginError');
    
    // Reset state
    errorAlert.classList.add('d-none');
    btn.disabled = true;
    spinner.classList.remove('d-none');
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('techmart_token', data.access_token);
            localStorage.setItem('techmart_session', data.session_id);
            localStorage.setItem('techmart_username', data.username);
            window.location.href = 'chat.html';
        } else {
            errorAlert.textContent = data.detail || 'Login failed';
            errorAlert.classList.remove('d-none');
        }
    } catch (error) {
        errorAlert.textContent = 'Network error. Please try again.';
        errorAlert.classList.remove('d-none');
    } finally {
        btn.disabled = false;
        spinner.classList.add('d-none');
    }
}

function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    
    if (strength === 0 || password.length === 0) return 'none';
    if (strength === 1) return 'weak';
    if (strength === 2) return 'medium';
    return 'strong';
}

function updateStrengthMeter(e) {
    const password = e.target.value;
    const strength = checkPasswordStrength(password);
    const meter = document.getElementById('strengthMeter');
    const text = document.getElementById('strengthText');
    
    meter.className = 'progress-bar'; // reset
    if (strength === 'weak') {
        meter.classList.add('bg-danger');
        meter.style.width = '33%';
        text.textContent = 'Weak';
        text.className = 'text-danger small';
    } else if (strength === 'medium') {
        meter.classList.add('bg-warning');
        meter.style.width = '66%';
        text.textContent = 'Medium';
        text.className = 'text-warning small';
    } else if (strength === 'strong') {
        meter.classList.add('bg-success');
        meter.style.width = '100%';
        text.textContent = 'Strong';
        text.className = 'text-success small';
    } else {
        meter.style.width = '0%';
        text.textContent = '';
    }
}

async function register(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    const btn = document.getElementById('registerBtn');
    const spinner = document.getElementById('registerSpinner');
    const errorAlert = document.getElementById('registerError');
    const successAlert = document.getElementById('registerSuccess');
    
    // Reset state
    errorAlert.classList.add('d-none');
    successAlert.classList.add('d-none');
    
    // Client-side validation
    if (username.length < 3) {
        errorAlert.textContent = 'Username must be at least 3 characters.';
        errorAlert.classList.remove('d-none');
        return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        errorAlert.textContent = 'Invalid email format.';
        errorAlert.classList.remove('d-none');
        return;
    }
    
    if (password.length < 8) {
        errorAlert.textContent = 'Password must be at least 8 characters.';
        errorAlert.classList.remove('d-none');
        return;
    }
    
    if (password !== confirmPassword) {
        errorAlert.textContent = 'Passwords do not match.';
        errorAlert.classList.remove('d-none');
        return;
    }
    
    btn.disabled = true;
    spinner.classList.remove('d-none');
    
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            successAlert.textContent = 'Registration successful! Redirecting...';
            successAlert.classList.remove('d-none');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            errorAlert.textContent = data.detail || 'Registration failed';
            errorAlert.classList.remove('d-none');
        }
    } catch (error) {
        errorAlert.textContent = 'Network error. Please try again.';
        errorAlert.classList.remove('d-none');
    } finally {
        if (!successAlert.classList.contains('d-none')) {
            // Success, leave button disabled while redirecting
        } else {
            btn.disabled = false;
            spinner.classList.add('d-none');
        }
    }
}

// On page load for login/register pages
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('techmart_token');
    if (token) {
        // Simple check, auth_guard does detailed check on chat page
        window.location.href = 'chat.html';
    }
    
    const passInput = document.getElementById('password');
    if (passInput && document.getElementById('strengthMeter')) {
        passInput.addEventListener('input', updateStrengthMeter);
    }
});

// For HTML inline access
window.login = login;
window.register = register;
window.togglePassword = togglePassword;

const API_BASE_URL = "http://localhost:8000";

function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    if (button) {
        button.textContent = isPassword ? "Hide" : "Show";
    }
}

function setLoading(buttonId, spinnerId, isLoading) {
    const button = document.getElementById(buttonId);
    const spinner = document.getElementById(spinnerId);
    if (!button || !spinner) return;
    button.disabled = isLoading;
    spinner.classList.toggle("d-none", !isLoading);
}

function showAlert(elementId, message) {
    const alert = document.getElementById(elementId);
    if (!alert) return;
    alert.textContent = message;
    alert.classList.remove("d-none");
}

function hideAlert(elementId) {
    const alert = document.getElementById(elementId);
    if (!alert) return;
    alert.classList.add("d-none");
    alert.textContent = "";
}

async function login(event) {
    event.preventDefault();
    hideAlert("login-error");
    setLoading("login-btn", "login-spinner", true);

    const email = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;

    try {
        const response = await fetch(API_BASE_URL + "/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Login failed.");
        }

        localStorage.setItem("techmart_token", data.access_token);
        localStorage.setItem("techmart_session", data.session_id);
        window.location.href = "chat.html";
    } catch (error) {
        showAlert("login-error", error.message || "Login failed.");
    } finally {
        setLoading("login-btn", "login-spinner", false);
    }
}

function passwordStrengthLevel(password) {
    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    return score;
}

function updatePasswordStrength(password) {
    const meter = document.getElementById("strength-fill");
    const text = document.getElementById("strength-text");
    if (!meter || !text) return;

    const score = passwordStrengthLevel(password);
    const levels = [
        { width: 0, label: "Strength: weak", cls: "bg-danger" },
        { width: 25, label: "Strength: weak", cls: "bg-danger" },
        { width: 50, label: "Strength: fair", cls: "bg-warning" },
        { width: 75, label: "Strength: good", cls: "bg-info" },
        { width: 100, label: "Strength: strong", cls: "bg-success" },
        { width: 100, label: "Strength: very strong", cls: "bg-success" }
    ];

    const selected = levels[score];
    meter.className = selected.cls;
    meter.style.width = selected.width + "%";
    text.textContent = selected.label;
}

async function register(event) {
    event.preventDefault();
    hideAlert("register-error");
    hideAlert("register-success");
    setLoading("register-btn", "register-spinner", true);

    const username = document.getElementById("username")?.value.trim();
    const email = document.getElementById("register-email")?.value.trim();
    const password = document.getElementById("register-password")?.value;
    const confirmPassword = document.getElementById("confirm-password")?.value;

    if (password !== confirmPassword) {
        showAlert("register-error", "Passwords do not match.");
        setLoading("register-btn", "register-spinner", false);
        return;
    }

    try {
        const response = await fetch(API_BASE_URL + "/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Registration failed.");
        }

        showAlert("register-success", "Registration successful. Redirecting to login...");
        setTimeout(() => {
            window.location.href = "login.html";
        }, 2000);
    } catch (error) {
        showAlert("register-error", error.message || "Registration failed.");
    } finally {
        setLoading("register-btn", "register-spinner", false);
    }
}

window.login = login;
window.register = register;
window.togglePassword = togglePassword;
window.updatePasswordStrength = updatePasswordStrength;

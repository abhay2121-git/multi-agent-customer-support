// Protected page - check auth immediately
const userData = checkAuth();
const API_URL = 'http://localhost:8000';
let currentSessionId = localStorage.getItem('techmart_session');
let isWaitingForResponse = false;

document.addEventListener('DOMContentLoaded', async () => {
    // Set username in navbar
    const storedUsername = localStorage.getItem('techmart_username');
    if (storedUsername) {
        document.getElementById('navUsername').textContent = storedUsername;
    } else if (userData && userData.sub) {
        document.getElementById('navUsername').textContent = `User ${userData.sub}`;
    }

    // Mobile sidebar toggle
    document.getElementById('sidebarToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
    });

    // Character counter
    const input = document.getElementById('messageInput');
    const charCount = document.getElementById('charCount');
    input.addEventListener('input', () => {
        charCount.textContent = `${input.value.length}/1000`;
    });

    // Load initial data
    await loadSessionsList();
    await loadTicketsCount();

    if (currentSessionId) {
        await loadSession(currentSessionId);
    } else {
        await startNewSession();
    }
});

function getAuthHeaders() {
    const token = localStorage.getItem('techmart_token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

async function loadSessionsList() {
    try {
        const response = await fetch(`${API_URL}/chat/sessions`, {
            headers: getAuthHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            const list = document.getElementById('sessionList');
            list.innerHTML = '';

            data.sessions.forEach((s, index) => {
                const div = document.createElement('div');
                div.className = `session-item ${s.session_id === currentSessionId ? 'active' : ''}`;
                div.onclick = () => loadSession(s.session_id);

                const date = s.created_at ? new Date(s.created_at).toLocaleDateString() : 'New';
                div.innerHTML = `
                    <div class="d-flex justify-content-between">
                        <span>Session #${data.sessions.length - index}</span>
                        <small class="text-muted">${date}</small>
                    </div>
                `;
                list.appendChild(div);
            });
        }
    } catch (e) {
        console.error('Error loading sessions', e);
    }
}

async function loadTicketsCount() {
    try {
        const response = await fetch(`${API_URL}/chat/tickets`, {
            headers: getAuthHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('ticketCount').textContent = data.tickets.length;
        }
    } catch (e) {
        console.error('Error loading tickets', e);
    }
}

async function startNewSession() {
    try {
        const response = await fetch(`${API_URL}/chat/new-session`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            currentSessionId = data.session_id;
            localStorage.setItem('techmart_session', currentSessionId);

            document.getElementById('messagesArea').innerHTML = '';
            showWelcomeMessage();
            await loadSessionsList();
        }
    } catch (e) {
        console.error('Error starting new session', e);
    }
}

async function loadSession(sessionId) {
    try {
        const response = await fetch(`${API_URL}/chat/history/${sessionId}`, {
            headers: getAuthHeaders()
        });

        if (response.status === 401 || response.status === 403) {
            // Unauth, start new
            await startNewSession();
            return;
        }

        if (response.ok) {
            const data = await response.json();
            currentSessionId = sessionId;
            localStorage.setItem('techmart_session', sessionId);

            const messagesArea = document.getElementById('messagesArea');
            messagesArea.innerHTML = '';

            if (!data.messages || data.messages.length === 0) {
                showWelcomeMessage();
            } else {
                data.messages.forEach(msg => {
                    displayMessage(msg.role, msg.content, msg.agent_used, msg.timestamp);
                });
            }
            scrollToBottom();
            await loadSessionsList(); // Update active state
        }
    } catch (e) {
        console.error('Error loading session', e);
    }
}

function showWelcomeMessage() {
    displayMessage('assistant', "Hello! I'm TechMart's AI Support Assistant. How can I help you today?");
}

function formatTime(isoString) {
    if (!isoString) {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function displayMessage(role, content, agentInfo = null, timestamp = null) {
    const messagesArea = document.getElementById('messagesArea');
    const timeStr = formatTime(timestamp);

    const wrapper = document.createElement('div');
    wrapper.className = `d-flex flex-column ${role === 'user' ? 'align-items-end' : 'align-items-start'}`;

    const bubble = document.createElement('div');
    bubble.className = `bubble ${role === 'user' ? 'user-bubble' : 'bot-bubble'}`;
    bubble.textContent = content;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = timeStr;
    bubble.appendChild(timeSpan);

    wrapper.appendChild(bubble);

    if (role === 'assistant' && agentInfo) {
        const badge = document.createElement('span');
        badge.className = 'agent-badge';
        badge.innerHTML = `🤖 ${agentInfo}`;
        wrapper.appendChild(badge);
    }

    messagesArea.appendChild(wrapper);
}

function addTypingIndicator() {
    const messagesArea = document.getElementById('messagesArea');
    const wrapper = document.createElement('div');
    wrapper.className = 'd-flex flex-column align-items-start typing-wrapper';

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    wrapper.appendChild(indicator);
    messagesArea.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
}

function scrollToBottom() {
    const area = document.getElementById('messagesArea');
    area.scrollTop = area.scrollHeight;
}

async function sendMessage(event) {
    event.preventDefault();
    if (isWaitingForResponse) return;

    const input = document.getElementById('messageInput');
    const btn = document.getElementById('sendBtn');
    const text = input.value.trim();

    if (!text) return;

    // UI updates
    input.value = '';
    document.getElementById('charCount').textContent = '0/1000';
    input.disabled = true;
    btn.disabled = true;
    isWaitingForResponse = true;

    displayMessage('user', text);
    scrollToBottom();

    const typingElement = addTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/chat/message`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                message: text,
                session_id: currentSessionId
            })
        });

        // Remove typing indicator
        typingElement.remove();

        if (response.status === 401 || response.status === 403) {
            logout();
            return;
        }

        const data = await response.json();

        if (response.ok) {
            displayMessage('assistant', data.response, data.agent_used, data.timestamp);

            if (data.ticket_number) {
                showTicketToast(data.ticket_number);
                loadTicketsCount();
            }
        } else {
            displayMessage('assistant', "I'm sorry, I encountered an error processing your message.");
        }
    } catch (error) {
        typingElement.remove();
        displayMessage('assistant', "Network error. Please try again later.");
    } finally {
        input.disabled = false;
        btn.disabled = false;
        isWaitingForResponse = false;
        input.focus();
        scrollToBottom();
    }
}

function showTicketToast(ticketNumber) {
    const toastEl = document.getElementById('ticketToast');
    const toastBody = document.getElementById('ticketToastBody');
    toastBody.textContent = `Support ticket ${ticketNumber} has been opened for this issue.`;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

async function logout() {
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
    } catch (e) {
        // Ignore network errors on logout
    }
    localStorage.removeItem('techmart_token');
    localStorage.removeItem('techmart_session');
    localStorage.removeItem('techmart_username');
    window.location.href = 'login.html';
}

window.startNewSession = startNewSession;
window.logout = logout;
window.sendMessage = sendMessage;

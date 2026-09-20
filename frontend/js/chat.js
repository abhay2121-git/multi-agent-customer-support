// Protected page - check auth immediately
const userData = checkAuth();
const API_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : (window.location.origin.includes('onrender.com')
        ? window.location.origin
        : 'https://multi-agent-customer-support-pi1h.onrender.com');

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

    // Wire up My Tickets button explicitly for desktop and mobile touch
    const myTicketsBtn = document.getElementById('myTicketsBtn');
    if (myTicketsBtn) {
        myTicketsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openTicketsModal();
        });
        myTicketsBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            openTicketsModal();
        });
    }

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
            const errorMsg = (data && data.detail) ? data.detail : "I'm sorry, I encountered an error processing your message.";
            displayMessage('assistant', errorMsg);
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

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showTicketToast(ticketNumber) {
    const toastEl = document.getElementById('ticketToast');
    const toastBody = document.getElementById('ticketToastBody');
    toastBody.innerHTML = `
        <div>Support ticket <strong>${escapeHtml(ticketNumber)}</strong> has been opened for this issue.</div>
        <button class="btn btn-sm btn-light text-primary fw-bold mt-2" onclick="openTicketsModal()">
            <i class="bi bi-eye me-1"></i> View Tickets
        </button>
    `;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

async function openTicketsModal() {
    const modalEl = document.getElementById('ticketsModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    const loadingEl = document.getElementById('ticketsLoading');
    const emptyEl = document.getElementById('ticketsEmpty');
    const listEl = document.getElementById('ticketsList');

    loadingEl.classList.remove('d-none');
    emptyEl.classList.add('d-none');
    listEl.innerHTML = '';

    try {
        const response = await fetch(`${API_URL}/chat/tickets`, {
            headers: getAuthHeaders()
        });

        loadingEl.classList.add('d-none');

        if (response.ok) {
            const data = await response.json();
            const tickets = data.tickets || [];
            document.getElementById('ticketCount').textContent = tickets.length;

            if (tickets.length === 0) {
                emptyEl.classList.remove('d-none');
                return;
            }

            tickets.forEach(ticket => {
                const item = document.createElement('div');
                item.className = 'ticket-card';

                const createdDate = ticket.created_at
                    ? new Date(ticket.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
                    : 'N/A';

                // Status badge styling
                let statusBadgeClass = 'bg-warning text-dark';
                const status = (ticket.status || 'open').toLowerCase();
                if (status === 'resolved' || status === 'closed') {
                    statusBadgeClass = 'bg-success text-white';
                } else if (status === 'in-progress' || status === 'in_progress') {
                    statusBadgeClass = 'bg-info text-dark';
                }

                // Priority badge styling
                let priorityBadgeClass = 'bg-secondary text-white';
                const priority = (ticket.priority || 'medium').toLowerCase();
                if (priority === 'high' || priority === 'critical') {
                    priorityBadgeClass = 'bg-danger text-white';
                } else if (priority === 'medium') {
                    priorityBadgeClass = 'bg-warning text-dark';
                }

                const isCurrentSession = ticket.session_id && ticket.session_id === currentSessionId;

                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <span class="fw-bold text-primary-brand fs-6">${escapeHtml(ticket.ticket_number)}</span>
                            <span class="badge ${statusBadgeClass} ms-2 text-uppercase" style="font-size: 0.7rem;">${escapeHtml(ticket.status || 'open')}</span>
                            <span class="badge ${priorityBadgeClass} ms-1 text-uppercase" style="font-size: 0.7rem;">${escapeHtml(ticket.priority || 'medium')}</span>
                        </div>
                        <small class="text-muted"><i class="bi bi-clock me-1"></i>${createdDate}</small>
                    </div>
                    <p class="text-dark mb-2" style="font-size: 0.9rem; line-height: 1.4;">
                        ${escapeHtml(ticket.issue_summary || 'No issue description.')}
                    </p>
                    ${ticket.session_id ? `
                        <div class="d-flex align-items-center justify-content-between pt-2 border-top">
                            <small class="text-muted">Session: ${escapeHtml(ticket.session_id.substring(0, 16))}...</small>
                            <button class="btn btn-sm ${isCurrentSession ? 'btn-outline-secondary disabled' : 'btn-outline-primary'}" onclick="loadSessionFromTicket('${escapeHtml(ticket.session_id)}')">
                                <i class="bi bi-chat-left-text me-1"></i> ${isCurrentSession ? 'Current Session' : 'View Session'}
                            </button>
                        </div>
                    ` : ''}
                `;
                listEl.appendChild(item);
            });
        } else {
            listEl.innerHTML = `<div class="p-3 text-center text-danger">Failed to load tickets. Please try again.</div>`;
        }
    } catch (e) {
        console.error('Error opening tickets modal', e);
        loadingEl.classList.add('d-none');
        listEl.innerHTML = `<div class="p-3 text-center text-danger">Network error loading tickets.</div>`;
    }
}

function loadSessionFromTicket(sessionId) {
    const modalEl = document.getElementById('ticketsModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
    loadSession(sessionId);
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
window.openTicketsModal = openTicketsModal;
window.loadSessionFromTicket = loadSessionFromTicket;


/* ==========================================================================
   EASY-CHATGPT — Frontend Logic
   Plain JavaScript, no modules, no build step.
   ========================================================================== */

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------
const chatMessages   = document.getElementById('chat-messages');
const chatForm       = document.getElementById('chat-form');
const chatInput      = document.getElementById('chat-input');
const sendBtn        = document.getElementById('send-btn');
const welcomeMessage = document.getElementById('welcome-message');

const contextPanel    = document.getElementById('context-panel');
const contextMessages = document.getElementById('context-messages');
const contextToggle   = document.getElementById('context-toggle');
const resetBtn        = document.getElementById('reset-btn');

const promptTokensEl     = document.getElementById('prompt-tokens');
const completionTokensEl = document.getElementById('completion-tokens');
const totalTokensEl      = document.getElementById('total-tokens');

// ---------------------------------------------------------------------------
// Configure marked.js for Markdown rendering
// ---------------------------------------------------------------------------
marked.setOptions({
    breaks: true,         // GFM line breaks
    gfm: true,            // GitHub-flavoured Markdown
    highlight: function (code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            try {
                return hljs.highlight(code, { language: lang }).value;
            } catch (_) { /* fall through */ }
        }
        // Auto-detect
        try {
            return hljs.highlightAuto(code).value;
        } catch (_) {
            return code;
        }
    },
});

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let isSending = false;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Create a chat message bubble and append it to the messages container.
 * @param {'user'|'assistant'|'error'} role
 * @param {string} content  — raw text (user) or HTML (assistant, error)
 * @param {boolean} isHtml  — if true, content is set as innerHTML
 * @returns {HTMLElement} the .message-content element (for later updates)
 */
function addMessage(role, content, isHtml = false) {
    // Hide welcome text on first message
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }

    const avatarText = role === 'user' ? 'U' : role === 'assistant' ? 'AI' : '⚠';

    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = avatarText;

    const body = document.createElement('div');
    body.className = 'message-body';

    const roleLabel = document.createElement('div');
    roleLabel.className = 'message-role';
    roleLabel.textContent = role;

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    if (isHtml) {
        contentEl.innerHTML = content;
    } else {
        contentEl.textContent = content;
    }

    body.appendChild(roleLabel);
    body.appendChild(contentEl);
    wrapper.appendChild(avatar);
    wrapper.appendChild(body);
    chatMessages.appendChild(wrapper);

    scrollToBottom();
    return contentEl;
}

/** Scroll the chat container to the bottom. */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/** Update the token counters in the context panel. */
function updateTokenDisplay(usage) {
    if (!usage) return;
    promptTokensEl.textContent     = usage.prompt_tokens.toLocaleString();
    completionTokensEl.textContent = usage.completion_tokens.toLocaleString();
    totalTokensEl.textContent      = usage.total_tokens.toLocaleString();
}

// ---------------------------------------------------------------------------
// 2.3.1 — Send a message
// ---------------------------------------------------------------------------
chatForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    if (isSending) return;

    const text = chatInput.value.trim();
    if (!text) return;

    // Show user message immediately
    addMessage('user', text);

    // Clear input and auto-resize
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Show loading indicator in assistant bubble
    const loadingEl = addMessage('assistant', '<span class="loading-dots">Thinking</span>', true);

    isSending = true;
    sendBtn.disabled = true;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            const errorText = err.detail || `Error ${res.status}`;
            // Replace loading with error
            loadingEl.closest('.message').remove();
            addMessage('error', errorText);
        } else {
            const data = await res.json();

            // Render assistant reply as Markdown
            loadingEl.innerHTML = marked.parse(data.reply || '');

            // Highlight code blocks that marked.js produced
            loadingEl.querySelectorAll('pre code').forEach(function (block) {
                hljs.highlightElement(block);
            });

            // Update token usage
            updateTokenDisplay(data.usage);
        }

        // Refresh context view
        await refreshContext();

    } catch (err) {
        loadingEl.closest('.message').remove();
        addMessage('error', 'Could not reach the server. Is the backend running?');
    } finally {
        isSending = false;
        sendBtn.disabled = false;
        chatInput.focus();
        scrollToBottom();
    }
});

// ---------------------------------------------------------------------------
// 2.3.2 — Update the context view
// ---------------------------------------------------------------------------
async function refreshContext() {
    try {
        const res = await fetch('/api/context');
        if (!res.ok) return;
        const data = await res.json();

        // Update token counters
        updateTokenDisplay(data.token_usage);

        // Render messages list
        if (data.messages.length === 0) {
            contextMessages.innerHTML = '<span class="context-empty">No messages yet.</span>';
            return;
        }

        contextMessages.innerHTML = '';
        data.messages.forEach(function (msg, i) {
            const entry = document.createElement('div');
            entry.className = `context-msg ${msg.role}`;

            const role = document.createElement('div');
            role.className = 'context-msg-role';
            role.textContent = `[${i}] ${msg.role}`;

            const content = document.createElement('div');
            content.className = 'context-msg-content';
            // Truncate long messages in context view for readability
            const maxLen = 300;
            const text = msg.content || '';
            content.textContent = text.length > maxLen
                ? text.substring(0, maxLen) + '…'
                : text;

            entry.appendChild(role);
            entry.appendChild(content);
            contextMessages.appendChild(entry);
        });

        // Scroll context to bottom
        contextMessages.scrollTop = contextMessages.scrollHeight;

    } catch (_) {
        // Silently fail — the context view is secondary
    }
}

// ---------------------------------------------------------------------------
// 2.3.3 — Reset conversation
// ---------------------------------------------------------------------------
resetBtn.addEventListener('click', async function () {
    try {
        const res = await fetch('/api/reset', { method: 'POST' });
        if (!res.ok) return;
    } catch (_) {
        return;
    }

    // Clear chat panel
    chatMessages.innerHTML = '';
    if (welcomeMessage) {
        // Re-create welcome message
        const welcome = document.createElement('div');
        welcome.className = 'welcome-message';
        welcome.id = 'welcome-message';
        welcome.innerHTML = '<div class="welcome-icon">💬</div><p>Start a conversation — type a message below.</p>';
        chatMessages.appendChild(welcome);
    }

    // Clear context panel
    contextMessages.innerHTML = '<span class="context-empty">No messages yet.</span>';

    // Reset token counters
    promptTokensEl.textContent = '0';
    completionTokensEl.textContent = '0';
    totalTokensEl.textContent = '0';

    chatInput.focus();
});

// ---------------------------------------------------------------------------
// Auto-resize textarea
// ---------------------------------------------------------------------------
chatInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Submit on Enter (Shift+Enter for newline)
chatInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// ---------------------------------------------------------------------------
// Context panel toggle (narrow viewports)
// ---------------------------------------------------------------------------
contextToggle.addEventListener('click', function () {
    contextPanel.classList.toggle('open');
});

// ---------------------------------------------------------------------------
// Initial context load
// ---------------------------------------------------------------------------
refreshContext();

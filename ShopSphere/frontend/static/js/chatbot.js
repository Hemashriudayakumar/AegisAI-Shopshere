// ShopSphere AI Customer Support Chatbot & Developer Mode Inspector

let isDevMode = localStorage.getItem('shopsphere_chat_dev_mode') === 'true';

function toggleChatbot() {
  const windowEl = document.getElementById('shopsphere-chat-window');
  if (!windowEl) return;
  windowEl.classList.toggle('hidden');
  if (!windowEl.classList.contains('hidden')) {
    document.getElementById('chat-user-input')?.focus();
  }
}

function setDevMode(enabled) {
  isDevMode = enabled;
  localStorage.setItem('shopsphere_chat_dev_mode', enabled ? 'true' : 'false');
  const devToggle = document.getElementById('chat-dev-mode-toggle');
  if (devToggle) devToggle.checked = enabled;

  // Toggle visibility of existing inspector cards
  document.querySelectorAll('.dev-inspector-card').forEach(card => {
    card.style.display = enabled ? 'block' : 'none';
  });
}

function sendSuggestedQuery(text) {
  const input = document.getElementById('chat-user-input');
  if (input) {
    input.value = text;
    sendChatMessage();
  }
}

async function sendChatMessage() {
  const input = document.getElementById('chat-user-input');
  const messagesContainer = document.getElementById('chat-messages-container');
  if (!input || !messagesContainer) return;

  const userText = input.value.trim();
  if (!userText) return;

  // Append user bubble
  appendChatBubble(userText, 'user');
  input.value = '';

  // Append typing indicator
  const typingId = 'typing-' + Date.now();
  appendTypingIndicator(typingId);

  // Check if active page has an order ID
  const pageOrderId = window.CURRENT_PAGE_ORDER_ID || null;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userText,
        current_order_id: pageOrderId
      })
    });

    const data = await res.json();
    removeTypingIndicator(typingId);

    if (data.success) {
      appendChatBubble(data.reply, 'bot', data.developer_metadata);
    } else {
      appendChatBubble('Sorry, I encountered an issue connecting to the customer support service.', 'bot');
    }
  } catch (err) {
    removeTypingIndicator(typingId);
    appendChatBubble('Network error. Please check your connection and try again.', 'bot');
  }
}

function appendChatBubble(text, sender, devMeta = null) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const bubbleWrapper = document.createElement('div');
  bubbleWrapper.className = `d-flex flex-column ${sender === 'user' ? 'align-items-end' : 'align-items-start'} mb-2`;

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;

  // Simple Markdown link and newline parsing
  let formattedText = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="bg-light text-dark px-1 rounded">$1</code>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>')
    .replace(/\n/g, '<br>');

  bubble.innerHTML = formattedText;
  bubbleWrapper.appendChild(bubble);

  // If developer metadata is available, build Developer Mode inspector card
  if (sender === 'bot' && devMeta) {
    const dec = (devMeta.policy_service?.decision || 'UNKNOWN').toUpperCase();
    const risk = (devMeta.tool_metadata?.risk_level || 'LOW').toUpperCase();

    let decClass = 'tag-allow';
    if (dec === 'BLOCK') decClass = 'tag-block';
    else if (dec === 'ESCALATE') decClass = 'tag-escalate';
    else if (dec === 'MODIFY') decClass = 'tag-modify';

    let riskClass = 'tag-low';
    if (risk === 'MEDIUM') riskClass = 'tag-med';
    else if (risk === 'HIGH') riskClass = 'tag-high';
    else if (risk === 'CRITICAL') riskClass = 'tag-crit';

    const inspector = document.createElement('div');
    inspector.className = 'dev-inspector-card';
    inspector.style.display = isDevMode ? 'block' : 'none';
    inspector.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-1">
        <span><i class="bi bi-cpu"></i> <strong>${devMeta.tool_name}</strong></span>
        <div>
          <span class="dev-tag ${riskClass}">RISK: ${risk}</span>
          <span class="dev-tag ${decClass}">AEGIS: ${dec}</span>
        </div>
      </div>
      <div class="text-secondary small mb-1">Args: ${JSON.stringify(devMeta.arguments)}</div>
      <div class="small text-light"><strong>Policy Reason:</strong> ${devMeta.policy_service?.reason || 'Permitted'}</div>
      <div class="text-muted" style="font-size: 0.65rem;">Execution: ${devMeta.execution_status}</div>
    `;
    bubbleWrapper.appendChild(inspector);
  }

  container.appendChild(bubbleWrapper);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator(id) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;
  const ind = document.createElement('div');
  ind.id = id;
  ind.className = 'chat-bubble bot text-muted fst-italic py-2 px-3';
  ind.innerHTML = '<span class="spinner-grow spinner-grow-sm me-1" role="status"></span> ShopSphere Agent is thinking...';
  container.appendChild(ind);
  container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator(id) {
  const ind = document.getElementById(id);
  if (ind) ind.remove();
}

document.addEventListener('DOMContentLoaded', () => {
  const devToggle = document.getElementById('chat-dev-mode-toggle');
  if (devToggle) {
    devToggle.checked = isDevMode;
    devToggle.addEventListener('change', (e) => {
      setDevMode(e.target.checked);
    });
  }

  const chatInput = document.getElementById('chat-user-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }
});


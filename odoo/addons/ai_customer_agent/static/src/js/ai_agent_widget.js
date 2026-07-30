/**
 * AI Customer Agent — Embeddable chat widget
 * -------------------------------------------------
 * Usage:
 * <script src="ai-agent-widget.js"
 *         data-endpoint="https://your-store.com/ai_agent/chat"
 *         data-store-name="My Store"
 *         data-primary-color="#1E2A4A"
 *         data-accent-color="#E8A33D"
 *         data-welcome="Hi! How can I help you?"
 *         data-lang="en">
 * </script>
 *
 * No library dependencies. Self-initializes on load. data-lang picks the
 * fixed-string UI language (placeholder, aria-labels, fallback messages) -
 * supported values: "en" (default), "es".
 */
(function () {
  "use strict";

  // Every string a visitor can read that ISN'T the agent's own reply lives
  // here, keyed by data-lang. Keeping this fixed-string UI in sync with the
  // language configured in Odoo (Settings -> AI Customer Agent) matters as
  // much as the system prompt does - a Spanish "Escribe tu mensaje..." on an
  // English site is just as much a language mismatch as a Spanish reply.
  var I18N = {
    en: {
      storeNameFallback: "the store",
      welcome: function (storeName) {
        return "Hi! I'm the virtual assistant for " + storeName + ". How can I help you today?";
      },
      headerTitle: function (storeName) {
        return storeName + " Assistant";
      },
      windowAriaLabel: "Customer support chat",
      statusOnline: "Online",
      closeAriaLabel: "Close chat",
      inputPlaceholder: "Type your message...",
      inputAriaLabel: "Message",
      sendAriaLabel: "Send message",
      launcherAriaLabel: "Open customer support chat",
      replyFallback: "I couldn't process your message. Please try again.",
      connectionError: "I couldn't connect to the assistant. Please try again in a few seconds.",
    },
    es: {
      storeNameFallback: "la tienda",
      welcome: function (storeName) {
        return "¡Hola! Soy el asistente virtual de " + storeName + ". ¿En qué puedo ayudarte hoy?";
      },
      headerTitle: function (storeName) {
        return "Asistente de " + storeName;
      },
      windowAriaLabel: "Chat de atención al cliente",
      statusOnline: "En línea",
      closeAriaLabel: "Cerrar chat",
      inputPlaceholder: "Escribe tu mensaje...",
      inputAriaLabel: "Mensaje",
      sendAriaLabel: "Enviar mensaje",
      launcherAriaLabel: "Abrir chat de atención al cliente",
      replyFallback: "No pude procesar tu mensaje. Intenta de nuevo.",
      connectionError: "No pude conectar con el asistente. Intenta de nuevo en unos segundos.",
    },
  };

  var scriptEl = document.currentScript;
  var t = I18N[scriptEl.dataset.lang] || I18N.en;
  var cfg = {
    endpoint: scriptEl.dataset.endpoint || "/ai_agent/chat",
    storeName: scriptEl.dataset.storeName || t.storeNameFallback,
    primaryColor: scriptEl.dataset.primaryColor || "#1E2A4A",
    accentColor: scriptEl.dataset.accentColor || "#E8A33D",
    welcome: scriptEl.dataset.welcome || t.welcome(scriptEl.dataset.storeName || t.storeNameFallback),
  };

  var sessionId =
    "sess-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);

  // ---------------------------------------------------------------------
  // Estilos (inyectados con prefijo "aiw-" para no chocar con el sitio host)
  // ---------------------------------------------------------------------
  var css = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&display=swap');

  .aiw-root {
    --aiw-primary: ${cfg.primaryColor};
    --aiw-accent: ${cfg.accentColor};
    --aiw-bg: #FFFFFF;
    --aiw-surface: #F5F6F8;
    --aiw-ink: #14161B;
    --aiw-ink-soft: #5B6270;
    --aiw-border: #E3E5EA;
    --aiw-bubble-agent: #F0F1F4;
    --aiw-radius: 20px;
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 2147483000;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
  }
  .aiw-root * { box-sizing: border-box; }

  .aiw-launcher {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--aiw-primary);
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 12px 28px -6px rgba(20, 22, 27, 0.35);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    position: relative;
  }
  .aiw-launcher:hover { transform: translateY(-2px); box-shadow: 0 16px 32px -6px rgba(20, 22, 27, 0.4); }
  .aiw-launcher:focus-visible { outline: 2px solid var(--aiw-accent); outline-offset: 3px; }
  .aiw-launcher-ring {
    position: absolute;
    inset: -6px;
    border-radius: 50%;
    border: 2px solid var(--aiw-accent);
    opacity: 0.55;
    animation: aiw-pulse 2.4s ease-out infinite;
  }
  @media (prefers-reduced-motion: reduce) { .aiw-launcher-ring { animation: none; } }
  @keyframes aiw-pulse {
    0% { transform: scale(0.92); opacity: 0.55; }
    70% { transform: scale(1.18); opacity: 0; }
    100% { opacity: 0; }
  }
  .aiw-launcher svg { width: 26px; height: 26px; }

  .aiw-window {
    position: absolute;
    bottom: 76px;
    right: 0;
    width: 380px;
    max-width: calc(100vw - 32px);
    height: 580px;
    max-height: calc(100vh - 120px);
    background: var(--aiw-bg);
    border-radius: var(--aiw-radius);
    box-shadow: 0 24px 60px -12px rgba(20, 22, 27, 0.28), 0 4px 16px -4px rgba(20,22,27,.12);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transform-origin: bottom right;
    transform: scale(0.92);
    opacity: 0;
    pointer-events: none;
    transition: transform 0.22s cubic-bezier(.2,.9,.3,1.2), opacity 0.18s ease;
  }
  .aiw-window.aiw-open { transform: scale(1); opacity: 1; pointer-events: auto; }
  @media (prefers-reduced-motion: reduce) { .aiw-window { transition: opacity 0.15s ease; transform: none; } }

  .aiw-header {
    background: var(--aiw-primary);
    color: #fff;
    padding: 18px 18px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }
  .aiw-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: rgba(255,255,255,0.14);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    flex-shrink: 0;
  }
  .aiw-header-text { flex: 1; min-width: 0; }
  .aiw-header-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .aiw-header-status {
    font-size: 12.5px;
    opacity: 0.82;
    display: flex;
    align-items: center;
    gap: 5px;
    margin-top: 2px;
  }
  .aiw-status-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--aiw-accent);
    box-shadow: 0 0 0 3px rgba(232,163,61,0.25);
  }
  .aiw-close {
    background: transparent;
    border: none;
    color: #fff;
    opacity: 0.75;
    cursor: pointer;
    padding: 6px;
    border-radius: 8px;
    display: flex;
    flex-shrink: 0;
  }
  .aiw-close:hover { opacity: 1; background: rgba(255,255,255,0.1); }

  .aiw-messages {
    flex: 1;
    overflow-y: auto;
    padding: 18px 16px;
    background: var(--aiw-surface);
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .aiw-row { display: flex; }
  .aiw-row.aiw-user { justify-content: flex-end; }
  .aiw-bubble {
    max-width: 78%;
    padding: 10px 14px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.45;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .aiw-row.aiw-agent .aiw-bubble {
    background: var(--aiw-bubble-agent);
    color: var(--aiw-ink);
    border-bottom-left-radius: 4px;
  }
  .aiw-row.aiw-user .aiw-bubble {
    background: var(--aiw-primary);
    color: #fff;
    border-bottom-right-radius: 4px;
  }
  .aiw-row.aiw-error .aiw-bubble {
    background: #FDEDEC;
    color: #A23B2E;
    border-bottom-left-radius: 4px;
  }

  .aiw-typing { display: flex; gap: 4px; padding: 4px 2px; }
  .aiw-typing span {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--aiw-ink-soft);
    animation: aiw-bounce 1.1s ease-in-out infinite;
  }
  .aiw-typing span:nth-child(2) { animation-delay: 0.15s; }
  .aiw-typing span:nth-child(3) { animation-delay: 0.3s; }
  @keyframes aiw-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
    30% { transform: translateY(-4px); opacity: 1; }
  }

  .aiw-inputbar {
    border-top: 1px solid var(--aiw-border);
    padding: 12px;
    display: flex;
    gap: 8px;
    align-items: flex-end;
    flex-shrink: 0;
    background: var(--aiw-bg);
  }
  .aiw-input {
    flex: 1;
    border: 1px solid var(--aiw-border);
    border-radius: 14px;
    padding: 10px 14px;
    font-size: 14px;
    font-family: inherit;
    resize: none;
    max-height: 100px;
    color: var(--aiw-ink);
    outline: none;
    transition: border-color 0.15s ease;
  }
  .aiw-input:focus { border-color: var(--aiw-primary); }
  .aiw-send {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: var(--aiw-primary);
    border: none;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.15s ease, opacity 0.15s ease;
  }
  .aiw-send:hover:not(:disabled) { background: var(--aiw-accent); }
  .aiw-send:disabled { opacity: 0.45; cursor: not-allowed; }
  .aiw-send:focus-visible { outline: 2px solid var(--aiw-accent); outline-offset: 2px; }
  `;

  var styleTag = document.createElement("style");
  styleTag.textContent = css;
  document.head.appendChild(styleTag);

  // ---------------------------------------------------------------------
  // DOM
  // ---------------------------------------------------------------------
  var root = document.createElement("div");
  root.className = "aiw-root";
  root.innerHTML = `
    <div class="aiw-window" id="aiw-window" role="dialog" aria-label="${t.windowAriaLabel}">
      <div class="aiw-header">
        <div class="aiw-avatar">${initials(cfg.storeName)}</div>
        <div class="aiw-header-text">
          <div class="aiw-header-title">${escapeHtml(t.headerTitle(cfg.storeName))}</div>
          <div class="aiw-header-status"><span class="aiw-status-dot"></span>${t.statusOnline}</div>
        </div>
        <button class="aiw-close" id="aiw-close" aria-label="${t.closeAriaLabel}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="aiw-messages" id="aiw-messages" aria-live="polite"></div>
      <div class="aiw-inputbar">
        <textarea class="aiw-input" id="aiw-input" rows="1" placeholder="${t.inputPlaceholder}" aria-label="${t.inputAriaLabel}"></textarea>
        <button class="aiw-send" id="aiw-send" aria-label="${t.sendAriaLabel}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg>
        </button>
      </div>
    </div>
    <button class="aiw-launcher" id="aiw-launcher" aria-label="${t.launcherAriaLabel}">
      <span class="aiw-launcher-ring"></span>
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z"/>
      </svg>
    </button>
  `;
  document.body.appendChild(root);

  var windowEl = root.querySelector("#aiw-window");
  var launcherEl = root.querySelector("#aiw-launcher");
  var closeEl = root.querySelector("#aiw-close");
  var messagesEl = root.querySelector("#aiw-messages");
  var inputEl = root.querySelector("#aiw-input");
  var sendEl = root.querySelector("#aiw-send");

  var hasGreeted = false;

  launcherEl.addEventListener("click", function () {
    var isOpen = windowEl.classList.toggle("aiw-open");
    if (isOpen) {
      if (!hasGreeted) {
        addMessage("agent", cfg.welcome);
        hasGreeted = true;
      }
      inputEl.focus();
    }
  });
  closeEl.addEventListener("click", function () {
    windowEl.classList.remove("aiw-open");
  });

  inputEl.addEventListener("input", function () {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + "px";
  });
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
  sendEl.addEventListener("click", handleSend);

  function handleSend() {
    var text = inputEl.value.trim();
    if (!text) return;
    addMessage("user", text);
    inputEl.value = "";
    inputEl.style.height = "auto";
    sendEl.disabled = true;
    var typingRow = addTyping();

    fetch(cfg.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: { message: text, session_id: sessionId },
      }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        typingRow.remove();
        var result = data.result || data;
        var reply = (result && result.reply) || t.replyFallback;
        addMessage("agent", reply);
      })
      .catch(function () {
        typingRow.remove();
        addMessage("error", t.connectionError);
      })
      .finally(function () {
        sendEl.disabled = false;
      });
  }

  function addMessage(role, text) {
    var row = document.createElement("div");
    row.className = "aiw-row aiw-" + role;
    var bubble = document.createElement("div");
    bubble.className = "aiw-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return row;
  }

  function addTyping() {
    var row = document.createElement("div");
    row.className = "aiw-row aiw-agent";
    row.innerHTML =
      '<div class="aiw-bubble aiw-typing"><span></span><span></span><span></span></div>';
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return row;
  }

  function initials(name) {
    return (name || "T")
      .split(" ")
      .slice(0, 2)
      .map(function (w) { return w.charAt(0).toUpperCase(); })
      .join("");
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
})();

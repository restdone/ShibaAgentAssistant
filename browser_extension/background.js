let ws = null;
let connected = false;
let activeTabId = null;
let retryDelay = 2000;
let retryTimer = null;
let heartbeatTimer = null;

function connect() {
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    return;
  }

  ws = new WebSocket("ws://localhost:9009");

  ws.onopen = () => {
    connected = true;
    retryDelay = 2000;
    console.log("[Shiba] Connected to WebSocket server");
    broadcast({ type: "status", connected: true });
    startHeartbeat();
  };

  ws.onclose = () => {
    connected = false;
    stopHeartbeat();
    console.log(`[Shiba] Disconnected. Retrying in ${retryDelay / 1000}s...`);
    broadcast({ type: "status", connected: false });
    scheduleReconnect();
  };

  ws.onerror = () => {
    // onerror is always followed by onclose
  };

  ws.onmessage = (event) => {
    let msg;
    try {
      msg = JSON.parse(event.data);
    } catch (e) {
      console.error("[Shiba] Bad message:", event.data);
      return;
    }

    // Ignore heartbeat acks
    if (msg.type === "pong") return;

    console.log("[Shiba] Received command:", msg);
    handleCommand(msg);
  };
}

function startHeartbeat() {
  stopHeartbeat();
  heartbeatTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify({ type: "ping" }));
      } catch (e) {
        // Connection is dead — force close to trigger onclose and reconnect
        connected = false;
        broadcast({ type: "status", connected: false });
        ws.close();
      }
    } else {
      // WebSocket not open but we think we're connected — fix it
      if (connected) {
        connected = false;
        broadcast({ type: "status", connected: false });
        stopHeartbeat();
        scheduleReconnect();
      }
    }
  }, 3000);
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

function scheduleReconnect() {
  if (retryTimer) clearTimeout(retryTimer);
  retryTimer = setTimeout(() => {
    retryTimer = null;
    connect();
    retryDelay = Math.min(retryDelay * 1.5, 10000);
  }, retryDelay);
}

function broadcast(data) {
  browser.runtime.sendMessage(data).catch(() => {});
}

// Handle messages from popup
browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "get_status") {
    // Also verify the WebSocket is actually open, not just flagged as connected
    const reallyConnected = connected && ws && ws.readyState === WebSocket.OPEN;
    sendResponse({ type: "status", connected: reallyConnected });
  }
  return true;
});

function handleCommand(msg) {
  const { id, command, params } = msg;

  if (command === "open_tab") {
    const url = (params && params.url) ? params.url : "about:newtab";
    browser.tabs.create({ url, active: true }).then((tab) => {
      if (url === "about:newtab" || !url || url === "about:blank") {
        sendResult(id, { tabId: tab.id, url: tab.url });
      } else {
        waitForLoad(tab.id, id);
      }
    }).catch((err) => {
      sendResult(id, null, err.message);
    });
    return;
  }

  browser.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
    if (!tabs || tabs.length === 0) {
      sendResult(id, null, "No active tab found");
      return;
    }
    const tab = tabs[0];
    activeTabId = tab.id;

    if (command === "get_info") {
      sendResult(id, { url: tab.url, title: tab.title });

    } else if (command === "navigate") {
      browser.tabs.update(tab.id, { url: params.url }).then(() => {
        waitForLoad(tab.id, id);
      });

    } else if (command === "get_text") {
      sendToContent(tab.id, id, { action: "get_text" });

    } else if (command === "get_html") {
      sendToContent(tab.id, id, { action: "get_html" });

    } else if (command === "click") {
      sendToContent(tab.id, id, { action: "click", selector: params.selector });

    } else if (command === "type") {
      sendToContent(tab.id, id, { action: "type", selector: params.selector, text: params.text });

    } else if (command === "scroll") {
      sendToContent(tab.id, id, { action: "scroll", x: params.x || 0, y: params.y || 500 });

    } else if (command === "screenshot") {
      browser.tabs.captureVisibleTab(null, { format: "png" }).then((dataUrl) => {
        sendResult(id, { screenshot: dataUrl });
      });

    } else if (command === "evaluate") {
      sendToContent(tab.id, id, { action: "evaluate", code: params.code });

    } else {
      sendResult(id, null, `Unknown command: ${command}`);
    }
  });
}

function sendToContent(tabId, commandId, payload) {
  browser.tabs.sendMessage(tabId, payload).then((result) => {
    sendResult(commandId, result);
  }).catch((err) => {
    sendResult(commandId, null, err.message);
  });
}

function sendResult(id, result, error) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ id, result, error: error || null }));
  }
}

function waitForLoad(tabId, commandId) {
  const listener = (updatedTabId, changeInfo) => {
    if (updatedTabId === tabId && changeInfo.status === "complete") {
      browser.tabs.onUpdated.removeListener(listener);
      browser.tabs.get(tabId).then((tab) => {
        sendResult(commandId, { url: tab.url, title: tab.title });
      });
    }
  };
  browser.tabs.onUpdated.addListener(listener);
}

// Start connection
connect();

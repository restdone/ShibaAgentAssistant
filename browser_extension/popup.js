const statusEl = document.getElementById("status");

function updateStatus(connected) {
  if (connected) {
    statusEl.textContent = "Connected";
    statusEl.className = "connected";
  } else {
    statusEl.textContent = "Disconnected";
    statusEl.className = "disconnected";
  }
}

// Ask background for current status on open — use the response directly
browser.runtime.sendMessage({ type: "get_status" }).then((response) => {
  if (response && response.type === "status") {
    updateStatus(response.connected);
  }
}).catch(() => {
  updateStatus(false);
});

// Also listen for live status updates pushed from background
browser.runtime.onMessage.addListener((msg) => {
  if (msg.type === "status") {
    updateStatus(msg.connected);
  }
});

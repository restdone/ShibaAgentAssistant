browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  try {
    if (msg.action === "get_text") {
      sendResponse({ text: document.body.innerText });

    } else if (msg.action === "get_html") {
      sendResponse({ html: document.body.innerHTML });

    } else if (msg.action === "click") {
      const el = document.querySelector(msg.selector);
      if (!el) {
        sendResponse({ error: `Element not found: ${msg.selector}` });
      } else {
        el.click();
        sendResponse({ ok: true });
      }

    } else if (msg.action === "type") {
      const el = document.querySelector(msg.selector);
      if (!el) {
        sendResponse({ error: `Element not found: ${msg.selector}` });
      } else {
        el.focus();
        el.value = msg.text;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        sendResponse({ ok: true });
      }

    } else if (msg.action === "scroll") {
      window.scrollBy(msg.x || 0, msg.y || 500);
      sendResponse({ ok: true });

    } else if (msg.action === "evaluate") {
      // eslint-disable-next-line no-eval
      const result = eval(msg.code);
      sendResponse({ result: String(result) });

    } else {
      sendResponse({ error: `Unknown action: ${msg.action}` });
    }
  } catch (e) {
    sendResponse({ error: e.message });
  }

  return true; // keep channel open for async
});

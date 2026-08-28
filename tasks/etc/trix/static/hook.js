//
(() => {
  const params = {};

  const query = new URLSearchParams(params).toString();
  const scriptUrl = document.currentScript?.src;

  let wsUrl;
  if (!scriptUrl) {
    wsUrl = `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/device?${query}`;
  } else {
    const url = new URL(scriptUrl);
    wsUrl = `${url.protocol === "https:" ? "wss:" : "ws:"}//${url.host}/device?${query}`;
  }

  const ws = new WebSocket(wsUrl);

  function sendEvent(event, payload) {
    ws.send(JSON.stringify({ event, payload }));
  }

  const log = (message, color = "blue") => {
    sendEvent("log", {
      message,
      color
    });
  };

  const table = data => {
    sendEvent("table", data);
  };

  function runCode(code) {
    eval(code);
  }

  ws.onmessage = e => {
    try {
      const { event, payload } = JSON.parse(e.data);

      if (event == "run-code") {
        runCode(payload);
      }
    } catch (err) {
      log(String(err), "pink");
    }
  };
})();

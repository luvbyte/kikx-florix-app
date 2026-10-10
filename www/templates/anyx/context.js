// context

const sendPostMessage = (event, payload = null) => {
  window.parent.postMessage(
    {
      event,
      payload
    },
    "*"
  );
};

const getPanel = () => $("#panel-screen");

const scr = {
  clear: () => getPanel().empty(),
  print: (...args) =>
    getPanel().append($("<p>").text(args.map(String).join(" ")))
};

const exit = () => sendPostMessage("exit");

window.addEventListener("message", e => {
  const { event, payload } = e.data;

  if (e.source !== window.parent) {
    sendPostMessage(event, payload);
    return;
  }

  if (event === "RUN_CODE") {
    eval(payload);
  } else if (event === "HTML_CODE") {
    $("body").html(payload);
  } else if (event === "RAW_HTML_CODE") {
    const iframe = $("<iframe>").attr("srcdoc", payload).css({
      width: "100%",
      height: "100vh",
      border: "0",
      display: "block"
    });

    $("body").html(iframe);
  }
});

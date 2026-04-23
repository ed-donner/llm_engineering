chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 1. When button is clicked in TOP frame
 // 1. Button clicked in TOP frame
 if (request.action === "requestCapture") {
  // Send a message to ALL frames in the tab to trigger the scan
  chrome.tabs.sendMessage(sender.tab.id, { action: "triggerScan" });
}

  // 2. When text is sent from SUB frame
  if (request.action === "analyze") {
    fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: request.text })
    })
    .then(res => res.json())
    .then(data => {
      // Send results back to the TOP frame UI
      chrome.tabs.sendMessage(sender.tab.id, { action: "updateUI", data: data });
    })
    .catch(err => {
      chrome.tabs.sendMessage(sender.tab.id, { 
        action: "updateUI", 
        data: { error: "Backend unreachable. Ensure main.py is running." } 
      });
    });
  }
  return true;
});
  
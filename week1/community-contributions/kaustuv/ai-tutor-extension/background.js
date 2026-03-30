chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyze") {
      console.log("Background received text. Calling Python API...");
      
      fetch("http://127.0.0.1", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: request.text })
      })
      .then(res => res.json())
      .then(data => {
        console.log("API Success. Sending to UI...");
        // CRITICAL: Send to the TAB, not just the sender frame
        chrome.tabs.sendMessage(sender.tab.id, { action: "updateUI", data: data });
      })
      .catch(err => console.error("Fetch Error:", err));
      
      return true; // Keep channel open
    }
  });
  
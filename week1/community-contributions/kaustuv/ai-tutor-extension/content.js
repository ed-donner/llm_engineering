const isTopFrame = window.top === window.self;

if (isTopFrame) {
    console.log("[AI Tutor] UI Setup in TOP frame.");
    const sidebar = document.createElement('div');
    sidebar.id = 'ai-tutor-sidebar';
    sidebar.style.cssText = "position:fixed;right:20px;top:70px;width:340px;background:white;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.3);z-index:2147483647;padding:20px;font-family:Segoe UI, sans-serif;border:1px solid #ddd;max-height:85vh;overflow-y:auto;pointer-events:auto;";
    sidebar.innerHTML = `
        <h3 style="margin:0;color:#0078d4;">Selective Coach</h3>
        <div id="tutor-status" style="color:orange;margin-top:5px;font-weight:bold;">Waiting for typing...</div>
        <div id="tutor-summary"></div>
        <div id="details-container" style="display:none; margin-top:15px; border-top:1px solid #eee; padding-top:10px;">
            <h4 style="margin-bottom:10px; font-size:14px; color:#444;">Rubric Violations</h4>
            <div id="tutor-details-list"></div>
        </div>
        <button id="toggle-details" style="display:none; margin-top:15px; width:100%; padding:8px; cursor:pointer; background:#f8f9fa; border:1px solid #ccc; border-radius:5px;">Show Details</button>
    `;
    document.body.appendChild(sidebar);

    chrome.runtime.onMessage.addListener((msg) => {
        if (msg.action === "updateUI") {
            document.getElementById('tutor-status').innerHTML = `<span style="color:green;font-size:20px;">Score: ${msg.data["Overall score out of 25"]}/25</span>`;
            document.getElementById('tutor-summary').innerHTML = `
                <div style="background:#f0f9ff;padding:10px;border-left:4px solid #0078d4;margin:10px 0;"><b>Glow:</b> ${msg.data["Detailed Feedback"]?.Good}</div>
                <div style="background:#fff5f5;padding:10px;border-left:4px solid #e81123;"><b>Grow:</b> ${msg.data["Detailed Feedback"]?.Improve}</div>`;
            
            let dHtml = "";
            (msg.data.Details || []).forEach(item => {
                dHtml += `<div style="font-size:12px; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;">
                    <b style="color:#d35400;">Line ${item["Line number which violates rubric item"]}: ${item["Which rubric item it violates"]}</b><br>
                    <i style="color:#666;">"${item["Extract which violates rubric"]}"</i><br>
                    <b>Why:</b> ${item["Reason for violating rubric"]}<br>
                    <b style="color:green;">Try:</b> ${item["Improvement with example"]}
                </div>`;
            });
            document.getElementById('tutor-details-list').innerHTML = dHtml;
            document.getElementById('toggle-details').style.display = "block";
            document.getElementById('toggle-details').onclick = () => {
                const cont = document.getElementById('details-container');
                const hide = cont.style.display === "none";
                cont.style.display = hide ? "block" : "none";
                document.getElementById('toggle-details').innerText = hide ? "Hide Details" : "Show Details";
            };
        }
    });
}

// SENSOR LOGIC (Runs in ALL frames to find where Word is hiding the text)
let lastText = "";
setInterval(() => {
    // 1. Try common Word Online selectors
    let editor = document.querySelector('.WACViewPanel_WordCore_EventLayer') || 
                 document.querySelector('.Paragraph') || 
                 document.querySelector('[role="textbox"]');
    
    let text = editor ? (editor.innerText || editor.textContent || "") : "";

    // 2. Fallback: If no editor found, check the whole body if it has substantial content
    if (text.length < 20) {
        const bodyText = document.body.innerText || "";
        // We look for text that looks like a document (over 100 chars) but isn't just UI labels
        if (bodyText.length > 100 && bodyText.includes(" ")) {
            text = bodyText;
        }
    }

    // 3. Send if text is new and significant
    if (text.length > 50 && text !== lastText) {
        console.log("[AI Tutor] Text detected (" + text.length + " chars). Sending...");
        lastText = text;
        chrome.runtime.sendMessage({ action: "analyze", text: text });
    }
}, 7000);

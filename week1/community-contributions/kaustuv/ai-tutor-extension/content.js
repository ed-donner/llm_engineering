const isTopFrame = window.top === window.self;

if (isTopFrame) {
    const injectSidebar = () => {
        if (document.getElementById('ai-tutor-sidebar')) return;

        const sidebar = document.createElement('div');
        sidebar.id = 'ai-tutor-sidebar';
        
        sidebar.style.cssText = `
            position: fixed;
            right: 20px;
            top: 70px;
            width: 350px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 2147483647;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, sans-serif;
            border: 1px solid #ddd;
            pointer-events: auto; 
            max-height: 85vh;
            overflow-y: auto;
        `;
        
        sidebar.innerHTML = `
            <h3 style="margin:0;color:#0078d4;">Selective Coach</h3>
            <div id="tutor-status" style="color:orange;margin-top:5px;font-weight:bold;">Ready to Check</div>
            <button id="check-writing-btn" style="margin-top:15px; width:100%; padding:10px; background:#0078d4; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">Check Writing</button>
            
            <div id="tutor-main-results">
                <div id="tutor-score-display" style="margin-top:15px;"></div>
                <div id="tutor-content" style="margin-top:10px;"></div>
            </div>

            <div id="details-section" style="display:none; margin-top:15px; border-top:1px solid #eee; padding-top:15px;">
                <h4 style="margin:0 0 10px 0; font-size:14px; color:#444;">Rubric Violations</h4>
                <div id="tutor-details-list"></div>
            </div>
            
            <button id="toggle-details-btn" style="display:none; margin-top:15px; width:100%; padding:8px; background:#f8f9fa; color:#444; border:1px solid #ccc; border-radius:5px; cursor:pointer; font-size:12px;">Show Details</button>
        `;
        
        document.body.appendChild(sidebar);

        document.getElementById('check-writing-btn').onclick = () => {
            document.getElementById('tutor-status').innerText = "Requesting text...";
            document.getElementById('tutor-content').innerHTML = "";
            document.getElementById('tutor-score-display').innerHTML = "";
            document.getElementById('details-section').style.display = "none";
            document.getElementById('toggle-details-btn').style.display = "none";
            chrome.runtime.sendMessage({ action: "requestCapture" });
        };

        setupListener();
    };

    const setupListener = () => {
        chrome.runtime.onMessage.addListener((msg) => {
            if (msg.action === "updateUI") {
                const status = document.getElementById('tutor-status');
                const scoreDisplay = document.getElementById('tutor-score-display');
                const content = document.getElementById('tutor-content');
                const detailsList = document.getElementById('tutor-details-list');
                const toggleBtn = document.getElementById('toggle-details-btn');
                const detailsSection = document.getElementById('details-section');

                // 1. Update Score & Header
                const score = msg.data["Overall score out of 25"] || "N/A";
                status.innerText = "Analysis Complete";
                scoreDisplay.innerHTML = `<b style="color:green;font-size:22px;">Score: ${score}/25</b>`;

                // 2. Update Glow/Grow
                content.innerHTML = `
                    <div style="background:#f0f9ff;padding:12px;border-left:4px solid #0078d4;margin-bottom:10px;border-radius:4px;font-size:13px;">
                        <b style="color:#0078d4;">Glow:</b> ${msg.data["Detailed Feedback"]?.Good}
                    </div>
                    <div style="background:#fff5f5;padding:12px;border-left:4px solid #e81123;margin-bottom:10px;border-radius:4px;font-size:13px;">
                        <b style="color:#e81123;">Grow:</b> ${msg.data["Detailed Feedback"]?.Improve}
                    </div>
                `;

                // 3. Build Details List
                let dHtml = "";
                const details = msg.data.Details || [];
                details.forEach(item => {
                    dHtml += `
                        <div style="font-size:12px; margin-bottom:15px; border-bottom:1px dashed #ddd; padding-bottom:10px;">
                            <div style="color:#d35400; font-weight:bold; margin-bottom:4px;">Line ${item["Line number which violates rubric item"]}: ${item["Which rubric item it violates"]}</div>
                            <div style="font-style:italic; color:#666; margin-bottom:5px; padding:5px; background:#f9f9f9; border-radius:3px;">"${item["Extract which violates rubric"]}"</div>
                            <div style="margin-bottom:4px;"><b>Reason:</b> ${item["Reason for violating rubric"]}</div>
                            <div style="color:#27ae60; font-weight:500;"><b>Try:</b> ${item["Improvement with example"]}</div>
                        </div>`;
                });
                
                detailsList.innerHTML = dHtml;

                // 4. Setup Toggle Button
                if (details.length > 0) {
                    toggleBtn.style.display = "block";
                    toggleBtn.innerText = "Show Details";
                    toggleBtn.onclick = () => {
                        const isHidden = detailsSection.style.display === "none";
                        detailsSection.style.display = isHidden ? "block" : "none";
                        toggleBtn.innerText = isHidden ? "Hide Details" : "Show Details";
                    };
                }
            }
        });
    };

    if (document.body) {
        injectSidebar();
    } else {
        const bodyObserver = new MutationObserver((mutations, obs) => {
            if (document.body) {
                injectSidebar();
                obs.disconnect();
            }
        });
        bodyObserver.observe(document.documentElement, { childList: true });
    }
}

// SENSOR LOGIC (SUB-FRAME)
if (!isTopFrame) {
    chrome.runtime.onMessage.addListener((msg) => {
        if (msg.action === "triggerScan") {
            const editor = document.querySelector('.WACViewPanel') || 
                           document.querySelector('.WACViewPanel_WordCore_EventLayer') || 
                           document.querySelector('.Paragraph') || 
                           document.querySelector('[role="textbox"]') ||
                           document.querySelector('[contenteditable="true"]');

            if (editor) {
                const currentText = editor.innerText || editor.textContent || "";
                chrome.runtime.sendMessage({ action: "analyze", text: currentText });
            }
        }
    });
}

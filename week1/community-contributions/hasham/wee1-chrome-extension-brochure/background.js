// background.js - Service worker for the Chrome extension

chrome.runtime.onInstalled.addListener(() => {
    console.log('Company Brochure Generator extension installed');
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'generateBrochure') {
        // Forward to backend server
        fetch('http://localhost:5000/generate-brochure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                company_name: request.companyName,
                url: request.url
            })
        })
        .then(response => response.json())
        .then(data => sendResponse({ success: true, data: data }))
        .catch(error => sendResponse({ success: false, error: error.message }));
        
        return true; // Keep the message channel open for async response
    }
});

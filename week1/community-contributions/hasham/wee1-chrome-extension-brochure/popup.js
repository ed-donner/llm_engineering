// popup.js - Handle user interactions in the extension popup

document.addEventListener('DOMContentLoaded', async function() {
    const form = document.getElementById('brochureForm');
    const generateBtn = document.getElementById('generateBtn');
    const statusDiv = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    const brochureContent = document.getElementById('brochureContent');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const companyNameInput = document.getElementById('companyName');
    const companyUrlInput = document.getElementById('companyUrl');
    const tabWarning = document.getElementById('tabWarning');

    let currentBrochureMarkdown = '';

    // Auto-fill form with current tab's URL on load
    await fillFromCurrentTab();

    async function fillFromCurrentTab() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            // Check if it's a valid URL (not chrome://, edge://, etc.)
            if (tab.url && (tab.url.startsWith('http://') || tab.url.startsWith('https://'))) {
                companyUrlInput.value = tab.url;
                
                // Try to extract company name from title
                if (tab.title) {
                    // Remove common suffixes and clean up
                    let cleanTitle = tab.title
                        .split('|')[0]
                        .split('-')[0]
                        .split('•')[0]
                        .split('—')[0]
                        .trim();
                    companyNameInput.value = cleanTitle;
                }
                
                // Enable the button
                generateBtn.disabled = false;
                tabWarning.classList.add('hidden');
            } else {
                // Disable if on invalid page
                generateBtn.disabled = true;
                tabWarning.classList.remove('hidden');
                showStatus('Please navigate to a website (http:// or https://) to use this extension', 'error');
            }
        } catch (error) {
            console.error('Error getting current tab info:', error);
            generateBtn.disabled = true;
            tabWarning.classList.remove('hidden');
        }
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const companyName = companyNameInput.value.trim();
        const companyUrl = companyUrlInput.value.trim();

        if (!companyName || !companyUrl) {
            showStatus('Please fill in all fields', 'error');
            return;
        }

        // Disable button and show loading status
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        resultDiv.classList.add('hidden');
        showStatus('Generating brochure... This may take 30-60 seconds.', 'loading');

        try {
            const response = await fetch('http://localhost:5000/generate-brochure', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: companyName,
                    url: companyUrl
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate brochure');
            }

            const data = await response.json();
            currentBrochureMarkdown = data.brochure;
            
            // Convert markdown to HTML for display
            brochureContent.innerHTML = markdownToHtml(currentBrochureMarkdown);
            
            resultDiv.classList.remove('hidden');
            showStatus('Brochure generated successfully!', 'success');
            
        } catch (error) {
            showStatus(`Error: ${error.message}. Make sure the backend server is running on localhost:5000`, 'error');
            console.error('Error:', error);
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Brochure';
        }
    });

    // Copy brochure to clipboard
    copyBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(currentBrochureMarkdown).then(() => {
            showStatus('Copied to clipboard!', 'success');
            copyBtn.textContent = '✓ Copied!';
            setTimeout(() => {
                copyBtn.textContent = '📋 Copy';
            }, 2000);
        }).catch(err => {
            showStatus('Failed to copy to clipboard', 'error');
        });
    });

    // Download brochure as markdown file
    downloadBtn.addEventListener('click', function() {
        const companyName = companyNameInput.value.trim().replace(/[^a-z0-9]/gi, '_').toLowerCase();
        const filename = `${companyName}_brochure.md`;
        
        const blob = new Blob([currentBrochureMarkdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showStatus('Brochure downloaded!', 'success');
    });

    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.classList.remove('hidden');
        
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    }

    // Simple markdown to HTML converter
    function markdownToHtml(markdown) {
        // Split into lines for better processing
        const lines = markdown.split('\n');
        let html = '';
        let inList = false;
        
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            
            // Skip empty lines
            if (!line) {
                if (inList) {
                    html += '</ul>';
                    inList = false;
                }
                html += '<br>';
                continue;
            }
            
            // Headers
            if (line.startsWith('### ')) {
                if (inList) { html += '</ul>'; inList = false; }
                html += '<h3>' + line.substring(4) + '</h3>';
            } else if (line.startsWith('## ')) {
                if (inList) { html += '</ul>'; inList = false; }
                html += '<h2>' + line.substring(3) + '</h2>';
            } else if (line.startsWith('# ')) {
                if (inList) { html += '</ul>'; inList = false; }
                html += '<h1>' + line.substring(2) + '</h1>';
            }
            // List items
            else if (line.startsWith('- ') || line.startsWith('* ')) {
                if (!inList) {
                    html += '<ul>';
                    inList = true;
                }
                html += '<li>' + formatInline(line.substring(2)) + '</li>';
            }
            // Regular paragraphs
            else {
                if (inList) {
                    html += '</ul>';
                    inList = false;
                }
                html += '<p>' + formatInline(line) + '</p>';
            }
        }
        
        // Close any open lists
        if (inList) {
            html += '</ul>';
        }
        
        return html;
    }
    
    // Format inline markdown (bold, italic, links)
    function formatInline(text) {
        // Bold
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Links
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        
        return text;
    }
});

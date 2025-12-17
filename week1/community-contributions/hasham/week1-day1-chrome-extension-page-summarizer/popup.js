document.getElementById('summarizeBtn').addEventListener('click', async () => {
  const apiKey = CONFIG.OPENAI_API_KEY;
  const summaryDiv = document.getElementById('summary');
  const loadingDiv = document.getElementById('loading');
  const button = document.getElementById('summarizeBtn');
  
  if (!apiKey || apiKey === 'your-api-key-here') {
    summaryDiv.style.display = 'block';
    summaryDiv.innerHTML = '<div class="error">Please configure your OpenAI API key in config.js</div>';
    return;
  }
  
  // Show loading state
  button.disabled = true;
  loadingDiv.style.display = 'block';
  summaryDiv.style.display = 'none';
  
  try {
    // Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Extract page content
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: extractPageContent
    });
    
    const pageContent = results[0].result;
    
    // Call OpenAI API
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content: 'You are a hilarious assistant that summarizes web pages humorously. Provide a clear, informative summary.'
          },
          {
            role: 'user',
            content: `Please summarize this webpage:\n\nTitle: ${pageContent.title}\n\nContent: ${pageContent.text}`
          }
        ],
        max_tokens: 300,
        temperature: 0.7
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'API request failed');
    }
    
    const data = await response.json();
    const summary = data.choices[0].message.content;
    
    // Display summary
    summaryDiv.style.display = 'block';
    summaryDiv.innerHTML = `<strong>Summary:</strong><br><br>${summary}`;
    
  } catch (error) {
    summaryDiv.style.display = 'block';
    summaryDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
  } finally {
    button.disabled = false;
    loadingDiv.style.display = 'none';
  }
});

// Function to extract page content (runs in page context)
function extractPageContent() {
  const title = document.title;
  
  // Get main text content, excluding scripts and styles
  const clone = document.body.cloneNode(true);
  const scripts = clone.querySelectorAll('script, style, nav, footer, header');
  scripts.forEach(el => el.remove());
  
  let text = clone.innerText || clone.textContent;
  
  // Clean up and limit text length
  text = text.replace(/\s+/g, ' ').trim();
  text = text.substring(0, 4000); // Limit to avoid token limits
  
  return { title, text };
}
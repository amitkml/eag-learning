document.addEventListener('DOMContentLoaded', function() {
  const summarizeButton = document.getElementById('summarize');
  const loadingElement = document.getElementById('loading');
  const summaryContainer = document.getElementById('summary-container');
  const summaryText = document.getElementById('summary-text');
  const errorContainer = document.getElementById('error-container');
  const errorMessage = document.getElementById('error-message');

  summarizeButton.addEventListener('click', async () => {
    // Reset UI
    summaryContainer.classList.add('hidden');
    errorContainer.classList.add('hidden');
    loadingElement.classList.remove('hidden');
    
    try {
      // Get the current active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Execute content script to extract text from the page
      const result = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: extractPageContent
      });
      
      const pageContent = result[0].result;
      
      if (!pageContent || pageContent.trim() === '') {
        throw new Error('Could not extract content from this page.');
      }
      
      // Generate summary using an API
      const summary = await generateSummary(pageContent);
      
      // Display the summary
      summaryText.textContent = summary;
      summaryContainer.classList.remove('hidden');
    } catch (error) {
      errorMessage.textContent = `Error: ${error.message}`;
      errorContainer.classList.remove('hidden');
    } finally {
      loadingElement.classList.add('hidden');
    }
  });
  
  // Function to generate a summary using an API
  async function generateSummary(content) {
    try {
      // Get the API key from storage
      const storageData = await chrome.storage.sync.get('openaiApiKey');
      const apiKey = storageData.openaiApiKey;
      
      if (!apiKey) {
        return "Please set your OpenAI API key in the extension options.";
      }
      
      // Prepare content for summarization (truncate if too long)
      const maxInputLength = 4000;
      const truncatedContent = content.length > maxInputLength 
        ? content.substring(0, maxInputLength) + '...'
        : content;
      
      // Make API call to OpenAI
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: "gpt-3.5-turbo",
          messages: [
            {
              role: "system",
              content: "You are a helpful assistant that summarizes web content concisely."
            },
            {
              role: "user",
              content: `Please provide a concise summary of the following web page content in 3-5 sentences:\n\n${truncatedContent}`
            }
          ],
          max_tokens: 150,
          temperature: 0.5
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`API error: ${errorData.error?.message || 'Unknown error'}`);
      }
      
      const data = await response.json();
      return data.choices[0].message.content.trim();
    } catch (error) {
      console.error('Summary generation error:', error);
      return `Error generating summary: ${error.message}. Please try again later.`;
    }
  }
});

// This function runs in the context of the web page
function extractPageContent() {
  // Function to check if an element is visible
  function isVisible(element) {
    return !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length);
  }
  
  // Function to get the main content of the page
  function getMainContent() {
    // Try to find the main content using common selectors
    const contentSelectors = [
      'article', 'main', '.content', '#content', '.post', '.article', '.post-content',
      '[role="main"]', '.main-content', '#main-content'
    ];
    
    for (const selector of contentSelectors) {
      const elements = document.querySelectorAll(selector);
      for (const element of elements) {
        if (isVisible(element) && element.textContent.length > 200) {
          return element.textContent;
        }
      }
    }
    
    // If no main content found, get all paragraphs
    const paragraphs = Array.from(document.querySelectorAll('p'))
      .filter(p => isVisible(p) && p.textContent.trim().length > 50);
    
    if (paragraphs.length > 0) {
      return paragraphs.map(p => p.textContent).join('\n\n');
    }
    
    // Fallback to body text
    return document.body.textContent;
  }
  
  // Get the page content
  let content = getMainContent();
  
  // Clean up the content
  content = content
    .replace(/\s+/g, ' ')  // Replace multiple spaces with a single space
    .replace(/\n+/g, '\n') // Replace multiple newlines with a single newline
    .trim();
  
  return content;
} 
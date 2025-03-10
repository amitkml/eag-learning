// This file is not strictly necessary as we're using executeScript in popup.js,
// but it's included here for completeness in case you want to modify the extension
// to use a content script approach instead.

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractContent') {
    const content = extractPageContent();
    sendResponse({ content });
  }
  return true; // Required for async response
});

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
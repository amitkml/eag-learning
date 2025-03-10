// This function runs in the context of the web page
function extractPageContent() {
  // Function to check if an element is visible
  function isVisible(element) {
    return !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length);
  }
  
  // Function to calculate text-to-HTML ratio for an element
  function getTextToHtmlRatio(element) {
    const text = element.textContent.trim();
    const html = element.innerHTML.trim();
    return html.length > 0 ? text.length / html.length : 0;
  }
  
  // Detect if we're on a homepage or article list page
  function isHomePage() {
    // Check URL patterns that typically indicate homepages
    const url = window.location.href;
    if (url.endsWith('/') || url.endsWith('.com') || url.endsWith('.org') || url.endsWith('.net')) {
      return true;
    }
    
    // Check for multiple article headlines/links
    const articleLinks = document.querySelectorAll('a h2, h2 a, h3 a, a h3, .headline a, a .headline');
    if (articleLinks.length > 5) {
      return true;
    }
    
    return false;
  }
  
  // If we're on a homepage, try to find the most prominent article
  if (isHomePage()) {
    console.log('Detected homepage or article listing page');
    
    // Try to find the main/featured article
    const featuredArticleSelectors = [
      '.featured-article', '.main-article', '.top-story', '.lead-story',
      '.headline-story', '.primary-article', '[data-featured="true"]'
    ];
    
    for (const selector of featuredArticleSelectors) {
      const featuredElement = document.querySelector(selector);
      if (featuredElement && isVisible(featuredElement)) {
        // Try to extract the article title and link
        const titleElement = featuredElement.querySelector('h1, h2, .title, .headline');
        const linkElement = featuredElement.querySelector('a');
        
        if (titleElement && linkElement) {
          return {
            type: 'homepage',
            title: titleElement.textContent.trim(),
            link: linkElement.href,
            description: 'This appears to be a homepage or article listing page. The featured article is: ' + 
                        titleElement.textContent.trim()
          };
        }
      }
    }
    
    return {
      type: 'homepage',
      description: 'This appears to be a homepage or article listing page with multiple articles. Please navigate to a specific article to get a summary.'
    };
  }
  
  // Function to get the main content of the page
  function getMainContent() {
    // First, try to remove common non-content elements
    const nonContentSelectors = [
      'header', 'footer', 'nav', '.navigation', '.menu', '.sidebar', '.comments', 
      '.related-articles', '.recommended', '.social-share', '.advertisement',
      '.nav', '#header', '#footer', '#nav', '.header', '.footer'
    ];
    
    // Create a clone of the body to work with
    const bodyClone = document.body.cloneNode(true);
    
    // Remove non-content elements from the clone
    for (const selector of nonContentSelectors) {
      const elements = bodyClone.querySelectorAll(selector);
      for (const element of elements) {
        if (element.parentNode) {
          element.parentNode.removeChild(element);
        }
      }
    }
    
    // First, try to find the article headline/title
    const titleSelectors = [
      'h1.article-title', 'h1.entry-title', 'h1.headline', 'h1.title', 
      '.article-headline', '.article-title', '.story-title', '.entry-title',
      '[itemprop="headline"]'
    ];
    
    let articleTitle = '';
    for (const selector of titleSelectors) {
      const titleElement = bodyClone.querySelector(selector);
      if (titleElement && isVisible(titleElement)) {
        articleTitle = titleElement.textContent.trim();
        break;
      }
    }
    
    console.log('Found article title:', articleTitle || 'None detected');
    
    // Try to find the main content using common article selectors
    const contentSelectors = [
      // Common article content selectors
      'article', '.article-body', '.story-content', '.entry-content', '.post-content',
      '[itemprop="articleBody"]', '.story__content', '.article__content', '.content-body',
      // News site specific selectors
      '.story-article', '.article-text', '.news-content', '.main-content', '#articleBody',
      '.story-body__inner', '.article-container', '.article__body', '.story-body',
      // Times of India specific selectors
      '.Normal', '.article_content', '#content-body', '.main-content', '.article-txt'
    ];
    
    // First try to find article elements with substantial content
    let bestElement = null;
    let bestScore = 0;
    
    for (const selector of contentSelectors) {
      const elements = bodyClone.querySelectorAll(selector);
      for (const element of elements) {
        if (isVisible(element) && element.textContent.trim().length > 200) {
          // Calculate a score based on text length and text-to-HTML ratio
          const textLength = element.textContent.trim().length;
          const ratio = getTextToHtmlRatio(element);
          const score = textLength * ratio;
          
          // If this element contains the title, boost its score
          if (articleTitle && element.textContent.includes(articleTitle)) {
            score *= 1.5;
          }
          
          if (score > bestScore) {
            bestScore = score;
            bestElement = element;
          }
        }
      }
    }
    
    if (bestElement) {
      console.log('Found main content using selector');
      return bestElement.textContent;
    }
    
    // If no main content found with selectors, look for clusters of paragraphs
    const paragraphs = Array.from(bodyClone.querySelectorAll('p'))
      .filter(p => isVisible(p) && p.textContent.trim().length > 40);
    
    if (paragraphs.length > 3) {
      console.log('Using paragraph cluster method');
      return paragraphs.map(p => p.textContent).join('\n\n');
    }
    
    // Try to find the longest text block with a good text-to-HTML ratio
    let bestTextBlock = '';
    let bestBlockScore = 0;
    
    const textElements = bodyClone.querySelectorAll('div, section, main');
    for (const element of textElements) {
      if (isVisible(element) && element.children.length > 2) {
        const text = element.textContent.trim();
        if (text.length > 500) {
          const ratio = getTextToHtmlRatio(element);
          const score = text.length * ratio;
          
          if (score > bestBlockScore) {
            bestBlockScore = score;
            bestTextBlock = text;
          }
        }
      }
    }
    
    if (bestTextBlock) {
      console.log('Using best text block method');
      return bestTextBlock;
    }
    
    // Absolute fallback to body text
    console.log('Falling back to body text');
    return bodyClone.textContent;
  }
  
  // Get the page content
  let content = getMainContent();
  
  // Clean up the content
  content = content
    .replace(/\s+/g, ' ')  // Replace multiple spaces with a single space
    .replace(/\n+/g, '\n') // Replace multiple newlines with a single newline
    .replace(/\t+/g, ' ')  // Replace tabs with spaces
    .replace(/\r+/g, '')   // Remove carriage returns
    .replace(/Advertisement/gi, '') // Remove advertisement markers
    .trim();
  
  // Add debugging info
  console.log('Extracted content length:', content.length);
  console.log('Content preview:', content.substring(0, 300) + '...');
  
  // Return the extracted content with metadata
  return {
    type: 'article',
    title: articleTitle || 'Unknown Article',
    content: content
  };
}

async function generateSummary(contentData) {
  try {
    // Handle homepage or listing pages
    if (contentData.type === 'homepage') {
      return contentData.description;
    }
    
    // Get the API key from storage
    const storageData = await chrome.storage.sync.get('openaiApiKey');
    const apiKey = storageData.openaiApiKey;
    
    if (!apiKey) {
      return "Please set your OpenAI API key in the extension options.";
    }
    
    // Prepare content for summarization (truncate if too long)
    const content = contentData.content;
    const maxInputLength = 4000;
    const truncatedContent = content.length > maxInputLength 
      ? content.substring(0, maxInputLength) + '...'
      : content;
    
    // Make API call to OpenAI with a more specific prompt
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
            content: "You are a helpful assistant that summarizes specific article content. Focus only on the main article content, not general website descriptions or navigation elements."
          },
          {
            role: "user",
            content: `Please provide a concise summary of the main article from the following web page content. The article title is: "${contentData.title}". Focus ONLY on the specific article content, NOT on general descriptions of the website, publication, or news desk. If you can't identify a specific article, state that clearly. Summary should be 3-5 sentences:\n\n${truncatedContent}`
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
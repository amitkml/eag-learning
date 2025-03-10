document.addEventListener('DOMContentLoaded', function() {
  // Load saved API key
  chrome.storage.sync.get('openaiApiKey', function(data) {
    if (data.openaiApiKey) {
      document.getElementById('apiKey').value = data.openaiApiKey;
    }
  });
  
  // Save API key
  document.getElementById('save').addEventListener('click', function() {
    const apiKey = document.getElementById('apiKey').value.trim();
    
    if (!apiKey) {
      showStatus('Please enter a valid API key', 'error');
      return;
    }
    
    chrome.storage.sync.set({ 'openaiApiKey': apiKey }, function() {
      showStatus('API key saved successfully!', 'success');
    });
  });
  
  function showStatus(message, type) {
    const statusElement = document.getElementById('status');
    statusElement.textContent = message;
    statusElement.className = 'status ' + type;
    statusElement.style.display = 'block';
    
    setTimeout(function() {
      statusElement.style.display = 'none';
    }, 3000);
  }
}); 
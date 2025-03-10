// This is a helper script to create basic icons
// You can run this in a browser console or Node.js environment

// Function to create a simple canvas icon
function createIcon(size, color = '#4285f4') {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  
  // Draw background
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, size, size);
  
  // Draw 'S' for Summarizer
  ctx.fillStyle = 'white';
  ctx.font = `bold ${Math.floor(size * 0.7)}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('S', size/2, size/2);
  
  return canvas.toDataURL('image/png');
}

// Create icons of different sizes
const icon16 = createIcon(16);
const icon48 = createIcon(48);
const icon128 = createIcon(128);

console.log('Icon 16x16:', icon16);
console.log('Icon 48x48:', icon48);
console.log('Icon 128x128:', icon128); 
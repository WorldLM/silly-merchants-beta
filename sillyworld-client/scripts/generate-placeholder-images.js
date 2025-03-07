const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');

// Create directory if it doesn't exist
const imagesDir = path.join(__dirname, '../public/images');
if (!fs.existsSync(imagesDir)) {
  fs.mkdirSync(imagesDir, { recursive: true });
}

// Generate Alex avatar
const alexCanvas = createCanvas(200, 200);
const alexCtx = alexCanvas.getContext('2d');

// Background
alexCtx.fillStyle = '#3498db';
alexCtx.fillRect(0, 0, 200, 200);

// Text
alexCtx.fillStyle = '#ffffff';
alexCtx.font = 'bold 60px Arial';
alexCtx.textAlign = 'center';
alexCtx.textBaseline = 'middle';
alexCtx.fillText('Alex', 100, 100);

const alexBuffer = alexCanvas.toBuffer('image/png');
fs.writeFileSync(path.join(imagesDir, 'alex-avatar.png'), alexBuffer);

// Generate judge avatars
const judgeColors = ['#e74c3c', '#9b59b6', '#2ecc71'];
const judgeNames = ['Judge 1', 'Judge 2', 'Judge 3'];

for (let i = 0; i < 3; i++) {
  const judgeCanvas = createCanvas(200, 200);
  const judgeCtx = judgeCanvas.getContext('2d');
  
  // Background
  judgeCtx.fillStyle = judgeColors[i];
  judgeCtx.fillRect(0, 0, 200, 200);
  
  // Text
  judgeCtx.fillStyle = '#ffffff';
  judgeCtx.font = 'bold 40px Arial';
  judgeCtx.textAlign = 'center';
  judgeCtx.textBaseline = 'middle';
  judgeCtx.fillText(judgeNames[i], 100, 100);
  
  const judgeBuffer = judgeCanvas.toBuffer('image/png');
  fs.writeFileSync(path.join(imagesDir, `judge-${i + 1}.png`), judgeBuffer);
}

console.log('Placeholder images generated successfully!'); 
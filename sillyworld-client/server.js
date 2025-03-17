const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

const PORT = process.env.PORT || 3000;

// Check if audio files need to be generated
const audioDir = path.join(__dirname, 'public/audio');
const needsAudioGeneration = !fs.existsSync(audioDir) || fs.readdirSync(audioDir).length === 0;

app.prepare().then(() => {
  // Generate audio files if needed
  if (needsAudioGeneration) {
    console.log('Generating audio files...');
    
    // Create directories if they don't exist
    if (!fs.existsSync(path.join(__dirname, 'public'))) {
      fs.mkdirSync(path.join(__dirname, 'public'));
    }
    
    if (!fs.existsSync(audioDir)) {
      fs.mkdirSync(audioDir);
    }
    
    // Generate placeholder audio
    exec('node scripts/generate-voice-content.js && node scripts/generate-placeholder-audio.js', (error, stdout, stderr) => {
      if (error) {
        console.error(`Error generating audio: ${error.message}`);
        return;
      }
      if (stderr) {
        console.error(`Audio generation stderr: ${stderr}`);
      }
      console.log(`Audio generation stdout: ${stdout}`);
    });
  }

  createServer((req, res) => {
    const parsedUrl = parse(req.url, true);
    handle(req, res, parsedUrl);
  }).listen(PORT, (err) => {
    if (err) throw err;
    console.log(`> Ready on http://localhost:${PORT}`);
  });
}); 
/**
 * Script to generate placeholder audio files for the Idea Pitching POC
 * 
 * This script creates MP3 files with speech-like sounds to simulate
 * voice recordings used in the application.
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execPromise = promisify(exec);

// Create directory if it doesn't exist
const audioDir = path.join(__dirname, '../public/audio');
if (!fs.existsSync(audioDir)) {
  fs.mkdirSync(audioDir, { recursive: true });
}

// Voice content directory
const contentDir = path.join(__dirname, '../public/voice-content');

// Check if FFmpeg is installed
async function checkFFmpeg() {
  try {
    await execPromise('ffmpeg -version');
    console.log('FFmpeg is installed and working.');
    return true;
  } catch (error) {
    console.error('FFmpeg is not installed or not in PATH. Please install FFmpeg to continue.');
    console.error('Installation instructions: https://ffmpeg.org/download.html');
    return false;
  }
}

// Generate a simple tone audio file (more reliable than complex filters)
async function generateSimpleAudio(filename, duration, voice) {
  try {
    // Use a simpler command that's more likely to work across different ffmpeg versions
    const frequency = voice === 'male' ? 120 : 220;
    const command = `ffmpeg -f lavfi -i "sine=frequency=${frequency}:duration=${duration}" -ar 44100 -ac 1 -b:a 192k "${filename}"`;
    
    console.log(`Executing: ${command}`);
    const { stdout, stderr } = await execPromise(command);
    
    if (stderr && !stderr.includes('Output #0')) {
      console.warn(`Warning for ${filename}: ${stderr}`);
    }
    
    return true;
  } catch (error) {
    console.error(`Error generating ${filename}:`, error.message);
    return false;
  }
}

// Main function to generate all audio files
async function generateAllAudioFiles() {
  console.log('Checking FFmpeg installation...');
  const ffmpegInstalled = await checkFFmpeg();
  if (!ffmpegInstalled) {
    return;
  }
  
  console.log('Generating placeholder audio files...');
  
  // First, check if voice content files exist
  if (!fs.existsSync(contentDir)) {
    console.log('Voice content directory not found. Please run generate-voice-content.js first.');
    return;
  }
  
  const contentFiles = fs.readdirSync(contentDir);
  if (contentFiles.length === 0) {
    console.log('No voice content files found. Please run generate-voice-content.js first.');
    return;
  }
  
  console.log(`Found ${contentFiles.length} voice content files.`);
  
  // Generate audio for each content file
  let successCount = 0;
  let failCount = 0;
  
  for (const contentFile of contentFiles) {
    if (!contentFile.endsWith('.txt')) continue;
    
    const baseName = path.basename(contentFile, '.txt');
    const outputFile = path.join(audioDir, `${baseName}.mp3`);
    
    // Read content to determine duration
    const content = fs.readFileSync(path.join(contentDir, contentFile), 'utf8');
    const words = content.split(' ').length;
    const duration = Math.max(3, Math.ceil(words * 0.4)); // 0.4 seconds per word
    
    // Determine voice type
    const voice = baseName.startsWith('judge_1_') || 
                 baseName.startsWith('judge_3_') || 
                 baseName.startsWith('system_') ? 'female' : 'male';
    
    console.log(`Generating ${outputFile} (${duration}s, ${voice} voice)...`);
    
    const success = await generateSimpleAudio(outputFile, duration, voice);
    if (success) {
      successCount++;
    } else {
      failCount++;
    }
  }
  
  console.log(`Audio generation complete: ${successCount} succeeded, ${failCount} failed.`);
}

// Run the main function
generateAllAudioFiles().catch(error => {
  console.error('Unhandled error:', error);
}); 
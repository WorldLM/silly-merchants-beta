/**
 * Script to generate realistic voice audio files using OpenAI's Text-to-Speech API
 * for the Idea Pitching POC
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { promisify } = require('util');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env.local') });

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
if (!OPENAI_API_KEY) {
  console.error('Error: OPENAI_API_KEY is not set in .env.local file');
  console.error('Please add your OpenAI API key to the .env.local file:');
  console.error('OPENAI_API_KEY=your_api_key_here');
  process.exit(1);
}

// Create directories if they don't exist
const audioDir = path.join(__dirname, '../public/audio');
if (!fs.existsSync(audioDir)) {
  fs.mkdirSync(audioDir, { recursive: true });
}

// Voice content directory
const contentDir = path.join(__dirname, '../public/voice-content');

// Voice mapping for different characters
const voiceMapping = {
  // Male voices
  male: {
    default: 'onyx', // Default male voice
    alex: 'echo',    // Alex (AI co-founder)
    judge2: 'fable'  // Judge 2 (male judge)
  },
  // Female voices
  female: {
    default: 'nova', // Default female voice
    judge1: 'shimmer', // Judge 1 (female judge)
    judge3: 'alloy'    // Judge 3 (female judge)
  }
};

// Function to determine which voice to use based on the filename
function getVoiceForFile(filename) {
  if (filename.startsWith('alex_')) {
    return voiceMapping.male.alex;
  } else if (filename.startsWith('judge_1_')) {
    return voiceMapping.female.judge1;
  } else if (filename.startsWith('judge_2_')) {
    return voiceMapping.male.judge2;
  } else if (filename.startsWith('judge_3_')) {
    return voiceMapping.female.judge3;
  } else if (filename.startsWith('system_')) {
    return voiceMapping.female.default;
  } else if (filename.startsWith('pitch_')) {
    return voiceMapping.male.alex;
  } else {
    // Default to male voice for anything else
    return voiceMapping.male.default;
  }
}

// Function to generate audio using OpenAI's TTS API
async function generateAudioWithOpenAI(text, outputFile, voice) {
  try {
    console.log(`Generating audio for: "${text.substring(0, 50)}..." with voice ${voice}`);
    
    const response = await axios({
      method: 'post',
      url: 'https://api.openai.com/v1/audio/speech',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      data: {
        model: 'tts-1',
        input: text,
        voice: voice,
        response_format: 'mp3'
      },
      responseType: 'arraybuffer'
    });
    
    fs.writeFileSync(outputFile, response.data);
    console.log(`Successfully generated ${outputFile}`);
    return true;
  } catch (error) {
    console.error(`Error generating audio for ${outputFile}:`, error.response?.data ? JSON.parse(Buffer.from(error.response.data).toString()) : error.message);
    return false;
  }
}

// Main function to generate all audio files
async function generateAllAudioFiles() {
  console.log('Generating audio files using OpenAI TTS API...');
  
  // Check if voice content files exist
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
  
  // Process files in batches to avoid rate limiting
  const batchSize = 5;
  const batches = Math.ceil(contentFiles.length / batchSize);
  
  for (let i = 0; i < batches; i++) {
    const batchStart = i * batchSize;
    const batchEnd = Math.min((i + 1) * batchSize, contentFiles.length);
    const batch = contentFiles.slice(batchStart, batchEnd);
    
    console.log(`Processing batch ${i + 1}/${batches} (files ${batchStart + 1}-${batchEnd})...`);
    
    const batchPromises = batch.map(async (contentFile) => {
      if (!contentFile.endsWith('.txt')) return null;
      
      const baseName = path.basename(contentFile, '.txt');
      const outputFile = path.join(audioDir, `${baseName}.mp3`);
      
      // Read content
      const content = fs.readFileSync(path.join(contentDir, contentFile), 'utf8');
      
      // Determine voice
      const voice = getVoiceForFile(baseName);
      
      // Generate audio
      const success = await generateAudioWithOpenAI(content, outputFile, voice);
      
      if (success) {
        successCount++;
        return true;
      } else {
        failCount++;
        return false;
      }
    });
    
    await Promise.all(batchPromises);
    
    // Add a delay between batches to avoid rate limiting
    if (i < batches - 1) {
      console.log('Waiting 2 seconds before processing next batch...');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  console.log(`Audio generation complete: ${successCount} succeeded, ${failCount} failed.`);
}

// Run the main function
generateAllAudioFiles().catch(error => {
  console.error('Unhandled error:', error);
}); 
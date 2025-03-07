import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { text, voice, judgeIndex } = await request.json();
    
    if (!text) {
      return NextResponse.json(
        { error: 'No text provided' },
        { status: 400 }
      );
    }
    
    // Map voice type to OpenAI voice
    let voiceId = 'alloy'; // default voice
    
    switch(voice) {
      case 'alex':
        voiceId = 'onyx'; // professional, clear voice
        break;
      case 'judge':
        // Use different voices for different judges
        if (judgeIndex === 1) {
          voiceId = 'nova'; // female voice for second judge
        } else if (judgeIndex === 2) {
          voiceId = 'fable'; // different male voice for third judge
        } else {
          voiceId = 'echo'; // default male voice for first judge
        }
        break;
      case 'echo':
        voiceId = 'echo'; // versatile voice
        break;
      case 'system':
        voiceId = 'shimmer'; // enthusiastic voice
        break;
    }
    
    // Call OpenAI TTS API with enhanced settings
    const mp3 = await openai.audio.speech.create({
      model: 'tts-1-hd', // Use HD model for better quality
      voice: voiceId,
      input: text,
      speed: voice === 'system' ? 1.0 : 1.1, // Slightly faster for more energy
      response_format: 'mp3',
    });
    
    // Convert to ArrayBuffer
    const buffer = Buffer.from(await mp3.arrayBuffer());
    
    // Return audio as response
    return new NextResponse(buffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': buffer.length.toString(),
      },
    });
  } catch (error) {
    console.error('Error generating speech:', error);
    return NextResponse.json(
      { error: 'Failed to generate speech' },
      { status: 500 }
    );
  }
} 
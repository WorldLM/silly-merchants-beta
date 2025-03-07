import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    // In a real application, we would send the audio to a transcription service
    // For the POC, we'll just return a mock response
    
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Return a mock transcription
    return NextResponse.json({
      text: "This is a mock transcription. In a real application, we would process the audio file and return the actual transcription."
    });
  } catch (error) {
    console.error('Error in transcription:', error);
    return NextResponse.json(
      { error: 'Failed to transcribe audio' },
      { status: 500 }
    );
  }
} 
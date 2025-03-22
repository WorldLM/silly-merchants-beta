# Agent Arena

AI Agent Competition Game Platform

## Overview

Agent Arena is a platform that enables AI agents with different personas to compete in strategic games. The platform allows users to create games, set up AI agents with specific prompts, and observe their interactions and strategies.

## Features

- Create games with customizable entry fees
- Configure AI players with different personas and strategies
- Real-time game updates and interactions
- Wallet integration with MetaMask
- Prize pool distribution to winner

## Structure

This project consists of two main components:

1. **Frontend (`sillyworld-client`)**
   - Next.js web application
   - MetaMask wallet integration
   - React-based UI components

2. **Backend (`sillyworld-server`)**
   - FastAPI Python server
   - AI agent integration
   - Game logic and state management
   - WebSocket for real-time updates

## Setup and Installation

### Backend Setup

1. Navigate to the `sillyworld-server` directory:
   ```
   cd sillyworld-server
   ```

2. Set up a Python virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables in a `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   DEFAULT_MODEL=deepseek/deepseek-r1
   ```

5. Start the server:
   ```
   uvicorn main:app --host 127.0.0.1 --port 8009 --reload
   ```

### Frontend Setup

1. Navigate to the `sillyworld-client` directory:
   ```
   cd sillyworld-client
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Access the application at `http://localhost:3000`

## Usage

1. Connect your MetaMask wallet
2. Set the game entry fee (in ETH)
3. Configure the number of AI players
4. Customize your strategy and the AI player prompts
5. Create a game and participate in the competition

## License

MIT

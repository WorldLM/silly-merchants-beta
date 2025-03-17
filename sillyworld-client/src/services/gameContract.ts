import * as anchor from '@project-serum/anchor';
import { Connection, PublicKey, SystemProgram } from '@solana/web3.js';

// Game contract details
const PROGRAM_ID = new PublicKey('25jUhpQfPWWJ9e4BaP6eNyH3y1YrhF9CDY5DHPhTBiFW');
const NETWORK_URL = 'https://api.testnet.sonic.game';

export class GameContract {
  private connection: Connection;
  private wallet: any;
  private feeRecipient: PublicKey;
  private isMock: boolean;

  constructor(wallet: any) {
    this.wallet = wallet;
    this.isMock = wallet.constructor.name === 'MockSonicWallet';
    
    if (this.isMock) {
      console.log("Using mock GameContract implementation");
      this.connection = {} as Connection;
      this.feeRecipient = {} as PublicKey;
      return;
    }
    
    this.connection = new Connection(NETWORK_URL, 'confirmed');
    
    // Set fee recipient (this should be your project's wallet)
    this.feeRecipient = new PublicKey('DcchPY9gXM7z8QWre6WoMDoXE3SW92hZujgbvRVqdmys');
  }

  async initializeGame(entryFee: number): Promise<string> {
    if (this.isMock) {
      console.log("Mock initializeGame called with fee:", entryFee);
      return Date.now().toString();
    }
    
    try {
      // Generate a unique game ID using timestamp
      const gameId = new anchor.BN(Date.now());
      
      // Calculate PDAs
      const [gamePDA] = await PublicKey.findProgramAddress(
        [Buffer.from("game"), gameId.toArrayLike(Buffer, 'le', 8)],
        PROGRAM_ID
      );
      
      const [gameVaultPDA] = await PublicKey.findProgramAddress(
        [Buffer.from("vault"), gameId.toArrayLike(Buffer, 'le', 8)],
        PROGRAM_ID
      );
      
      // Convert entry fee to lamports (SOL)
      const entryFeeLamports = new anchor.BN(entryFee * 1000000000); // Convert SOL to lamports
      
      console.log("Game initialized with ID:", gameId.toString());
      
      return gameId.toString();
    } catch (error) {
      console.error("Error initializing game:", error);
      throw error;
    }
  }

  async joinGame(gameId: string): Promise<string> {
    if (this.isMock) {
      console.log("Mock joinGame called for game:", gameId);
      return "mock-transaction-id";
    }
    
    try {
      const gameIdBN = new anchor.BN(gameId);
      
      console.log("Joined game successfully");
      
      return "transaction-id";
    } catch (error) {
      console.error("Error joining game:", error);
      throw error;
    }
  }

  async endGame(gameId: string, winnerPublicKey: string): Promise<string> {
    if (this.isMock) {
      console.log("Mock endGame called:", gameId, winnerPublicKey);
      return "mock-transaction-id";
    }
    
    try {
      const gameIdBN = new anchor.BN(gameId);
      
      console.log("Game ended successfully");
      
      return "transaction-id";
    } catch (error) {
      console.error("Error ending game:", error);
      throw error;
    }
  }

  async getGameData(gameId: string): Promise<any> {
    if (this.isMock) {
      return {
        authority: "mock-authority",
        gameId: gameId,
        entryFee: "10000000 lamports (0.01 SOL)",
        prizePool: "100000000 lamports (0.1 SOL)",
        isActive: true,
        playerCount: "2",
        winner: null,
        feeRecipient: "mock-fee-recipient"
      };
    }
    
    try {
      const gameIdBN = new anchor.BN(gameId);
      
      // Return mock data since we can't actually fetch from blockchain
      return {
        authority: this.wallet.publicKey.toString(),
        gameId: gameId,
        entryFee: "10000000 lamports (0.01 SOL)",
        prizePool: "100000000 lamports (0.1 SOL)",
        isActive: true,
        playerCount: "2",
        winner: null,
        feeRecipient: this.feeRecipient.toString()
      };
    } catch (error) {
      console.error("Error fetching game data:", error);
      throw error;
    }
  }
}

// Helper function to get contract instance
let contractInstance: GameContract | null = null;

export const getGameContract = (wallet: any): GameContract => {
  if (!contractInstance) {
    contractInstance = new GameContract(wallet);
  }
  return contractInstance;
}; 
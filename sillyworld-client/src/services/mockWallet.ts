// Mock implementation of Sonic Wallet for development
class MockSonicWallet {
  private connected: boolean = false;
  private mockPublicKey: string = "SonicWa11etMockPub1icKeyXXXXXXXXXXXXXXXXXXX";

  constructor() {
    console.log("Mock Sonic Wallet initialized");
  }

  async connect(): Promise<void> {
    console.log("Mock wallet: Connecting...");
    this.connected = true;
    console.log("Mock wallet: Connected successfully");
    return Promise.resolve();
  }

  async disconnect(): Promise<void> {
    console.log("Mock wallet: Disconnecting...");
    this.connected = false;
    console.log("Mock wallet: Disconnected successfully");
    return Promise.resolve();
  }

  async isConnected(): Promise<boolean> {
    return Promise.resolve(this.connected);
  }

  async getPublicKey(): Promise<string> {
    if (!this.connected) {
      return Promise.reject(new Error("Wallet not connected"));
    }
    return Promise.resolve(this.mockPublicKey);
  }

  async signTransaction(transaction: any): Promise<any> {
    if (!this.connected) {
      return Promise.reject(new Error("Wallet not connected"));
    }
    console.log("Mock wallet: Signing transaction", transaction);
    return Promise.resolve({ ...transaction, signature: "mock_signature" });
  }

  async signAllTransactions(transactions: any[]): Promise<any[]> {
    if (!this.connected) {
      return Promise.reject(new Error("Wallet not connected"));
    }
    console.log("Mock wallet: Signing all transactions", transactions);
    return Promise.resolve(
      transactions.map(tx => ({ ...tx, signature: "mock_signature" }))
    );
  }
}

// Create a function to initialize the mock wallet
function initializeMockWallet() {
  try {
    console.log("Initializing mock wallet...");
    
    // Check if wallet already exists
    if (typeof window !== 'undefined' && 'sonicWallet' in window) {
      console.log("Wallet already exists in window object, not replacing");
      return;
    }
    
    // Add the mock wallet to the window object
    if (typeof window !== 'undefined') {
      console.log("Adding mock wallet to window object");
      (window as any).sonicWallet = new MockSonicWallet();
      console.log("Mock wallet added to window object");
    } else {
      console.error("Window object not available");
    }
  } catch (error) {
    console.error("Error initializing mock wallet:", error);
  }
}

// Initialize the mock wallet
initializeMockWallet();

export default MockSonicWallet; 
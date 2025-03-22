// Mock implementation of MetaMask wallet for development
class MockMetamask {
  private connected: boolean = false;
  public mockEthAddress: string = "0x001"; // Simulated ETH address

  constructor() {
    console.log("Mock MetaMask wallet initialized");
  }

  async connect(): Promise<void> {
    console.log("Mock MetaMask: Connecting...");
    this.connected = true;
    console.log("Mock MetaMask: Connected successfully");
    return Promise.resolve();
  }

  async disconnect(): Promise<void> {
    console.log("Mock MetaMask: Disconnecting...");
    this.connected = false;
    console.log("Mock MetaMask: Disconnected successfully");
    return Promise.resolve();
  }

  async isConnected(): Promise<boolean> {
    return Promise.resolve(this.connected);
  }

  async getAddress(): Promise<string> {
    if (!this.connected) {
      return Promise.reject(new Error("Wallet not connected"));
    }
    return Promise.resolve(this.mockEthAddress);
  }

  // Renamed from getPublicKey to getAddress to match MetaMask terminology
  async getPublicKey(): Promise<string> {
    return this.getAddress();
  }

  async signTransaction(transaction: any): Promise<any> {
    if (!this.connected) {
      return Promise.reject(new Error("Wallet not connected"));
    }
    console.log("Mock MetaMask: Signing transaction", transaction);
    return Promise.resolve({ ...transaction, signature: "mock_eth_signature" });
  }

  async signAllTransactions(transactions: any[]): Promise<any[]> {
    if (!this.connected) {
      return Promise.reject(new Error("Wallet not connected"));
    }
    console.log("Mock MetaMask: Signing all transactions", transactions);
    return Promise.resolve(
      transactions.map(tx => ({ ...tx, signature: "mock_eth_signature" }))
    );
  }

  // Add eth_signMessage for compatibility with MetaMask
  async signMessage(message: string): Promise<string> {
    if (!this.connected) {
      return Promise.reject(new Error("Wallet not connected"));
    }
    console.log("Mock MetaMask: Signing message", message);
    return Promise.resolve("0x1234567890abcdef"); // Mock signature
  }
}

// Create a function to initialize the mock MetaMask wallet
function initializeMockMetamask() {
  try {
    console.log("Initializing mock MetaMask wallet...");
    
    // Check if wallet already exists
    if (typeof window !== 'undefined' && 'ethereum' in window) {
      console.log("Ethereum provider already exists in window object, not replacing");
      return;
    }
    
    // Add the mock wallet to the window object
    if (typeof window !== 'undefined') {
      console.log("Adding mock MetaMask to window object");
      const mockMetamask = new MockMetamask();
      
      // Add ethereum provider to window
      (window as any).ethereum = {
        isMetaMask: true,
        request: async ({ method, params }: { method: string; params: any[] }) => {
          console.log(`Mock MetaMask: Received request for method ${method}`, params);
          
          switch (method) {
            case 'eth_requestAccounts':
              await mockMetamask.connect();
              return [mockMetamask.mockEthAddress];
              
            case 'eth_accounts':
              if (await mockMetamask.isConnected()) {
                return [mockMetamask.mockEthAddress];
              } else {
                return [];
              }
              
            case 'eth_chainId':
              return '0x1'; // Mainnet
              
            case 'eth_signTransaction':
              return mockMetamask.signTransaction(params[0]);
              
            case 'eth_signMessage':
            case 'personal_sign':
              return mockMetamask.signMessage(params[0]);
              
            default:
              console.warn(`Unknown method: ${method}`);
              return null;
          }
        },
        on: (event: string, callback: any) => {
          console.log(`Mock MetaMask: Registered event listener for ${event}`);
          // We don't really implement events in this mock
          return;
        },
        removeListener: (event: string, callback: any) => {
          console.log(`Mock MetaMask: Removed event listener for ${event}`);
          return;
        }
      };
      
      // Also add sonicWallet with metamask compatibility for backward compatibility
      (window as any).sonicWallet = mockMetamask;
      
      console.log("Mock MetaMask added to window object");
    } else {
      console.error("Window object not available");
    }
  } catch (error) {
    console.error("Error initializing mock MetaMask:", error);
  }
}

// Initialize the mock wallet
initializeMockMetamask();

export default MockMetamask; 
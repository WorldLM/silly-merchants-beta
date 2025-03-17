/**
 * Utility to resolve IPFS URLs to HTTP gateway URLs
 */

// Map of file names to IPFS CIDs
// This will be populated from the environment variables
const ipfsCidMap: Record<string, string> = {};

// Initialize the CID map from environment variables
Object.keys(process.env).forEach(key => {
  if (key.startsWith('NEXT_PUBLIC_IPFS_')) {
    const fileName = key
      .replace('NEXT_PUBLIC_IPFS_', '')
      .replace(/_/g, '.')
      .toLowerCase();
    
    ipfsCidMap[fileName] = process.env[key] as string;
  }
});

// List of IPFS gateways to use (for redundancy)
// Web3.Storage gateway is first for best performance
const ipfsGateways = [
  'https://{cid}.ipfs.w3s.link',
  'https://{cid}.ipfs.dweb.link',
  'https://ipfs.io/ipfs/{cid}',
  'https://cloudflare-ipfs.com/ipfs/{cid}'
];

// Current gateway index (for round-robin)
let currentGatewayIndex = 0;

/**
 * Resolves an IPFS URL or file name to an HTTP URL
 * @param ipfsUrlOrFileName IPFS URL (ipfs://CID) or file name
 * @returns HTTP URL for the IPFS content
 */
export function resolveIpfsUrl(ipfsUrlOrFileName: string): string {
  // If it's a file name, look up its CID
  if (ipfsUrlOrFileName.endsWith('.mp3')) {
    const cid = ipfsCidMap[ipfsUrlOrFileName];
    if (cid) {
      // Use round-robin to select a gateway
      const gateway = ipfsGateways[currentGatewayIndex];
      currentGatewayIndex = (currentGatewayIndex + 1) % ipfsGateways.length;
      
      return gateway.replace('{cid}', cid);
    }
    
    // Fallback to local file if CID not found
    return `/audio/${ipfsUrlOrFileName}`;
  }
  
  // If it's an IPFS URL, convert it to HTTP
  if (ipfsUrlOrFileName.startsWith('ipfs://')) {
    const cid = ipfsUrlOrFileName.replace('ipfs://', '');
    
    // Use round-robin to select a gateway
    const gateway = ipfsGateways[currentGatewayIndex];
    currentGatewayIndex = (currentGatewayIndex + 1) % ipfsGateways.length;
    
    return gateway.replace('{cid}', cid);
  }
  
  // If it's already an HTTP URL, return it as is
  return ipfsUrlOrFileName;
} 
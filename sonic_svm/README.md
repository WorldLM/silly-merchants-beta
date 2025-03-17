# Sonic SVM Game Contract

This is a Sonic SVM game contract that allows users to participate in games using SOL. The contract handles the entry fees, prize pool management, and automatic distribution of winnings.

## Features

1. **Entry Fee System**: Users pay a fixed amount of SOL as an entry fee to join a game.
2. **Prize Pool Management**: All entry fees are collected in a prize pool.
3. **Automatic Settlement**: When a game ends, the contract automatically distributes the prize pool:
   - 90% goes to the winner
   - 10% goes to a designated fee recipient (for development and maintenance)

## Contract Structure

The contract consists of three main instructions:

1. `initialize_game`: Creates a new game with a specified entry fee.
2. `join_game`: Allows a player to join the game by paying the entry fee.
3. `end_game`: Ends the game and distributes the prize pool based on the game result.

## Accounts

- `Game`: Stores game information including entry fee, prize pool, and game status.
- `PlayerEntry`: Records player participation in a specific game.

## Game End and Winner Determination

The contract itself does not determine when a game ends or who the winner is. Instead, it relies on an external authority (the game creator or a designated administrator) to:

1. **Game End Trigger**: The game's authority (set during initialization) is responsible for calling the `end_game` instruction when the game concludes. This is typically done by a centralized server that monitors the game state.

2. **Winner Determination**: The winner is determined off-chain by the game logic running on a centralized server. When calling the `end_game` instruction, the authority must provide the public key of the winning player as a parameter.

3. **Security Considerations**: Only the designated authority can end the game and declare a winner, which is enforced by the contract through signature verification.

This design separates the game logic (handled off-chain) from the financial aspects (handled by the contract), allowing for complex game mechanics while maintaining secure prize distribution.

## Development

### Prerequisites

- Rust and Cargo
- Solana CLI
- Anchor Framework

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Build the program:
   ```bash
   anchor build
   ```

3. Test the program:
   ```bash
   anchor test
   ```

4. Deploy to Sonic SVM:
   ```bash
   anchor deploy
   ```

## Usage

The game logic is handled off-chain, while the contract manages the financial aspects:

1. Game creator initializes a new game with a fixed entry fee.
2. Players join by paying the entry fee in SOL.
3. When the game concludes, the authority (game creator) calls `end_game` with the winner's address.
4. The contract automatically distributes 90% of the prize pool to the winner and 10% to the fee recipient.

## Frontend Integration Guide

### Contract Details

- **Program ID**: `25jUhpQfPWWJ9e4BaP6eNyH3y1YrhF9CDY5DHPhTBiFW`
- **Network**: Sonic Testnet (`https://api.testnet.sonic.game`)

### IDL

The IDL file is available in the `idl/sonic_svm.json` directory. You can load it in your frontend application to interact with the contract.

### Account PDAs

The contract uses the following PDAs:

1. **Game Account**: `[Buffer.from("game"), gameId.toArrayLike(Buffer, 'le', 8)]`
2. **Game Vault**: `[Buffer.from("vault"), gameId.toArrayLike(Buffer, 'le', 8)]`
3. **Player Entry**: `[Buffer.from("player"), gamePDA.toBuffer(), playerPublicKey.toBuffer()]`

### Important Implementation Notes

1. **Unique Game IDs**: Always use a unique game ID when initializing a new game. Using a timestamp is a good approach:
   ```typescript
   const gameId = new anchor.BN(Date.now());
   ```

2. **SOL Handling**: The contract now uses native SOL for all transactions. Players pay entry fees in SOL, and winners receive SOL rewards.

3. **Authority Management**: The authority (game creator) must be the same account that calls `end_game`. This is enforced by the contract.

### Integration Steps

1. **Setup Connection**:
   ```typescript
   import { Connection, PublicKey, SystemProgram } from '@solana/web3.js';
   import * as anchor from '@project-serum/anchor';
   
   const programId = new PublicKey('25jUhpQfPWWJ9e4BaP6eNyH3y1YrhF9CDY5DHPhTBiFW');
   const connection = new Connection('https://api.testnet.sonic.game', 'confirmed');
   ```

2. **Load IDL**:
   ```typescript
   const idl = require('./idl/sonic_svm.json');
   const program = new anchor.Program(idl, programId, provider);
   ```

3. **Initialize Game** (Admin only):
   ```typescript
   const gameId = new anchor.BN(Date.now()); // Use timestamp for unique ID
   const entryFee = new anchor.BN(10000000); // 0.01 SOL
   
   const [gamePDA] = await PublicKey.findProgramAddress(
     [Buffer.from("game"), gameId.toArrayLike(Buffer, 'le', 8)],
     program.programId
   );
   
   const [gameVaultPDA] = await PublicKey.findProgramAddress(
     [Buffer.from("vault"), gameId.toArrayLike(Buffer, 'le', 8)],
     program.programId
   );
   
   await program.methods
     .initializeGame(gameId, entryFee)
     .accounts({
       game: gamePDA,
       authority: wallet.publicKey,
       feeRecipient: feeRecipientPublicKey,
       gameVault: gameVaultPDA,
       systemProgram: SystemProgram.programId,
       rent: anchor.web3.SYSVAR_RENT_PUBKEY,
     })
     .signers([wallet.payer])
     .rpc();
   ```

4. **Join Game** (Players):
   ```typescript
   const [playerEntryPDA] = await PublicKey.findProgramAddress(
     [Buffer.from("player"), gamePDA.toBuffer(), wallet.publicKey.toBuffer()],
     program.programId
   );
   
   await program.methods
     .joinGame()
     .accounts({
       game: gamePDA,
       player: wallet.publicKey,
       gameVault: gameVaultPDA,
       playerEntry: playerEntryPDA,
       systemProgram: SystemProgram.programId,
       rent: anchor.web3.SYSVAR_RENT_PUBKEY,
     })
     .signers([wallet.payer])
     .rpc();
   ```

5. **End Game** (Admin only):
   ```typescript
   await program.methods
     .endGame(winnerPublicKey)
     .accounts({
       game: gamePDA,
       authority: wallet.publicKey, // Must be the same as the game creator
       gameVault: gameVaultPDA,
       winner: winnerPublicKey,
       feeRecipient: feeRecipientPublicKey,
       systemProgram: SystemProgram.programId,
     })
     .signers([wallet.payer])
     .rpc();
   ```

6. **Fetch Game Data**:
   ```typescript
   const gameAccount = await program.account.game.fetch(gamePDA);
   console.log("Game Data:", {
     authority: gameAccount.authority.toString(),
     gameId: gameAccount.gameId.toString(),
     entryFee: `${gameAccount.entryFee.toString()} lamports (${gameAccount.entryFee.toNumber() / 1e9} SOL)`,
     prizePool: `${gameAccount.prizePool.toString()} lamports (${gameAccount.prizePool.toNumber() / 1e9} SOL)`,
     isActive: gameAccount.isActive,
     playerCount: gameAccount.playerCount.toString(),
     winner: gameAccount.winner ? gameAccount.winner.toString() : null,
     feeRecipient: gameAccount.feeRecipient.toString()
   });
   ```

7. **Check Player Entry**:
   ```typescript
   const playerEntryAccount = await program.account.playerEntry.fetch(playerEntryPDA);
   console.log("Player Entry:", {
     player: playerEntryAccount.player.toString(),
     game: playerEntryAccount.game.toString(),
     joinedAt: new Date(playerEntryAccount.joinedAt.toNumber() * 1000).toISOString()
   });
   ```

8. **Check Game Vault Balance**:
   ```typescript
   const gameVaultBalance = await connection.getBalance(gameVaultPDA);
   console.log(`Game Vault Balance: ${gameVaultBalance} lamports (${gameVaultBalance / 1e9} SOL)`);
   ```

### Error Handling

Common errors to handle in your frontend:

1. **Game Already Exists**: When trying to initialize a game with an ID that's already in use.
   ```
   Allocate: account Address already in use
   ```
   Solution: Use a unique game ID (e.g., timestamp).

2. **Game Not Active**: When trying to join a game that's not active.
   ```
   Error Code: GameNotActive. Error Number: 6000. Error Message: Game is not active.
   ```
   Solution: Check game status before joining.

3. **Unauthorized Access**: When trying to end a game without being the authority.
   ```
   Error Code: ConstraintRaw. Error Number: 2003. Error Message: A raw constraint was violated.
   ```
   Solution: Ensure the same wallet that created the game is ending it.

4. **Insufficient Funds**: When a player doesn't have enough SOL to pay the entry fee.
   Solution: Check player balance before joining.

### Test Results

The contract has been successfully tested on the Sonic Testnet with the following results:

1. **Game Initialization**: Successfully created a game with an entry fee of 0.01 SOL.
2. **Player Joining**: Players can successfully join the game by paying the entry fee in SOL.
3. **Prize Distribution**: When the game ends, 90% of the prize pool is sent to the winner and 10% to the fee recipient.

Example test output:
```
✅ 初始化游戏成功
游戏账户数据:
- 权限: 3N34AmhAbcncRf3twdFAxjWfe3hkLbWCVZC2YNShb185
- 游戏ID: 1742191115320
- 入场费: 10000000 lamports (0.01 SOL)
- 奖池: 0 lamports (0 SOL)
- 是否活跃: true
- 玩家数量: 0
- 手续费接收者: DcchPY9gXM7z8QWre6WoMDoXE3SW92hZujgbvRVqdmys

✅ 加入游戏成功
游戏账户数据:
- 奖池: 10000000 lamports (0.01 SOL)
- 玩家数量: 1
玩家条目账户数据:
- 玩家: CqWjfX4M1zqzrBGixtxEE3iS8nu1c7Vpcecm4BmxCvvR
- 游戏: H9rExymxhwi2q1ER88RjD5RcjRETYKxyVg63jYi5N7Q1
- 加入时间: 2025-03-17T05:58:35.000Z
游戏金库余额: 10890880 lamports (0.01089088 SOL)

✅ 结束游戏成功
游戏账户数据:
- 是否活跃: false
- 获胜者: CqWjfX4M1zqzrBGixtxEE3iS8nu1c7Vpcecm4BmxCvvR
玩家获得奖励: 0.009 SOL
手续费接收者获得手续费: 0.001 SOL
```

## License

MIT 
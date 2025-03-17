import * as anchor from '@project-serum/anchor';
import { Program } from '@project-serum/anchor';
import { SonicSvm } from '../target/types/sonic_svm';
import { PublicKey, Keypair, SystemProgram } from '@solana/web3.js';
import { TOKEN_PROGRAM_ID, createMint, createAccount, mintTo } from '@solana/spl-token';
import { assert } from 'chai';

describe('sonic-svm', () => {
  // Configure the client to use the local cluster
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.SonicSvm as Program<SonicSvm>;
  
  // Game parameters
  const gameId = new anchor.BN(1);
  const entryFee = new anchor.BN(1000000000); // 1 SONIC token (assuming 9 decimals)
  
  // Test accounts
  const authority = Keypair.generate();
  const player1 = Keypair.generate();
  const player2 = Keypair.generate();
  const feeRecipient = Keypair.generate();
  
  // PDAs and token accounts
  let sonicTokenMint: PublicKey;
  let authorityTokenAccount: PublicKey;
  let player1TokenAccount: PublicKey;
  let player2TokenAccount: PublicKey;
  let feeRecipientTokenAccount: PublicKey;
  let gamePDA: PublicKey;
  let gameVaultPDA: PublicKey;
  let player1EntryPDA: PublicKey;
  let player2EntryPDA: PublicKey;
  let gameBump: number;
  let vaultBump: number;
  
  before(async () => {
    // Airdrop SOL to test accounts
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(authority.publicKey, 10 * anchor.web3.LAMPORTS_PER_SOL)
    );
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(player1.publicKey, 10 * anchor.web3.LAMPORTS_PER_SOL)
    );
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(player2.publicKey, 10 * anchor.web3.LAMPORTS_PER_SOL)
    );
    
    // Create SONIC token mint
    sonicTokenMint = await createMint(
      provider.connection,
      authority,
      authority.publicKey,
      null,
      9 // 9 decimals
    );
    
    // Create token accounts
    authorityTokenAccount = await createAccount(
      provider.connection,
      authority,
      sonicTokenMint,
      authority.publicKey
    );
    
    player1TokenAccount = await createAccount(
      provider.connection,
      player1,
      sonicTokenMint,
      player1.publicKey
    );
    
    player2TokenAccount = await createAccount(
      provider.connection,
      player2,
      sonicTokenMint,
      player2.publicKey
    );
    
    feeRecipientTokenAccount = await createAccount(
      provider.connection,
      feeRecipient,
      sonicTokenMint,
      feeRecipient.publicKey
    );
    
    // Mint tokens to players
    await mintTo(
      provider.connection,
      authority,
      sonicTokenMint,
      player1TokenAccount,
      authority.publicKey,
      entryFee.toNumber() * 2
    );
    
    await mintTo(
      provider.connection,
      authority,
      sonicTokenMint,
      player2TokenAccount,
      authority.publicKey,
      entryFee.toNumber() * 2
    );
    
    // Derive PDAs
    [gamePDA, gameBump] = await PublicKey.findProgramAddress(
      [Buffer.from('game'), gameId.toArrayLike(Buffer, 'le', 8)],
      program.programId
    );
    
    [gameVaultPDA, vaultBump] = await PublicKey.findProgramAddress(
      [Buffer.from('vault'), gameId.toArrayLike(Buffer, 'le', 8)],
      program.programId
    );
    
    [player1EntryPDA] = await PublicKey.findProgramAddress(
      [Buffer.from('player'), gamePDA.toBuffer(), player1.publicKey.toBuffer()],
      program.programId
    );
    
    [player2EntryPDA] = await PublicKey.findProgramAddress(
      [Buffer.from('player'), gamePDA.toBuffer(), player2.publicKey.toBuffer()],
      program.programId
    );
  });
  
  it('Initializes a new game', async () => {
    await program.methods
      .initializeGame(gameId, entryFee)
      .accounts({
        game: gamePDA,
        authority: authority.publicKey,
        feeRecipient: feeRecipient.publicKey,
        gameVault: gameVaultPDA,
        sonicTokenMint: sonicTokenMint,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        rent: anchor.web3.SYSVAR_RENT_PUBKEY,
      })
      .signers([authority])
      .rpc();
    
    // Verify game state
    const gameAccount = await program.account.game.fetch(gamePDA);
    assert.equal(gameAccount.authority.toString(), authority.publicKey.toString());
    assert.equal(gameAccount.gameId.toString(), gameId.toString());
    assert.equal(gameAccount.entryFee.toString(), entryFee.toString());
    assert.equal(gameAccount.prizePool.toString(), '0');
    assert.equal(gameAccount.isActive, true);
    assert.equal(gameAccount.playerCount.toString(), '0');
    assert.equal(gameAccount.feeRecipient.toString(), feeRecipient.publicKey.toString());
  });
  
  it('Allows players to join the game', async () => {
    // Player 1 joins
    await program.methods
      .joinGame()
      .accounts({
        game: gamePDA,
        player: player1.publicKey,
        playerTokenAccount: player1TokenAccount,
        gameVault: gameVaultPDA,
        playerEntry: player1EntryPDA,
        sonicTokenMint: sonicTokenMint,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        rent: anchor.web3.SYSVAR_RENT_PUBKEY,
      })
      .signers([player1])
      .rpc();
    
    // Player 2 joins
    await program.methods
      .joinGame()
      .accounts({
        game: gamePDA,
        player: player2.publicKey,
        playerTokenAccount: player2TokenAccount,
        gameVault: gameVaultPDA,
        playerEntry: player2EntryPDA,
        sonicTokenMint: sonicTokenMint,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        rent: anchor.web3.SYSVAR_RENT_PUBKEY,
      })
      .signers([player2])
      .rpc();
    
    // Verify game state
    const gameAccount = await program.account.game.fetch(gamePDA);
    assert.equal(gameAccount.playerCount.toString(), '2');
    assert.equal(gameAccount.prizePool.toString(), entryFee.mul(new anchor.BN(2)).toString());
    
    // Verify player entries
    const player1Entry = await program.account.playerEntry.fetch(player1EntryPDA);
    assert.equal(player1Entry.player.toString(), player1.publicKey.toString());
    assert.equal(player1Entry.game.toString(), gamePDA.toString());
    
    const player2Entry = await program.account.playerEntry.fetch(player2EntryPDA);
    assert.equal(player2Entry.player.toString(), player2.publicKey.toString());
    assert.equal(player2Entry.game.toString(), gamePDA.toString());
  });
  
  it('Ends the game and distributes prizes correctly', async () => {
    // End the game with player1 as the winner
    await program.methods
      .endGame(player1.publicKey)
      .accounts({
        game: gamePDA,
        authority: authority.publicKey,
        gameVault: gameVaultPDA,
        winnerTokenAccount: player1TokenAccount,
        feeRecipientTokenAccount: feeRecipientTokenAccount,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .signers([authority])
      .rpc();
    
    // Verify game state
    const gameAccount = await program.account.game.fetch(gamePDA);
    assert.equal(gameAccount.isActive, false);
    assert.equal(gameAccount.winner.toString(), player1.publicKey.toString());
    
    // Check token balances
    // Winner should have received 90% of the prize pool
    const totalPrize = entryFee.mul(new anchor.BN(2));
    const winnerPrize = totalPrize.mul(new anchor.BN(90)).div(new anchor.BN(100));
    const feeAmount = totalPrize.sub(winnerPrize);
    
    // TODO: Add token balance checks here
  });
}); 
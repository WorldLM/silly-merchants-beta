import * as anchor from '@project-serum/anchor';
import { Program } from '@project-serum/anchor';
import { PublicKey, Keypair, Connection, SystemProgram } from '@solana/web3.js';
import { assert } from 'chai';
import fs from 'fs';
import path from 'path';

// 合约地址
const PROGRAM_ID = new PublicKey('25jUhpQfPWWJ9e4BaP6eNyH3y1YrhF9CDY5DHPhTBiFW');

// 连接到Sonic测试网
const connection = new Connection('https://api.testnet.sonic.game', 'confirmed');

// 从文件加载IDL
const idlPath = path.join(__dirname, '../idl/sonic_svm.json');
const idlFile = fs.readFileSync(idlPath, 'utf8');
const IDL = JSON.parse(idlFile);

// 定义类型
type Game = {
  authority: PublicKey;
  gameId: anchor.BN;
  entryFee: anchor.BN;
  prizePool: anchor.BN;
  isActive: boolean;
  playerCount: anchor.BN;
  winner: PublicKey | null;
  feeRecipient: PublicKey;
};

type PlayerEntry = {
  player: PublicKey;
  game: PublicKey;
  joinedAt: anchor.BN;
};

async function main() {
  try {
    console.log("开始测试Sonic SVM游戏合约...");
    
    // 创建钱包
    const payer = Keypair.generate();
    const authority = payer; // 使用同一个账户作为payer和authority
    const player = Keypair.generate();
    const feeRecipient = Keypair.generate();
    
    console.log("创建的钱包地址:");
    console.log(`Payer/Authority: ${payer.publicKey.toString()}`);
    console.log(`Player: ${player.publicKey.toString()}`);
    console.log(`Fee Recipient: ${feeRecipient.publicKey.toString()}`);
    
    // 请求空投SOL
    console.log("请求空投SOL...");
    console.log("请手动从水龙头获取SOL: https://faucet.sonic.game");
    console.log(`需要为以下地址空投SOL: ${payer.publicKey.toString()}`);
    console.log(`需要为以下地址空投SOL: ${player.publicKey.toString()}`);
    
    // 等待用户手动空投SOL
    console.log("请在空投SOL后按Enter键继续...");
    await new Promise(resolve => {
      process.stdin.once('data', () => {
        resolve(null);
      });
    });
    
    // 检查余额
    const payerBalance = await connection.getBalance(payer.publicKey);
    const playerBalance = await connection.getBalance(player.publicKey);
    console.log(`Payer余额: ${payerBalance / 1e9} SOL`);
    console.log(`Player余额: ${playerBalance / 1e9} SOL`);
    
    if (payerBalance < 10000000) {
      console.error("Payer余额不足，请确保从水龙头获取足够的SOL（至少0.01 SOL）");
      process.exit(1);
    }
    
    if (playerBalance < 10000000) {
      console.error("Player余额不足，请确保从水龙头获取足够的SOL（至少0.01 SOL）");
      process.exit(1);
    }
    
    // 创建Provider
    const provider = new anchor.AnchorProvider(
      connection,
      new anchor.Wallet(payer),
      { commitment: 'confirmed' }
    );
    
    // 创建Program
    const program = new anchor.Program(IDL, PROGRAM_ID, provider);
    
    // 游戏参数
    const gameId = new anchor.BN(Date.now()); // 使用当前时间戳作为游戏ID，确保唯一性
    const entryFee = new anchor.BN(10000000); // 0.01 SOL
    
    // 派生PDA
    console.log("派生PDA...");
    const [gamePDA, gameBump] = await PublicKey.findProgramAddress(
      [Buffer.from("game"), gameId.toArrayLike(Buffer, 'le', 8)],
      program.programId
    );
    
    const [gameVaultPDA, vaultBump] = await PublicKey.findProgramAddress(
      [Buffer.from("vault"), gameId.toArrayLike(Buffer, 'le', 8)],
      program.programId
    );
    
    const [playerEntryPDA] = await PublicKey.findProgramAddress(
      [Buffer.from("player"), gamePDA.toBuffer(), player.publicKey.toBuffer()],
      program.programId
    );
    
    console.log(`Game PDA: ${gamePDA.toString()}`);
    console.log(`Game Vault PDA: ${gameVaultPDA.toString()}`);
    console.log(`Player Entry PDA: ${playerEntryPDA.toString()}`);
    
    // 初始化游戏
    console.log("\n测试初始化游戏...");
    try {
      await program.methods
        .initializeGame(gameId, entryFee)
        .accounts({
          game: gamePDA,
          authority: authority.publicKey,
          feeRecipient: feeRecipient.publicKey,
          gameVault: gameVaultPDA,
          systemProgram: SystemProgram.programId,
          rent: anchor.web3.SYSVAR_RENT_PUBKEY,
        })
        .signers([authority]) // 只使用authority作为签名者
        .rpc();
      
      console.log("✅ 初始化游戏成功");
      
      // 获取游戏账户数据
      const gameAccount = await program.account.game.fetch(gamePDA) as unknown as Game;
      console.log("游戏账户数据:");
      console.log(`- 权限: ${gameAccount.authority.toString()}`);
      console.log(`- 游戏ID: ${gameAccount.gameId.toString()}`);
      console.log(`- 入场费: ${gameAccount.entryFee.toString()} lamports (${gameAccount.entryFee.toNumber() / 1e9} SOL)`);
      console.log(`- 奖池: ${gameAccount.prizePool.toString()} lamports (${gameAccount.prizePool.toNumber() / 1e9} SOL)`);
      console.log(`- 是否活跃: ${gameAccount.isActive}`);
      console.log(`- 玩家数量: ${gameAccount.playerCount.toString()}`);
      console.log(`- 手续费接收者: ${gameAccount.feeRecipient.toString()}`);
    } catch (error) {
      console.error("❌ 初始化游戏失败:", error);
    }
    
    // 加入游戏
    console.log("\n测试加入游戏...");
    try {
      await program.methods
        .joinGame()
        .accounts({
          game: gamePDA,
          player: player.publicKey,
          gameVault: gameVaultPDA,
          playerEntry: playerEntryPDA,
          systemProgram: SystemProgram.programId,
          rent: anchor.web3.SYSVAR_RENT_PUBKEY,
        })
        .signers([player]) // 只使用player作为签名者
        .rpc();
      
      console.log("✅ 加入游戏成功");
      
      // 获取游戏账户数据
      const gameAccount = await program.account.game.fetch(gamePDA) as unknown as Game;
      console.log("游戏账户数据:");
      console.log(`- 奖池: ${gameAccount.prizePool.toString()} lamports (${gameAccount.prizePool.toNumber() / 1e9} SOL)`);
      console.log(`- 玩家数量: ${gameAccount.playerCount.toString()}`);
      
      // 获取玩家条目账户数据
      const playerEntryAccount = await program.account.playerEntry.fetch(playerEntryPDA) as unknown as PlayerEntry;
      console.log("玩家条目账户数据:");
      console.log(`- 玩家: ${playerEntryAccount.player.toString()}`);
      console.log(`- 游戏: ${playerEntryAccount.game.toString()}`);
      console.log(`- 加入时间: ${new Date(playerEntryAccount.joinedAt.toNumber() * 1000).toISOString()}`);
      
      // 获取游戏金库余额
      const gameVaultBalance = await connection.getBalance(gameVaultPDA);
      console.log(`游戏金库余额: ${gameVaultBalance} lamports (${gameVaultBalance / 1e9} SOL)`);
    } catch (error) {
      console.error("❌ 加入游戏失败:", error);
    }
    
    // 结束游戏
    console.log("\n测试结束游戏...");
    try {
      // 获取结束游戏前的余额
      const playerBalanceBefore = await connection.getBalance(player.publicKey);
      const feeRecipientBalanceBefore = await connection.getBalance(feeRecipient.publicKey);
      
      await program.methods
        .endGame(player.publicKey)
        .accounts({
          game: gamePDA,
          authority: authority.publicKey,
          gameVault: gameVaultPDA,
          winner: player.publicKey,
          feeRecipient: feeRecipient.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([authority]) // 只使用authority作为签名者
        .rpc();
      
      console.log("✅ 结束游戏成功");
      
      // 获取游戏账户数据
      const gameAccount = await program.account.game.fetch(gamePDA) as unknown as Game;
      console.log("游戏账户数据:");
      console.log(`- 是否活跃: ${gameAccount.isActive}`);
      console.log(`- 获胜者: ${gameAccount.winner ? gameAccount.winner.toString() : "无"}`);
      
      // 获取结束游戏后的余额
      const playerBalanceAfter = await connection.getBalance(player.publicKey);
      const feeRecipientBalanceAfter = await connection.getBalance(feeRecipient.publicKey);
      
      console.log(`玩家获得奖励: ${(playerBalanceAfter - playerBalanceBefore) / 1e9} SOL`);
      console.log(`手续费接收者获得手续费: ${(feeRecipientBalanceAfter - feeRecipientBalanceBefore) / 1e9} SOL`);
    } catch (error) {
      console.error("❌ 结束游戏失败:", error);
    }
    
    console.log("\n测试完成");
  } catch (error) {
    console.error("测试过程中出错:", error);
  }
}

main().then(
  () => process.exit(0),
  (error) => {
    console.error(error);
    process.exit(1);
  }
);
use anchor_lang::prelude::*;
use anchor_lang::system_program;

declare_id!("25jUhpQfPWWJ9e4BaP6eNyH3y1YrhF9CDY5DHPhTBiFW");

#[program]
pub mod sonic_svm {
    use super::*;

    // Initialize a new game with a fixed entry fee
    pub fn initialize_game(
        ctx: Context<InitializeGame>,
        game_id: u64,
        entry_fee: u64,
    ) -> Result<()> {
        let game = &mut ctx.accounts.game;
        game.authority = ctx.accounts.authority.key();
        game.game_id = game_id;
        game.entry_fee = entry_fee;
        game.prize_pool = 0;
        game.is_active = true;
        game.player_count = 0;
        game.winner = None;
        game.fee_recipient = ctx.accounts.fee_recipient.key();
        
        Ok(())
    }

    // Player joins the game by paying the entry fee
    pub fn join_game(ctx: Context<JoinGame>) -> Result<()> {
        let game = &mut ctx.accounts.game;
        require!(game.is_active, ErrorCode::GameNotActive);

        // Transfer the entry fee from player to the game vault
        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: ctx.accounts.player.to_account_info(),
                    to: ctx.accounts.game_vault.to_account_info(),
                },
            ),
            game.entry_fee,
        )?;

        // Update game state
        game.prize_pool = game.prize_pool.checked_add(game.entry_fee).unwrap();
        game.player_count = game.player_count.checked_add(1).unwrap();
        
        // Add player to the game's player list
        let player_entry = &mut ctx.accounts.player_entry;
        player_entry.player = ctx.accounts.player.key();
        player_entry.game = game.key();
        player_entry.joined_at = Clock::get()?.unix_timestamp;

        Ok(())
    }

    // End the game and distribute prizes
    pub fn end_game(ctx: Context<EndGame>, winner_key: Pubkey) -> Result<()> {
        // First, get all the data we need from the game account
        let game_id = ctx.accounts.game.game_id;
        let is_active = ctx.accounts.game.is_active;
        let authority = ctx.accounts.game.authority;
        let prize_pool = ctx.accounts.game.prize_pool;
        
        // Perform validations
        require!(is_active, ErrorCode::GameNotActive);
        require!(authority == ctx.accounts.authority.key(), ErrorCode::Unauthorized);

        // Calculate prize distribution (90% to winner, 10% to fee recipient)
        let winner_prize = prize_pool.checked_mul(90).unwrap().checked_div(100).unwrap();
        let fee_amount = prize_pool.checked_sub(winner_prize).unwrap();

        // Update game state
        let game = &mut ctx.accounts.game;
        game.is_active = false;
        game.winner = Some(winner_key);

        // Transfer winner prize
        **ctx.accounts.game_vault.try_borrow_mut_lamports()? = ctx
            .accounts
            .game_vault
            .lamports()
            .checked_sub(winner_prize)
            .unwrap();
            
        **ctx.accounts.winner.try_borrow_mut_lamports()? = ctx
            .accounts
            .winner
            .lamports()
            .checked_add(winner_prize)
            .unwrap();

        // Transfer fee to fee recipient
        **ctx.accounts.game_vault.try_borrow_mut_lamports()? = ctx
            .accounts
            .game_vault
            .lamports()
            .checked_sub(fee_amount)
            .unwrap();
            
        **ctx.accounts.fee_recipient.try_borrow_mut_lamports()? = ctx
            .accounts
            .fee_recipient
            .lamports()
            .checked_add(fee_amount)
            .unwrap();

        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(game_id: u64, entry_fee: u64)]
pub struct InitializeGame<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + Game::SPACE,
        seeds = [b"game".as_ref(), game_id.to_le_bytes().as_ref()],
        bump
    )]
    pub game: Account<'info, Game>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    /// CHECK: This is the address that will receive the fee
    pub fee_recipient: AccountInfo<'info>,
    
    #[account(
        init,
        payer = authority,
        seeds = [b"vault".as_ref(), game_id.to_le_bytes().as_ref()],
        bump,
        space = 0,
    )]
    /// CHECK: This is a PDA that will hold SOL
    pub game_vault: AccountInfo<'info>,
    
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct JoinGame<'info> {
    #[account(mut)]
    pub game: Account<'info, Game>,
    
    #[account(mut)]
    pub player: Signer<'info>,
    
    #[account(
        mut,
        seeds = [b"vault".as_ref(), game.game_id.to_le_bytes().as_ref()],
        bump,
    )]
    /// CHECK: This is a PDA that holds SOL
    pub game_vault: AccountInfo<'info>,
    
    #[account(
        init,
        payer = player,
        space = 8 + PlayerEntry::SPACE,
        seeds = [b"player".as_ref(), game.key().as_ref(), player.key().as_ref()],
        bump
    )]
    pub player_entry: Account<'info, PlayerEntry>,
    
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct EndGame<'info> {
    #[account(
        mut,
        seeds = [b"game".as_ref(), game.game_id.to_le_bytes().as_ref()],
        bump,
    )]
    pub game: Account<'info, Game>,
    
    #[account(
        constraint = authority.key() == game.authority,
    )]
    pub authority: Signer<'info>,
    
    #[account(
        mut,
        seeds = [b"vault".as_ref(), game.game_id.to_le_bytes().as_ref()],
        bump,
    )]
    /// CHECK: This is a PDA that holds SOL
    pub game_vault: AccountInfo<'info>,
    
    #[account(mut)]
    /// CHECK: This is the winner's account that will receive SOL
    pub winner: AccountInfo<'info>,
    
    #[account(
        mut,
        constraint = fee_recipient.key() == game.fee_recipient,
    )]
    /// CHECK: This is the fee recipient's account that will receive SOL
    pub fee_recipient: AccountInfo<'info>,
    
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Game {
    pub authority: Pubkey,
    pub game_id: u64,
    pub entry_fee: u64,
    pub prize_pool: u64,
    pub is_active: bool,
    pub player_count: u64,
    pub winner: Option<Pubkey>,
    pub fee_recipient: Pubkey,
}

impl Game {
    pub const SPACE: usize = 32 + 8 + 8 + 8 + 1 + 8 + 33 + 32;
}

#[account]
pub struct PlayerEntry {
    pub player: Pubkey,
    pub game: Pubkey,
    pub joined_at: i64,
}

impl PlayerEntry {
    pub const SPACE: usize = 32 + 32 + 8;
}

#[error_code]
pub enum ErrorCode {
    #[msg("Game is not active")]
    GameNotActive,
    #[msg("Unauthorized access")]
    Unauthorized,
} 
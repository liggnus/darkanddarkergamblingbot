import interactions
from interactions import Permissions, slash_default_member_permission, File, Embed
from interactions import slash_command, SlashContext, slash_option, OptionType, listen, events
import random
import json
from PIL import Image
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load the environment variables from .env file
load_dotenv()

# Load the token from environment variable
TOKEN = os.getenv('DISCORD_TOKEN')

# Load currency data from file
def load_currency():
    try:
        with open('currency_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save currency data to file
def save_currency():
    with open('currency_data.json', 'w') as file:
        json.dump(currency, file)

# Initialize currency dictionary
currency = load_currency()

# Add a new function to load total wagered data
def load_total_wagers():
    try:
        with open('wager_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Add a new function to save total wagered data
def save_total_wagers(wagers):
    with open('wager_data.json', 'w') as file:
        json.dump(wagers, file)

# Initialize the total wagered dictionary
wager_data = load_total_wagers()

# Dictionary to store last claimed daily reward times
last_daily_claim = {}

# Function to load daily claim times from file (if you want persistence)
def load_daily_claims():
    try:
        with open('daily_claims.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Function to save daily claim times to file
def save_daily_claims():
    with open('daily_claims.json', 'w') as file:
        json.dump(last_daily_claim, file)

# Initialize the last claim dictionary from file
last_daily_claim = load_daily_claims()

# Initialize the bot
bot = interactions.Client(token=TOKEN)

# Event for when the bot is ready
@bot.event
async def on_startup():
    print(f'{bot.me.name} has connected to Discord!')

@listen(events.MemberAdd)  # Use events.MemberAdd to capture when a member joins
async def on_guild_member_add(event: events.MemberAdd):
    channel_id = 1291005867981934646  # Replace with your welcome channel ID
    channel = await event.client.fetch_channel(channel_id)
    
    # Send a welcome message in the desired channel
    member = event.member
    await channel.send(f"Welcome to the server, {member.mention}! Don't forget to claim your 100 currency! Good luck have fun!")

@interactions.slash_command(
    name="wager_leaderboard",
    description="Displays the top players ranked by total wagered amount.",
)
async def wager_leaderboard(ctx: interactions.SlashContext):
    # Load the total wager data
    wager_data = load_total_wagers()

    # Debugging: print the wager data
    print("Wager data:", wager_data)  # This will print in your console to verify the data
    
    # Sort the players by total wagered amount in descending order
    sorted_players = sorted(wager_data.items(), key=lambda x: x[1], reverse=True)

    if not sorted_players:
        await ctx.send("No wagers have been placed yet.")
        return

    # Create an embed for the leaderboard
    wager_leaderboard_embed = interactions.Embed(
        title="🎲 **Total Wagers Leaderboard** 🎲",
        description="Top players ranked by total wagered amount this week.",
        color=0xFFD700  # Gold color for the leaderboard
    )

    # Limit to top 10 players or total number of players, whichever is smaller
    top_players = sorted_players[:10]
    for rank, (player_id, wagered) in enumerate(top_players, 1):
        try:
            # Fetch the player (user) by their ID and display their name and total wagered
            member = await bot.fetch_user(int(player_id))
            player_name = member.username if member else "Unknown Player"
            wager_leaderboard_embed.add_field(name=f"{rank}. {player_name}", value=f"Total Wagered: {wagered} currency", inline=False)
        except Exception as e:
            print(f"Error fetching user {player_id}: {e}")
            player_name = "Unknown Player"
            wager_leaderboard_embed.add_field(name=f"{rank}. {player_name}", value=f"Total Wagered: {wagered} currency", inline=False)

    # Send the leaderboard embed
    await ctx.send(embed=wager_leaderboard_embed)

@interactions.slash_command(
    name="reset_wager_leaderboard",
    description="Manually reset the wager leaderboard (Admin only)",
    scopes=[1288166371477160057]  # Replace with your guild ID
)
@slash_default_member_permission(Permissions.ADMINISTRATOR)
async def reset_wager_leaderboard(ctx: interactions.SlashContext):
    # Clear the wager data
    global wager_data
    wager_data = {}
    
    # Save the cleared wager data to the file
    save_total_wagers(wager_data)

    await ctx.send("The wager leaderboard has been successfully reset!")

@interactions.slash_command(
    name="daily",
    description="Claim your daily reward",
    scopes=[1288166371477160057]  # Replace with your guild ID
)
async def daily(ctx: interactions.SlashContext):
    user_id = str(ctx.author.id)
    current_time = datetime.now()

    # Check if user has claimed in the last 24 hours
    if user_id in last_daily_claim:
        last_claim_time = datetime.fromisoformat(last_daily_claim[user_id])
        time_since_last_claim = current_time - last_claim_time

        if time_since_last_claim < timedelta(days=1):
            hours_remaining = 24 - time_since_last_claim.total_seconds() // 3600
            await ctx.send(f"{ctx.author.username}, you've already claimed your daily reward! You can claim again in {int(hours_remaining)} hours.")
            return

    # Reward the user with a fixed amount of currency (e.g., 100)
    reward = 50  # You can make this a random value if you prefer
    if user_id not in currency:
        currency[user_id] = 0

    currency[user_id] += reward
    last_daily_claim[user_id] = current_time.isoformat()

    # Save the currency and claim time
    save_currency()
    save_daily_claims()

    await ctx.send(f"{ctx.author.username}, you've claimed your daily reward of {reward} currency! Your current balance is {currency[user_id]} currency.")

# Command for checking balance
@interactions.slash_command(
    name="check_balance",
    description="Check your balance or another player's balance",
    scopes=[1288166371477160057]
)
@interactions.slash_option(
    name="member",
    description="The member whose balance you want to check",
    opt_type=interactions.OptionType.USER,
    required=False
)
async def check_balance(ctx: interactions.SlashContext, member: interactions.Member = None):
    user = member or ctx.author
    user_id = str(user.id)

    balance = currency.get(user_id, 0)  # Default to 0 if the user doesn't have any balance
    await ctx.send(f"{user.display_name} has {balance} currency.")

# Command for removing currency (admin only)
@interactions.slash_command(
    name="remove_currency",
    description="Remove currency from a player's account (admin only)",
    scopes=[1288166371477160057]
)
@slash_default_member_permission(Permissions.ADMINISTRATOR)
@interactions.slash_option(
    name="member",
    description="The member whose currency you want to remove",
    opt_type=interactions.OptionType.USER,
    required=True
)
@interactions.slash_option(
    name="amount",
    description="Amount of currency to remove",
    opt_type=interactions.OptionType.INTEGER,
    required=True
)
async def remove_currency(ctx: interactions.SlashContext, member: interactions.Member, amount: int):
    user_id = str(member.id)

    if user_id not in currency or currency[user_id] < amount:
        await ctx.send(f"{member.display_name} doesn't have enough currency to remove.")
        return

    # Deduct the amount from the user's balance
    currency[user_id] -= amount
    save_currency()  # Save the updated balance

    await ctx.send(f"Removed {amount} currency from {member.display_name}'s account. They now have {currency[user_id]} currency.")

# Slash Command to add currency (Admin only)
@interactions.slash_command(
    name="add_currency",
    description="Add currency to a player's account (admin only)",
    scopes=[1288166371477160057]  # Replace with your actual guild ID
)
@slash_default_member_permission(Permissions.ADMINISTRATOR)
@interactions.slash_option(
    name="member",
    description="The member whose account you want to add currency to",
    opt_type=interactions.OptionType.USER,
    required=True
)
@interactions.slash_option(
    name="amount",
    description="Amount of currency to add",
    opt_type=interactions.OptionType.INTEGER,
    required=True
)
async def add_currency(ctx: interactions.SlashContext, member: interactions.Member, amount: int):
    user_id = str(member.id)

    # Initialize user balance if they don't already have one
    if user_id not in currency:
        currency[user_id] = 0

    # Add the specified amount to the user's balance
    currency[user_id] += amount
    save_currency()  # Save the updated balance

    await ctx.send(f"Added {amount} currency to {member.display_name}'s account. They now have {currency[user_id]} currency.")




def safe_remove_file(path):
    try:
        os.remove(path)
    except OSError as e:
        print(f"Error removing file {path}: {e}")

# Dictionary to store the game state for each player
game_states = {}

# Preload all card images into a dictionary
card_image_paths = {
    'back_of_card': 'back_of_card.png',
    'Ace of Clubs': 'Ace_of_Clubs.png',
    '2 of Clubs': '2_of_Clubs.png',
    '3 of Clubs': '3_of_Clubs.png',
    '4 of Clubs': '4_of_Clubs.png',
    '5 of Clubs': '5_of_Clubs.png',
    '6 of Clubs': '6_of_Clubs.png',
    '7 of Clubs': '7_of_Clubs.png',
    '8 of Clubs': '8_of_Clubs.png',
    '9 of Clubs': '9_of_Clubs.png',
    '10 of Clubs': '10_of_Clubs.png',
    'Jack of Clubs': 'Jack_of_Clubs.png',
    'Queen of Clubs': 'Queen_of_Clubs.png',
    'King of Clubs': 'King_of_Clubs.png',

    'Ace of Spades': 'Ace_of_Spades.png',
    '2 of Spades': '2_of_Spades.png',
    '3 of Spades': '3_of_Spades.png',
    '4 of Spades': '4_of_Spades.png',
    '5 of Spades': '5_of_Spades.png',
    '6 of Spades': '6_of_Spades.png',
    '7 of Spades': '7_of_Spades.png',
    '8 of Spades': '8_of_Spades.png',
    '9 of Spades': '9_of_Spades.png',
    '10 of Spades': '10_of_Spades.png',
    'Jack of Spades': 'Jack_of_Spades.png',
    'Queen of Spades': 'Queen_of_Spades.png',
    'King of Spades': 'King_of_Spades.png',

    'Ace of Hearts': 'Ace_of_Hearts.png',
    '2 of Hearts': '2_of_Hearts.png',
    '3 of Hearts': '3_of_Hearts.png',
    '4 of Hearts': '4_of_Hearts.png',
    '5 of Hearts': '5_of_Hearts.png',
    '6 of Hearts': '6_of_Hearts.png',
    '7 of Hearts': '7_of_Hearts.png',
    '8 of Hearts': '8_of_Hearts.png',
    '9 of Hearts': '9_of_Hearts.png',
    '10 of Hearts': '10_of_Hearts.png',
    'Jack of Hearts': 'Jack_of_Hearts.png',
    'Queen of Hearts': 'Queen_of_Hearts.png',
    'King of Hearts': 'King_of_Hearts.png',

    'Ace of Diamonds': 'Ace_of_Diamonds.png',
    '2 of Diamonds': '2_of_Diamonds.png',
    '3 of Diamonds': '3_of_Diamonds.png',
    '4 of Diamonds': '4_of_Diamonds.png',
    '5 of Diamonds': '5_of_Diamonds.png',
    '6 of Diamonds': '6_of_Diamonds.png',
    '7 of Diamonds': '7_of_Diamonds.png',
    '8 of Diamonds': '8_of_Diamonds.png',
    '9 of Diamonds': '9_of_Diamonds.png',
    '10 of Diamonds': '10_of_Diamonds.png',
    'Jack of Diamonds': 'Jack_of_Diamonds.png',
    'Queen of Diamonds': 'Queen_of_Diamonds.png',
    'King of Diamonds': 'King_of_Diamonds.png'
}

# Utility function to combine card images into one image
def combine_cards(card_names):
    cards = []

    for card_name in card_names:
        card_path = card_image_paths.get(card_name)
        if card_path:
            try:
                card_image = Image.open(card_path)
                cards.append(card_image)
            except FileNotFoundError:
                print(f"Image for {card_name} not found.")
                continue

    if not cards:
        return None

    widths, heights = zip(*(card.size for card in cards))
    total_width = sum(widths)
    max_height = max(heights)

    new_image = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for card in cards:
        new_image.paste(card, (x_offset, 0))
        x_offset += card.width

    return new_image

# Function to deal a random card
def deal_card():
    valid_cards = [card for card in card_image_paths.keys() if card != 'back_of_card']
    return random.choice(valid_cards)

# Function to check if the dealer has blackjack
def dealer_has_blackjack(dealer_hand):
    first_card = dealer_hand[0].split(' ')[0]
    second_card = dealer_hand[1].split(' ')[0]
    
    blackjack_cards = ['10', 'Jack', 'Queen', 'King']
    
    if first_card == 'Ace' and second_card in blackjack_cards:
        return True
    if first_card in blackjack_cards and second_card == 'Ace':
        return True
    
    return False

# Function to calculate hand total
def calculate_hand(hand):
    total = 0
    aces = 0
    for card in hand:
        value = card.split(' ')[0]
        if value in ['Jack', 'Queen', 'King']:
            total += 10
        elif value == 'Ace':
            total += 11
            aces += 1
        else:
            total += int(value)

    while total > 21 and aces:
        total -= 10
        aces -= 1

    is_soft = aces > 0 and total <= 21
    return total, is_soft

# Blackjack command
@interactions.slash_command(
    name="blackjack",
    description="Play a game of blackjack",
    scopes=[1288166371477160057]  # Replace with your guild ID
)
@interactions.slash_option(
    name="bet",
    description="Enter the amount you want to bet",
    opt_type=interactions.OptionType.INTEGER,
    required=True
)
async def blackjack(ctx: SlashContext, bet: int):
    user_id = str(ctx.author.id)

    # Define the maximum bet
    max_bet = 10000

    # Ensure the bet does not exceed the maximum bet
    if bet > max_bet:
        await ctx.send(f"{ctx.author.username}, the maximum bet is {max_bet} currency. Please place a lower bet.")
        return
    
    # Ensure user has enough currency to bet
    if user_id not in currency or currency[user_id] < bet:
        await ctx.send(f"{ctx.author.username}, you don't have enough currency to make that bet!")
        return

    # Track the wagered amount
    if user_id not in wager_data:
        wager_data[user_id] = 0
    wager_data[user_id] += bet
    save_total_wagers(wager_data)  # Save the updated wagered amount

    # Deduct the bet from user's balance
    currency[user_id] -= bet
    save_currency()

    # Deal initial hands
    player_hand = [deal_card(), deal_card()]
    dealer_hand = [deal_card(), deal_card()]

    # Store game state
    game_states[user_id] = {
        'player_hand': player_hand,
        'dealer_hand': dealer_hand,
        'bet': bet,
        'doubled_down': False,
        'has_split': False,
        'split_hands': [],
        'active_hand': 0,  # Tracks which hand is currently being played
        'has_hit': False   # Add this flag to track whether the player has hit
    }

    # Calculate player's hand total
    player_total, is_soft = calculate_hand(player_hand)
    dealer_blackjack = dealer_has_blackjack(dealer_hand)

    # Prepare player hand embed with text and image
    player_embed = interactions.Embed(
        title="Your Hand",
        description=f"Total: {player_total} (soft)" if is_soft else f"Total: {player_total}",
        color=0x2f3136
    )
    
    combined_image = combine_cards(player_hand)
    if combined_image:
        combined_image_path = "player_hand.png"
        combined_image.save(combined_image_path)
        player_embed.set_image(url=f"attachment://{combined_image_path}")
        await ctx.send(embeds=player_embed, files=interactions.File(combined_image_path))
        safe_remove_file(combined_image_path)

    # Prepare dealer hand embed with text and image (face-up card only)
    dealer_embed = interactions.Embed(
        title="Dealer's Hand",
        description="Showing one card...",
        color=0x2f3136
    )
    
    dealer_initial_hand = combine_cards([dealer_hand[0], 'back_of_card'])
    if dealer_initial_hand:
        dealer_initial_hand_path = "dealer_initial_hand.png"
        dealer_initial_hand.save(dealer_initial_hand_path)
        dealer_embed.set_image(url=f"attachment://{dealer_initial_hand_path}")
        await ctx.send(embeds=dealer_embed, files=interactions.File(dealer_initial_hand_path))
        safe_remove_file(dealer_initial_hand_path)

    # Check for dealer's blackjack
    if dealer_blackjack:
        if player_total == 21:
            # Reveal dealer's full hand (push case)
            dealer_full_hand_embed = interactions.Embed(
                title="Dealer's Hand",
                description="It's a push! Both you and the dealer have blackjack.",
                color=0x2f3136
            )
            combined_image = combine_cards(dealer_hand)
            if combined_image:
                combined_image_path = "dealer_blackjack_hand.png"
                combined_image.save(combined_image_path)
                dealer_full_hand_embed.set_image(url=f"attachment://{combined_image_path}")
                await ctx.send(embeds=dealer_full_hand_embed, files=interactions.File(combined_image_path))
                safe_remove_file(combined_image_path)
            
            # Refund the player's bet
            currency[user_id] += bet
            save_currency()
        else:
             # Reveal dealer's full hand (dealer wins case)
            dealer_full_hand_embed = interactions.Embed(
                title="Dealer's Hand",
                description="Dealer has blackjack!",
                color=0x2f3136
            )
            combined_image = combine_cards(dealer_hand)
            if combined_image:
                combined_image_path = "dealer_blackjack_hand.png"
                combined_image.save(combined_image_path)
                dealer_full_hand_embed.set_image(url=f"attachment://{combined_image_path}")
                await ctx.send(embeds=dealer_full_hand_embed, files=interactions.File(combined_image_path))
                safe_remove_file(combined_image_path)

            await ctx.send(f"Dealer has blackjack! You lose {bet} currency.")
            save_currency()

        # Stop the game if dealer has blackjack
        game_states.pop(user_id)
        return  # Game ends immediately

    # Player actions if no dealer blackjack
    if player_total == 21:
        winnings = int(bet * 1.5)
        currency[user_id] += winnings
        save_currency()
        await ctx.send(f"Blackjack! 3:2 payout! You win {winnings} currency! Your updated balance is {currency[user_id]} currency.")
        return

    await ctx.send("Type `/hit` to take another card, `/stand` to hold your hand, `/double_down` to double your bet, or `/split` to split your hand (if applicable).")


# Hit command
@interactions.slash_command(
    name="hit",
    description="Take another card",
    scopes=[1288166371477160057]
)
async def hit(ctx: SlashContext):
    user_id = str(ctx.author.id)

    if user_id not in game_states:
        await ctx.send("You don't have an ongoing game. Start one with `/blackjack`.")
        return

    game = game_states[user_id]
    
    # Check if the player is playing a split hand
    if game['has_split']:
        current_hand = game['split_hands'][game['active_hand']]
    else:
        current_hand = game['player_hand']

    # Deal a new card and update the hand
    new_card = deal_card()
    current_hand.append(new_card)

    # Mark that the player has hit
    game['has_hit'] = True

    player_total, is_soft = calculate_hand(current_hand)

    # Display the updated hand
    player_embed = interactions.Embed(
        title="Your Hand", 
        description=f"Total: {player_total} (soft)" if is_soft else f"Total: {player_total}",
        color=0x2f3136
    )

    # Combine and send the updated hand
    combined_image = combine_cards(current_hand)
    if combined_image:
        combined_image_path = f"updated_hand_{game['active_hand'] if game['has_split'] else 'player'}.png"
        combined_image.save(combined_image_path)
        player_embed.set_image(url="attachment://" + combined_image_path)
        await ctx.send(embed=player_embed, file=interactions.File(combined_image_path))
        safe_remove_file(combined_image_path)

    # Check if the player has busted
    if player_total > 21:
        await ctx.send(f"You busted with a total of {player_total}.")
        if game['has_split']:
            # Move to the next hand if it's a split hand
            game['active_hand'] += 1
            await play_split_hand(ctx)
        else:
            await dealer_turn(ctx, True)
    else:
        await ctx.send("Type `/hit` to take another card or `/stand` to hold your hand.")



# Stand command
@interactions.slash_command(
    name="stand",
    description="Hold your hand",
    scopes=[1288166371477160057]
)
async def stand(ctx: SlashContext):
    user_id = str(ctx.author.id)

    if user_id not in game_states:
        await ctx.send("You don't have an ongoing game. Start one with `/blackjack`.")
        return

    game = game_states[user_id]

    if game['has_split']:
        # If playing split hands, move to the next hand
        game['active_hand'] += 1
        await play_split_hand(ctx)
    else:
        # If not a split hand, move to dealer's turn
        await dealer_turn(ctx)


# Double down command
@interactions.slash_command(
    name="double_down",
    description="Double your bet and take one final card",
    scopes=[1288166371477160057]
)
async def double_down(ctx: SlashContext):
    user_id = str(ctx.author.id)

    if user_id not in game_states:
        await ctx.send("You don't have an ongoing game. Start one with `/blackjack`.")
        return

    game = game_states[user_id]

    # Prevent doubling down after a hit
    if game['has_hit']:
        await ctx.send("You can't double down after hitting.")
        return

    if game['has_split']:
        await ctx.send("You cannot double down on a split hand.")
        return

    if game['doubled_down']:
        await ctx.send("You have already doubled down.")
        return

    original_bet = game['bet']

    # Ensure the player has enough currency to double the bet
    if currency[user_id] < original_bet:
        await ctx.send(f"{ctx.author.name}, you don't have enough currency to double your bet.")
        return

    # Track the additional wager for double down
    wager_data[user_id] += original_bet
    save_total_wagers(wager_data)

    currency[user_id] -= original_bet
    game['bet'] += original_bet
    game['doubled_down'] = True

    # Deal one more card
    new_card = deal_card()
    game['player_hand'].append(new_card)

    # Calculate the player's hand total
    player_total, is_soft = calculate_hand(game['player_hand'])

    # Create an embed message with the updated hand
    player_embed = interactions.Embed(
        title="Your Hand", 
        description=f"Total: {player_total} (soft)" if is_soft else f"Total: {player_total}",
        color=0x2f3136
    )

    # Combine player's cards and send the embed
    combined_image = combine_cards(game['player_hand'])
    if combined_image:
        combined_image_path = "doubled_down_hand.png"
        combined_image.save(combined_image_path)
        player_embed.set_image(url="attachment://" + combined_image_path)
        await ctx.send(embed=player_embed, file=interactions.File(combined_image_path))
        safe_remove_file(combined_image_path)

    # Check if the player has busted
    if player_total > 21:
        await dealer_turn(ctx, True)
    else:
        await dealer_turn(ctx)



# Split command
@interactions.slash_command(
    name="split",
    description="Split your hand into two hands",
    scopes=[1288166371477160057]
)
async def split(ctx: SlashContext):
    user_id = str(ctx.author.id)

    if user_id not in game_states:
        await ctx.send("You don't have an ongoing game. Start one with `/blackjack`.")
        return

    game = game_states[user_id]

    # Prevent splitting after a hit
    if game['has_hit']:
        await ctx.send("You can't split after hitting.")
        return

    # Prevent splitting more than once
    if game['has_split']:
        await ctx.send("You can only split once per game.")
        return

    player_hand = game['player_hand']

    # Ensure the hand can be split
    if len(player_hand) != 2 or player_hand[0].split(' ')[0] != player_hand[1].split(' ')[0]:
        await ctx.send("You can only split if you have two cards of the same rank.")
        return

    # Ensure the player has enough currency to split
    if currency[user_id] < game['bet']:
        await ctx.send(f"{ctx.author.name}, you don't have enough currency to split.")
        return

    # Track the additional wager for splitting
    wager_data[user_id] += game['bet']
    save_total_wagers(wager_data)

    currency[user_id] -= game['bet']

    # Split the hand into two hands
    hand_1 = [player_hand[0], deal_card()]
    hand_2 = [player_hand[1], deal_card()]

    game['has_split'] = True
    game['split_hands'] = [hand_1, hand_2]
    game['active_hand'] = 0

    await ctx.send("Your hand has been split! You will now play each hand separately.")
    await play_split_hand(ctx)

async def play_split_hand(ctx: SlashContext):
    user_id = str(ctx.author.id)
    game = game_states[user_id]
    active_hand = game['active_hand']

    if active_hand < len(game['split_hands']):
        # Play the current active hand
        current_hand = game['split_hands'][active_hand]
        player_total, is_soft = calculate_hand(current_hand)

        # Display the current hand
        player_embed = interactions.Embed(
            title=f"Your Hand (Hand {active_hand + 1})", 
            description=f"Total: {player_total} (soft)" if is_soft else f"Total: {player_total}",
            color=0x2f3136
        )

        # Combine the current hand's cards and send the embed
        combined_image = combine_cards(current_hand)
        if combined_image:
            combined_image_path = f"split_hand_{active_hand}.png"
            combined_image.save(combined_image_path)
            player_embed.set_image(url="attachment://" + combined_image_path)
            await ctx.send(embed=player_embed, file=interactions.File(combined_image_path))
            safe_remove_file(combined_image_path)

        # Allow player to hit or stand on the current hand
        await ctx.send("Type `/hit` to take another card or `/stand` to hold your hand.")
    else:
        # If no more hands to play, proceed to dealer's turn
        await dealer_turn(ctx)



async def dealer_turn(ctx: SlashContext, player_busted=False):
    user_id = str(ctx.author.id)
    game = game_states.get(user_id)
    if not game:
        return

    dealer_hand = game['dealer_hand']
    dealer_total, _ = calculate_hand(dealer_hand)  # Extract total, ignore is_soft

    # If the player hasn't busted, the dealer needs to play
    if not player_busted:
        # Dealer hits until reaching at least 17
        while dealer_total < 17:
            new_card = deal_card()
            dealer_hand.append(new_card)
            dealer_total, _ = calculate_hand(dealer_hand)  # Recalculate total

    # Combine dealer's final hand into an image
    combined_image = combine_cards(dealer_hand)
    combined_image_path = "dealer_final_hand.png"
    if combined_image:
        combined_image.save(combined_image_path)

    # Show dealer's final hand
    dealer_embed = interactions.Embed(
        title="Dealer's Hand",
        description=f"Total: {dealer_total}",
        color=0x2f3136
    )
    dealer_embed.set_image(url=f"attachment://{combined_image_path}")
    await ctx.send(embeds=dealer_embed, files=interactions.File(combined_image_path))
    safe_remove_file(combined_image_path)

    # Now process the outcome
    if game['has_split']:
        # Handle split hands
        for hand_index, hand in enumerate(game['split_hands']):
            player_total, _ = calculate_hand(hand)
            await process_outcome(ctx, user_id, player_total, dealer_total, hand_index + 1)
    else:
        # Single hand outcome
        player_total, _ = calculate_hand(game['player_hand'])
        await process_outcome(ctx, user_id, player_total, dealer_total)

    # Cleanup the game state after the game ends
    game_states.pop(user_id)


async def process_outcome(ctx, user_id, player_total, dealer_total, hand_number=None):
    bet = game_states[user_id]['bet']
    dealer_bust = dealer_total > 21
    current_balance = currency[user_id]

    if hand_number:
        hand_label = f"Hand {hand_number}"
    else:
        hand_label = "Your hand"

    if player_total > 21:
        # Player busts
        await ctx.send(f"{hand_label} busted. You lose {bet} currency.")
    elif dealer_bust:
        # Dealer busts, player wins
        winnings = bet * 2
        currency[user_id] += winnings
        new_balance = currency[user_id]
        await ctx.send(f"Dealer busts! {hand_label} wins {winnings} currency! Your new balance is {new_balance}.")
    elif player_total > dealer_total:
        # Player wins
        winnings = bet * 2
        currency[user_id] += winnings
        new_balance = currency[user_id]
        await ctx.send(f"{hand_label} wins {winnings} currency! Dealer had {dealer_total}. Your new balance is {new_balance}.")
    elif player_total < dealer_total:
        # Dealer wins
        new_balance = currency[user_id]
        await ctx.send(f"{hand_label} loses. Dealer had {dealer_total}. You lost {bet} currency. Your new balance is {new_balance}.")
    else:
        # Draw
        currency[user_id] += bet
        new_balance = currency[user_id]
        await ctx.send(f"{hand_label} draws! You get your bet of {bet} currency back. Your new balance is {new_balance}.")

    save_currency()





import asyncio

# Dictionary to map prizes to their corresponding image paths
prize_images = {
    "Old Cloth": "old_cloth.png",
    "Spider Silk": "spider_silk.png",
    "Troll Pelt": "troll_pelt.png",
    "Gold Coin Bag": "gold_coin_bag.png",
    "Golden Key": "golden_key.png",
    "Frozen Key": "frozen_key.png",
    "Skull Key": "skull_key.png"
}

@interactions.slash_command(
    name="mystery_box",
    description="Open a Marvelous Chest for a chance to win valuable items",
    scopes=[1288166371477160057]  # Replace with your guild ID
)
async def mystery_box(ctx: SlashContext):
    user_id = str(ctx.author.id)
    chest_price = 5000  # Set to 5000 currency

    # Check if the user has enough currency
    if user_id not in currency or currency[user_id] < chest_price:
        await ctx.send(f"{ctx.author.username}, you don't have enough currency to open the Marvelous Chest!")
        return

    # Send a confirmation message asking if the player wants to proceed
    await ctx.send(f"The Marvelous Chest costs {chest_price} currency. Do you want to proceed?", components=[
        interactions.Button(style=interactions.ButtonStyle.PRIMARY, label="Confirm", custom_id="confirm_purchase"),
        interactions.Button(style=interactions.ButtonStyle.DANGER, label="Cancel", custom_id="cancel_purchase")
    ])

# Listener for the button click to confirm the purchase
@interactions.component_callback("confirm_purchase")
async def confirm_purchase(ctx: interactions.ComponentContext):
    user_id = str(ctx.author.id)
    chest_price = 5000  # Set to 5000 currency

    # Check again if the user has enough currency (in case it changed since the confirmation)
    if user_id not in currency or currency[user_id] < chest_price:
        await ctx.send(f"{ctx.author.username}, you no longer have enough currency to open the Marvelous Chest!")
        return

    # Deduct the cost of the chest
    currency[user_id] -= chest_price
    save_currency()

    # Display the Marvelous Chest image to start the unboxing
    chest_image = "/mnt/data/marvelous_chest.png"
    await ctx.send(f"**{ctx.author.username}** is opening the Marvelous Chest...", file=interactions.File(chest_image))

    # Add suspense with delays
    await asyncio.sleep(2)  # Delay before next message
    await ctx.send(f"The chest slowly creaks open...")
    await asyncio.sleep(2)  # Additional delay for suspense

    # Define the prize pool (without image paths, since we're using the dictionary)
    prize_pool = [
        ('Old Cloth', 1),                     # 60% chance
        ('Spider Silk', 950),                 # 20% chance
        ('Troll Pelt', 4500),                 # 10% chance
        ('Gold Coin Bag', 7000),              # 5% chance
        ('Golden Key', 8800),                 # 3% chance
        ('Frozen Key', 35200),                # 1.5% chance
        ('Skull Key', 61600)                  # 0.5% chance
    ]

    prize_weights = [
        60,   # Old Cloth
        20,   # Spider Silk
        10,   # Troll Pelt
        5,    # Gold Coin Bag
        3,    # Golden Key
        1.5,  # Frozen Key
        0.5   # Skull Key
    ]

    # Unbox a prize (weighted random selection)
    def weighted_choice(choices, weights):
        total = sum(weights)
        r = random.uniform(0, total)
        upto = 0
        for i, weight in enumerate(weights):
            if upto + weight >= r:
                return choices[i]
            upto += weight

    # Unbox the prize and get the prize name and value
    prize_name, prize_value = weighted_choice(prize_pool, prize_weights)

    # Credit the user with the prize value
    currency[user_id] += prize_value
    save_currency()

    # Final suspense before revealing the prize
    await asyncio.sleep(3)  # Final delay
    await ctx.send(f"**{ctx.author.username}** the chest is opening...")

    # Retrieve the image for the prize from the dictionary
    prize_image = prize_images.get(prize_name)

    # Send the prize message with the prize image
    if prize_image:
        await ctx.send(f"**{ctx.author.username}** opens the Marvelous Chest...\nA mystical glow fills the room...\n**You have unboxed: {prize_name}!**\nYou have been credited {prize_value} currency.", file=interactions.File(prize_image))
    else:
        await ctx.send(f"**{ctx.author.username}** opens the Marvelous Chest...\nA mystical glow fills the room...\n**You have unboxed: {prize_name}!**\nYou have been credited {prize_value} currency.")

    # Optionally, track the total wagered in the Marvelous Chest
    if user_id not in wager_data:
        wager_data[user_id] = 0
    wager_data[user_id] += chest_price
    save_total_wagers(wager_data)

# Listener for the button click to cancel the purchase
@interactions.component_callback("cancel_purchase")
async def cancel_purchase(ctx: interactions.ComponentContext):
    await ctx.send("Purchase canceled.")















house_profit = 0  # To track total house profit
house_edge = 0.02  # House edge of 2%

# Slash Command for Coinflip
coinflip_battles = {}

@interactions.slash_command(
    name="coinflip",
    description="Start a coinflip game",
    scopes=[1288166371477160057]
)
@interactions.slash_option(
    name="bet",
    description="Enter the amount you want to bet",
    opt_type=interactions.OptionType.INTEGER,
    required=True
)
@interactions.slash_option(
    name="choice",
    description="Choose heads or tails",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=[
        {"name": "Heads", "value": "heads"},
        {"name": "Tails", "value": "tails"}
    ]
)
async def coinflip(ctx: interactions.SlashContext, bet: int, choice: str):
    user_id = str(ctx.author.id)

    if user_id not in currency or currency[user_id] < bet:
        await ctx.send(f"{ctx.author.username}, you don't have enough currency to make that bet!")
        return

    # Deduct the bet amount
    currency[user_id] -= bet
    save_currency()

    # Track the wagered amount for the user
    if user_id not in wager_data:
        wager_data[user_id] = 0
    wager_data[user_id] += bet  # Add the bet to the player's total wagers
    save_total_wagers(wager_data)  # Save the wager data

    coinflip_battles[user_id] = {
        'player1': ctx.author,
        'bet': bet,
        'choice': choice
    }

    await ctx.send(f"{ctx.author.username} started a coinflip with a bet of {bet} currency and chose {choice}! Type `/join_coinflip` to join.")

# Slash Command for joining the coinflip
@interactions.slash_command(
    name="join_coinflip",
    description="Join an ongoing coinflip game",
    scopes=[1288166371477160057]
)
@interactions.slash_option(
    name="opponent",
    description="The user who started the coinflip game",
    opt_type=interactions.OptionType.USER,
    required=True
)
async def join_coinflip(ctx: interactions.SlashContext, opponent: interactions.User):
    opponent_id = str(opponent.id)
    user_id = str(ctx.author.id)

    # Check if the user is trying to join their own game
    if user_id == opponent_id:
        await ctx.send("You can't join your own coinflip game!")
        return

    if opponent_id not in coinflip_battles:
        await ctx.send(f"{opponent.username} doesn't have an ongoing coinflip game.")
        return

    bet = coinflip_battles[opponent_id]['bet']
    if user_id not in currency or currency[user_id] < bet:
        await ctx.send(f"{ctx.author.username}, you don't have enough currency to join the game!")
        return

    # Deduct the bet amount
    currency[user_id] -= bet
    save_currency()

    # Track the wagered amount for the user
    if user_id not in wager_data:
        wager_data[user_id] = 0
    wager_data[user_id] += bet  # Add the bet to the player's total wagers
    save_total_wagers(wager_data)  # Save the wager data

    coinflip_battles[opponent_id]['player2'] = ctx.author

    await ctx.send(f"{ctx.author.username} joined {opponent.username}'s game! Flipping the coin...")
    await flip_coin(ctx, opponent_id)

async def flip_coin(ctx: interactions.SlashContext, opponent_id):
    battle = coinflip_battles[opponent_id]
    outcome = random.choice(["heads", "tails"])
    creator_choice = battle['choice']
    winner = battle['player1'] if outcome == creator_choice else battle['player2']

    total_bet = battle['bet'] * 2

    house_cut = int(total_bet * house_edge)  # Calculate house profit

    # Add the house cut to the house's profit
    global house_profit
    house_profit += house_cut

    # Calculate winnings after the house cut
    winnings = total_bet - house_cut

    # Add the winnings to the winner's currency
    currency[str(winner.id)] += winnings
    save_currency()

    image_path = f"{outcome}.png"
    await ctx.send(f"The coin landed on **{outcome}**!", file=interactions.File(image_path))
    await ctx.send(f"{winner.username} wins {winnings} currency after a 2% fees!")
    del coinflip_battles[opponent_id]

# Slash Command for checking house profit
@interactions.slash_command(
    name="house_profit",
    description="Check how much profit the house has earned",
    scopes=[1288166371477160057]
)
async def house_profit_command(ctx: interactions.SlashContext):
    await ctx.send(f"The house has earned {house_profit} currency in total profits.")

# Start the bot
bot.start()


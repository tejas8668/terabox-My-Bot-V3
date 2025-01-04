import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import urllib.parse

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token and channel ID from environment variables
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# In-memory storage for user tracking
users = set()

# Define the /start command handler
async def start(update: Update, context: CallbackContext) -> None:
    logger.info("Received /start command")
    user = update.effective_user

    # Add user to the set
    users.add(user.id)

    message = (
        f"New user started the bot:\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username}\n"
        f"User ID: {user.id}"
    )
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
    await update.message.reply_photo(
        photo='https://ik.imagekit.io/dvnhxw9vq/unnamed.png?updatedAt=1735280750258',  # Replace with your image URL
        caption=(
            "👋 **ℍ𝕖𝕝𝕝𝕠 𝔻𝕖𝕒𝕣!**\n\n"
            "SEND ME ANY TERABOX LINK, I WILL SEND YOU DIRECT STREAM LINK WITHOUT TERABOX LOGIN OR ANY ADS​\n\n"
            "**𝐈𝐦𝐩𝐨𝐫𝐭𝐚𝐧𝐭​​**\n\n"
            "𝗨𝘀𝗲 𝗖𝗵𝗿𝗼𝗺𝗲 𝗙𝗼𝗿 𝗔𝗰𝗰𝗲𝘀𝘀 𝗠𝘆 𝗔𝗹𝗹 𝗳𝗲𝗮𝘁𝘂𝗿𝗲𝘀"
        ),
        parse_mode='Markdown'
    )

# Define the /users command handler
async def users_count(update: Update, context: CallbackContext) -> None:
    logger.info("Received /users command")
    user_count = len(users)
    await update.message.reply_text(f"Total users who have interacted with the bot: {user_count}")

# Define the link handler
async def handle_link(update: Update, context: CallbackContext) -> None:
    logger.info("Received message: %s", update.message.text)
    user = update.effective_user

    # Add user to the set
    users.add(user.id)

    original_link = update.message.text

    # Check if the message contains an http or https link
    if 'http://' in original_link or 'https://' in original_link:
        parsed_link = urllib.parse.quote(original_link, safe='')
        modified_link = f"https://streamterabox.blogspot.com/?q={parsed_link}&m=0"
        modified_url = f"https://streamterabox.blogspot.com/2024/12/terabox-player.html?q={parsed_link}"

        # Create a button with the modified link
        button = [
            [InlineKeyboardButton("Stream Server 1", url=modified_link)],
            [InlineKeyboardButton("Stream Server 2", url=modified_url)]
        ]
        reply_markup = InlineKeyboardMarkup(button)

        # Send the user's details and message to the channel
        user_message = (
            f"User message:\n"
            f"Name: {user.full_name}\n"
            f"Username: @{user.username}\n"
            f"User ID: {user.id}\n"
            f"Message: {original_link}"
        )
        await context.bot.send_message(chat_id=CHANNEL_ID, text=user_message)

        # Send the message with the link, copyable link, and button
        await update.message.reply_text(
            f"👇👇 YOUR VIDEO LINK IS READY, USE THESE SERVERS 👇👇\n\n♥ 👇Your Stream Link👇 ♥\n",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("Please send Me Only TeraBox Link.")

# Define the /broadcast command handler
async def broadcast(update: Update, context: CallbackContext) -> None:
    logger.info("Received /broadcast command")
    message = update.message.reply_to_message

    if message:
        total_users = len(users)
        sent_count = 0
        block_count = 0
        fail_count = 0

        for user_id in users:
            try:
                await context.bot.send_message(chat_id=user_id, text=message.text)
                sent_count += 1
            except Exception as e:
                if 'blocked' in str(e):
                    block_count += 1
                else:
                    fail_count += 1

        await update.message.reply_text(
            f"Broadcast completed!\n\n"
            f"Total users: {total_users}\n"
            f"Messages sent: {sent_count}\n"
            f"Users blocked the bot: {block_count}\n"
            f"Failed to send messages: {fail_count}"
        )
    else:
        await update.message.reply_text("Please reply to a message with /broadcast to send it to all users.")

def main() -> None:
    # Get the port from the environment variable or use default
    port = int(os.environ.get('PORT', 8080))  # Default to port 8080
    webhook_url = f"https://total-jessalyn-toxiccdeveloperr-36046375.koyeb.app/{TOKEN}"  # Replace with your server URL

    # Create the Application and pass it your bot's token
    app = ApplicationBuilder().token(TOKEN).build()

    # Register the /start command handler
    app.add_handler(CommandHandler("start", start))

    # Register the /users command handler
    app.add_handler(CommandHandler("users", users_count))

    # Register the link handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    # Register the /broadcast command handler
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Run the bot using a webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    main()

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import urllib.parse
from pymongo import MongoClient
from datetime import datetime, timedelta
import requests

# Add this at the top of the file
VERIFICATION_REQUIRED = os.getenv('VERIFICATION_REQUIRED', 'false').lower() == 'true'

admin_ids = [6025969005, 6018060368]

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')  # Get MongoDB URI from environment variables
client = MongoClient(MONGO_URI)
db = client['terabox_bot']
users_collection = db['users']

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token and channel ID from environment variables
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Define the /start command handler
async def start(update: Update, context: CallbackContext) -> None:
    logger.info("Received /start command")
    user = update.effective_user

    # Check if the start command includes a token (for verification)
    if context.args:
        text = update.message.text
        if text.startswith("/start terabox-"):
            await handle_terabox_link(update, context)
            return
        token = context.args[0]
        user_data = users_collection.find_one({"user_id": user.id, "token": token})

        if user_data:
            # Update the user's verification status
            users_collection.update_one(
                {"user_id": user.id},
                {"$set": {"verified_until": datetime.now() + timedelta(days=1)}},
                upsert=True
            )
            await update.message.reply_text(
                "✅ **Verification Successful!**\n\n"
                "You can now use the bot for the next 24 hours without any ads or restrictions.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ **Invalid Token!**\n\n"
                "Please try verifying again.",
                parse_mode='Markdown'
            )
        return

    # If no token, send the welcome message and store user ID in MongoDB
    users_collection.update_one(
        {"user_id": user.id},
        {"$set": {"username": user.username, "full_name": user.full_name}},
        upsert=True
    )
    message = (
        f"New user started the bot:\n"
        f"Name: {user.full_name}\n"
        f"Username: @{user.username}\n"
        f"User   ID: {user.id}"
    )
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
    # Corrected photo URL
    photo_url = 'https://ik.imagekit.io/dvnhxw9vq/unnamed.png?updatedAt=1735280750258'
    await update.message.reply_photo(
        photo=photo_url,
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
    if update.effective_user.id in admin_ids:
        # Count the number of users in the MongoDB collection
        user_count = users_collection.count_documents({})
        await update.message.reply_text(f"Total users who have interacted with the bot: {user_count}")
    else:
        await update.message.reply_text("You Have No Rights To Use My Commands")

async def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in admin_ids:
        try:
            # Get total users
            total_users = users_collection.count_documents({})

            # Get MongoDB database stats
            db_stats = db.command("dbstats")

            # Calculate used storage
            used_storage_mb = db_stats['dataSize'] / (1024 ** 2)  # Convert bytes to MB

            # Calculate total and free storage (if available)
            if 'fsTotalSize' in db_stats:
                total_storage_mb = db_stats['fsTotalSize'] / (1024 ** 2)  # Convert bytes to MB
                free_storage_mb = total_storage_mb - used_storage_mb
            else:
                total_storage_in_mb = 512

                # Calculate free storage
                free_storage_in_mb = total_storage_in_mb - used_storage_mb
                # Fallback for environments where fsTotalSize is not available
                total_storage_mb = "N/A"
                free_storage_mb = free_storage_in_mb

            # Prepare the response message
            message = (
                f"📊 **Bot Statistics**\n\n"
                f"👥 **Total Users:** {total_users}\n"
                f"💾 **MongoDB Used Storage:** {used_storage_mb:.2f} MB\n"
                f"🆓 **MongoDB Free Storage:** {free_storage_mb if isinstance(free_storage_mb, str) else f'{free_storage_mb:.2f} MB'}\n"
            )

            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            await update.message.reply_text("❌ An error occurred while fetching stats.")
    else:
        await update.message.reply_text("You Have No Rights To Use My Commands")

async def handle_link(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    # Check if user is admin
    if user.id in admin_ids:
        # Admin ko verify karne ki zaroorat na ho
        pass
    else:
        # User ko verify karne ki zaroorat hai
        if VERIFICATION_REQUIRED and not await check_verification(user.id):
            # User ko verify karne ki zaroorat hai
            btn = [
                [InlineKeyboardButton("Verify", url=await get_token(user.id, context.bot.username))],
                [InlineKeyboardButton("How To Open Link & Verify", url="https://t.me/how_to_download_0011")]
            ]
            await update.message.reply_text(
                text="🚨 <b>Token Expired!</b>\n\n"
                     "<b>Timeout: 24 hours</b>\n\n"
                     "Your access token has expired. Verify it to continue using the bot!\n\n"
                     "<b>🔑 Why Tokens?</b>\n\n"
                     "Tokens unlock premium features with a quick ad process. Enjoy 24 hours of uninterrupted access! 🌟\n\n"
                     "<b>👉 Tap below to verify your token.</b>\n\n"
                     "Thank you for your support! ❤️",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return

    # Check if user sent a link
    if update.message.text.startswith('http://') or update.message.text.startswith('https://'):
        # User sent a link
        original_link = update.message.text
        parsed_link = urllib.parse.quote(original_link, safe='')
        modified_link = f"https://terabox-player-one.vercel.app/?url=https://www.terabox.tech/play.html?url={parsed_link}"
        modified_url = f"https://terabox-player-one.vercel.app/?url=https://www.terabox.tech/play.html?url={parsed_link}"

        # Create a button with the modified link
        button = [
            [InlineKeyboardButton("Stream Server 1", url=modified_link)],
            [InlineKeyboardButton("Stream Server 2", url=modified_url)]
        ]
        reply_markup = InlineKeyboardMarkup(button)

        # Send the user's details and message to the channel
        user_message = (
            f"User   message:\n"
            f"Name: {update.effective_user.full_name}\n"
            f"Username: @{update.effective_user.username}\n"
            f"User   ID: {update.effective_user.id}\n"
            f"Message: {original_link}"
        )
        await context.bot.send_message(chat_id=os.getenv('CHANNEL_ID'), text=user_message)

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
    if update.effective_user.id in admin_ids:
        message = update.message.reply_to_message
        if message:
            # Fetch all user IDs from MongoDB
            all_users = users_collection.find({}, {"user_id": 1})
            total_users = users_collection.count_documents({})
            sent_count = 0
            block_count = 0
            fail_count = 0

            for user_data in all_users:
                user_id = user_data['user_id']
                try:
                    if message.photo:
                        await context.bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=message.caption)
                    elif message.video:
                        await context.bot.send_video(chat_id=user_id, video=message.video.file_id, caption=message.caption)
                    else:
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
    else:
        await update.message.reply_text("You Have No Rights To Use My Commands")


async def check_verification(user_id: int) -> bool:
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("verified_until", datetime.min) > datetime.now():
        return True
    return False

async def get_token(user_id: int, bot_username: str) -> str:
    # Generate a random token
    token = os.urandom(16).hex()
    # Update user's verification status in database
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"token": token, "verified_until": datetime.min}},  # Reset verified_until to min
        upsert=True
    )
    # Create verification link
    verification_link = f"https://telegram.me/{bot_username}?start={token}"
    # Shorten verification link using shorten_url_link function
    shortened_link = shorten_url_link(verification_link)
    return shortened_link

def shorten_url_link(url):
    api_url = 'https://clickspay.in/api'
    api_key = 'bbcbd18b768b0a22ba0081b567af29d51b45f2aa'
    params = {
        'api': api_key,
        'url': url
    }
    # Yahan pe custom certificate bundle ka path specify karo
    response = requests.get(api_url, params=params, verify=False)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            logger.info(f"Adrinolinks shortened URL: {data['shortenedUrl']}")
            return data['shortenedUrl']
    logger.error(f"Failed to shorten URL with Adrinolinks: {url}")
    return url

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Define the /userss command handler
async def userss(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in admin_ids:
        # Fetch the first 100 users
        users = list(users_collection.find({}, {"full_name": 1, "username": 1}).limit(100))

        if not users:
            await update.message.reply_text("No users found in the database.")
            return

        # Prepare the message with user details
        message = ""
        for i, user in enumerate(users):
            name = user.get("full_name", "N/A")
            username = user.get("username", "N/A")
            message += f"<b>Name:</b> {name}\n"
            message += f"<b>Username:</b> @{username}\n\n"

            # Send the message in chunks of 5 users
            if (i + 1) % 5 == 0:
                await update.message.reply_text(message, parse_mode='HTML')
                message = ""

        # Send the remaining users
        if message:
            await update.message.reply_text(message, parse_mode='HTML')

        # Display the "Next" button
        keyboard = [[InlineKeyboardButton("Next", callback_data="next_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Click 'Next' to view more users", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You Have No Rights To Use My Commands")

async def next_users(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Fetch the next 100 users
    users = list(users_collection.find({}, {"full_name": 1, "username": 1}).skip(100).limit(100))

    if not users:
        await query.edit_message_text("No more users found in the database.")
        return

    # Prepare the message with user details
    message = ""
    for i, user in enumerate(users):
        name = user.get("full_name", "N/A")
        username = user.get("username", "N/A")
        message += f"<b>Name:</b> {name}\n"
        message += f"<b>Username:</b> @{username}\n\n"

        # Send the message in chunks of 5 users
        if (i + 1) % 5 == 0:
            await query.edit_message_text(message, parse_mode='HTML')
            message = ""

    # Send the remaining users
    if message:
        await query.edit_message_text(message, parse_mode='HTML')

    # Display the "Next" button
    keyboard = [[InlineKeyboardButton("Next", callback_data="next_users")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Click 'Next' to view more users", reply_markup=reply_markup)
    
async def handle_terabox_link(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text.startswith("/start terabox-"):
        link_text = text.replace("/start terabox-", "")
        link = f"https://terabox.com/s/{link_text}"
        linkb = f"https://terafileshare.com/s/{link_text}"
        slink = f"https://terabox-player-one.vercel.app/?url=https://www.terabox.tech/play.html?url={link}"
        slinkb = f"https://terabox-player-one.vercel.app/?url=https://www.terabox.tech/play.html?url={linkb}"

        button = [
            [InlineKeyboardButton("Stream Server 1", url=slink)],
            [InlineKeyboardButton("Stream Server 2", url=slinkb)]
        ]
        reply_markup = InlineKeyboardMarkup(button)

        await update.message.reply_text(
            f"👇👇 YOUR VIDEO LINK IS READY, USE THESE SERVERS 👇👇\n\n♥ 👇Your Stream Link👇 ♥\n",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
def main() -> None:
    # Get the port from the environment variable or use default
    port = int(os.environ.get('PORT', 8080))  # Default to port 8080
    webhook_url = f"https://accurate-cordula-imdb07-87daeb39.koyeb.app/{TOKEN}"  # Replace with your server URL

    # Create the Application and pass it your bot's token
    app = ApplicationBuilder().token(TOKEN).build()

    # Register the /start command handler
    app.add_handler(CommandHandler("start", start))

    # Register the /users command handler
    app.add_handler(CommandHandler("totalusers", users_count))

    # Register the /userss command handler
    app.add_handler(CommandHandler("users", userss))

    # Register the /stats command handler
    app.add_handler(CommandHandler("stats", stats))

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

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')

# Verify environment variables
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in .env file")
if not SERVICE_ACCOUNT_FILE:
    raise ValueError("No GOOGLE_APPLICATION_CREDENTIALS found in .env file")
if not SPREADSHEET_ID:
    raise ValueError("No GOOGLE_SHEETS_SPREADSHEET_ID found in .env file")

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
RANGE_NAME = 'Sheet1!A2:F'  # Includes the Image URLs column

# Client's WhatsApp number
WHATSAPP_NUMBER = "+60175773070"

try:
    logging.info(f"Attempting to load service account file from: {SERVICE_ACCOUNT_FILE}")
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    logging.info(f"Successfully loaded credentials for service account: {creds.service_account_email}")
    sheets_service = build('sheets', 'v4', credentials=creds)
    logging.info("Successfully built Google Sheets service")
except Exception as e:
    logging.error(f"Error setting up Google Sheets: {str(e)}")
    raise

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Property Agent Profile", callback_data='profile')],
        [InlineKeyboardButton("List of Properties", callback_data='properties')],
        [InlineKeyboardButton("Link to WhatsApp", callback_data='whatsapp')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_photo(
            photo=open('welcome_image.jpg', 'rb'),
            caption="Welcome to Property Azizi Bot! How can I assist you today?"
        )
    except FileNotFoundError:
        logging.warning("welcome_image.jpg not found. Sending text message instead.")
        await update.message.reply_text("Welcome to Property Azizi Bot! How can I assist you today?")
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please choose an option:", reply_markup=get_main_menu_keyboard())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'profile':
        await query.message.reply_text("Here's the Property Agent Profile: [Add profile details here]")
    elif query.data == 'properties':
        await list_properties(query, context)
    elif query.data == 'whatsapp':
        whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}"
        await query.message.reply_text(f"Click here to chat on WhatsApp: {whatsapp_link}")

    # Show the main menu again after handling the button click
    await query.message.reply_text("What else would you like to do?", reply_markup=get_main_menu_keyboard())

async def list_properties(query, context):
    try:
        logging.info(f"Attempting to fetch properties from spreadsheet: {SPREADSHEET_ID}")
        logging.info(f"Using range: {RANGE_NAME}")
        
        sheet = sheets_service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])

        logging.info(f"Fetched {len(values)} rows of data")

        if not values:
            await query.message.reply_text('No properties found.')
        else:
            for row in values:
                if len(row) >= 6:  # Ensure the row has at least 6 elements (including image URLs)
                    property_info = (
                        f"💰 Price: {row[0]}\n"
                        f"📍 Location: {row[1]}\n"
                        f"📐 Size: {row[2]}\n"
                        f"🛏️ Bedrooms: {row[3]}\n"
                        f"ℹ️ Details: {row[4]}"
                    )
                    image_urls = [url.strip() for url in row[5].split(',')]
                    
                    if image_urls:
                        media_group = [InputMediaPhoto(media=url) for url in image_urls]
                        media_group[0] = InputMediaPhoto(media=image_urls[0], caption=property_info)
                        
                        try:
                            await query.message.reply_media_group(media=media_group)
                        except Exception as img_error:
                            logging.error(f"Error sending images: {str(img_error)}")
                            await query.message.reply_text(f"{property_info}\n\nImages: {', '.join(image_urls)}")
                    else:
                        await query.message.reply_text(property_info)
                else:
                    logging.warning(f"Skipping row with insufficient data: {row}")
            
            whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}"
            await query.message.reply_text(f"These are all the available properties. Contact the agent for more information: {whatsapp_link}")
    except Exception as e:
        logging.error(f"Error fetching properties: {str(e)}")
        logging.error(f"Spreadsheet ID: {SPREADSHEET_ID}")
        logging.error(f"Range: {RANGE_NAME}")
        await query.message.reply_text("An error occurred while fetching properties. Please try again later.")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def setup_commands(application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Show the main menu")
    ]
    await application.bot.set_my_commands(commands)

async def post_init(application):
    await setup_commands(application)

def main():
    try:
        application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CallbackQueryHandler(button_click))

        application.run_polling()
    except Exception as e:
        logging.error(f"Error running the bot: {str(e)}")

if __name__ == '__main__':
    main()
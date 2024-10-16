import os
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from io import BytesIO
from PIL import Image
from telegram import Update
from flask import Flask
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import torch
from diffusers import StableDiffusionPipeline

# Use environment variables for sensitive information
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN', '8137808539:AAHLkp2A5wuJpOmeBFQMjkVRw5ySHDXF2sw')

# Flask app for port binding
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Keep-alive ping function
def ping_self():
    url = "https://testing-teligram-bots.onrender.com"  # Replace with your Render app's URL
    try:
        requests.get(url)
        print(f"Pinged {url} to keep the app alive.")
    except Exception as e:
        print(f"Failed to ping the app: {e}")

# Load the Stable Diffusion model
model_id = "CompVis/stable-diffusion-v1-4"  # Adjust if needed
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained(model_id).to(device)

# Handle the user's prompt and fetch the image
async def handle_prompt(update: Update, context):
    user_input = update.message.text
    await update.message.reply_text("Generating an image based on your prompt...")

    try:
        # Generate image using Stable Diffusion
        image = pipe(user_input).images[0]

        # Convert the image to RGB format and save as JPG
        output_path = f"image_{update.message.from_user.id}.jpg"
        image = image.convert("RGB")  # Ensure the image is in RGB format
        image.save(output_path, format='JPEG')

        with open(output_path, 'rb') as img_file:
            await context.bot.send_photo(chat_id=update.message.chat.id, photo=img_file)

        # Optional: Clean up the saved image file after sending
        os.remove(output_path)

    except Exception as e:
        print(f"Error generating image: {str(e)}")  # Log the error for debugging
        await update.message.reply_text(f"Error generating image: {str(e)}")

# Start command handler
async def start(update: Update, context):
    await update.message.reply_text("Hello! Send me a prompt, and I will generate an image in JPG format for you!")

# Run the Telegram bot
def run_telegram_bot():
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))

    application.run_polling()

if __name__ == '__main__':
    # Start the Flask server in a separate thread
    port = int(os.environ.get('PORT', 6001))  # Port for Flask
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': port}).start()

    # Run the Telegram bot
    run_telegram_bot()

    # Set up the scheduler to ping the app URL every 1 minute
    scheduler = BackgroundScheduler()
    scheduler.add_job(ping_self, 'interval', minutes=1)
    scheduler.start()

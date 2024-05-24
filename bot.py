import discord
from discord.ext import commands
import requests
import base64
import os
import tempfile
import asyncio
from PIL import Image
import aiohttp
import io

# Made by Zombro01
# do not forget to make a file called ban.txt for all banned words


# Discord bot token
DISCORD_TOKEN = "bot_token_here"

# Initialize bot with all intents enabled and the prefix /
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

# URL for interacting with the local API
API_URL = "http://127.0.0.1:7860"

# Load banned words from ban.txt
banned_words = []
banned_words_enabled = True  # Flag to track the state of banned words filter

def load_banned_words():
    global banned_words
    try:
        with open("ban.txt", "r") as file:
            banned_words = file.read().splitlines()
    except FileNotFoundError:
        print("ban.txt file not found.")
    except Exception as e:
        print(f"Error loading banned words: {e}")

load_banned_words()

# Function to check if the prompt contains any banned words
def contains_banned_words(prompt):
    return any(word.lower() in prompt.lower() for word in banned_words)

# A queue to manage image generation requests
request_queue = asyncio.Queue()

# Function to generate image and send to Discord
async def generate_image(ctx, sentence, command_message, status_message):
    try:
        print("Generating image...")

        payload = {
            "prompt": sentence,
            "steps": 20,
            "negative_prompt": "negitive prompt",
            "sampler_name": "sampler",
        }
        response = requests.post(url=f'{API_URL}/sdapi/v1/txt2img', json=payload)
        response.raise_for_status()

        r = response.json()
        image_data = base64.b64decode(r['images'][0])

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        print("Image generated. Sending to Discord...")

        message = await ctx.send(f"Prompt: {sentence}\nUser: {ctx.author.mention}\n", file=discord.File(temp_file_path))

        await message.add_reaction("👍")

        print("Image sent to Discord. Cleaning up...")

        await command_message.delete()  # Delete the original command message
        await status_message.delete()   # Delete the queue status message

        os.remove(temp_file_path)

        print("Temporary files deleted. Request completed.")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

# Function to process the request queue
async def process_queue():
    while True:
        ctx, sentence, command_message, status_message = await request_queue.get()
        await generate_image(ctx, sentence, command_message, status_message)
        request_queue.task_done()

@bot.command()
async def gen(ctx, *, sentence: str):
    print("Request received")

    command_message = ctx.message  # Store the command message

    print(f"User: {ctx.author} Prompt: {sentence}")

    if banned_words_enabled and contains_banned_words(sentence):
        await ctx.message.delete()
        await ctx.send("Your prompt contains inappropriate content.")
        return

    # Send initial status message to the user
    status_message = await ctx.send(f"{ctx.author.mention}, your request has been received and is in the queue.")

    # Put the request in the queue
    await request_queue.put((ctx, sentence, command_message, status_message))

@bot.command()
async def clear(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        try:
            print("Clearing bot's messages...")
            async for message in ctx.channel.history(limit=None):
                if message.author == bot.user:
                    await message.delete()
            await asyncio.sleep(60)
            print("Bot messages cleared.")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        await ctx.send("This command can only be used in DMs.")

@bot.command()
async def TFU(ctx):
    try:
        print("Clearing bot's messages...")
        for channel in ctx.guild.text_channels:
            async for message in channel.history(limit=None):
                if message.author == bot.user:
                    await message.delete()
        await asyncio.sleep(60)
        print("Bot's messages cleared.")
    except Exception as e:
        print(f"An error occurred: {e}")

@bot.command(name="TBW")
async def toggle_banned_words(ctx):
    global banned_words_enabled
    banned_words_enabled = not banned_words_enabled
    state = "enabled" if banned_words_enabled else "disabled"
    confirmation_message = await ctx.send(f"Banned words filter {state}.")
    await asyncio.sleep(5)
    await ctx.message.delete()
    await confirmation_message.delete()

@bot.command(name="TLR")
@commands.has_permissions(administrator=True)
async def toggle_log_requests(ctx):
    global log_requests
    log_requests = not log_requests
    state = "enabled" if log_requests else "disabled"
    confirmation_message = await ctx.send(f"Logging of requests {state}.")
    await asyncio.sleep(5)
    await ctx.message.delete()
    await confirmation_message.delete()

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == "👍" and user != bot.user:
        message = reaction.message
        try:
            # List to store image attachment URLs
            image_urls = []

            # Check for image URLs in message attachments
            for attachment in message.attachments:
                if attachment.filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_urls.append(attachment.url)

            print(f"Number of image attachments: {len(image_urls)}")
            print(f"Image attachments: {image_urls}")

            if image_urls:
                # Send the image URLs to the user's DM
                dm_message = await user.send(f"Here are the image links you liked from message '{message.content}':")
                for image_url in image_urls:
                    await user.send(image_url)

                print(f"Sent liked image URLs to {user.name}")
            else:
                print("No image attachments found.")

        except discord.Forbidden:
            print(f"Cannot send messages to {user.name}.")
        except Exception as e:
            print(f"An error occurred sending DM: {e}")

# Event: Triggered when the bot is ready
@bot.event
async def on_ready():
    print("Setup done. Bot is active")
    print("-----------------------------------------")
    # Start processing the request queue
    bot.loop.create_task(process_queue())

# Run the bot
bot.run(DISCORD_TOKEN)

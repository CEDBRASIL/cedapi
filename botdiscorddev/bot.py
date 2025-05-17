import discord
from discord.ext import commands
import os

# Intents setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        print("❌ Por favor, configure a variável de ambiente DISCORD_BOT_TOKEN com o token do bot.")
    else:
        bot.run(TOKEN)

import discord
from discord.ext import commands
import sys, os

# Import utils/data.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import data

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------
# Events
# -----------------------
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")

# -----------------------
# Setup hook
# -----------------------
async def setup_hook():
    # Load dữ liệu
    data.load_data()
    bot.loop.create_task(data.autosave_loop())
    print("✅ Đã load dữ liệu & chạy autosave")

    # Load tất cả cogs
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    print("✅ Đã load xong tất cả cogs")

    # Đồng bộ slash commands
    await bot.tree.sync()
    print("✅ Slash commands synced!")

bot.setup_hook = setup_hook

# -----------------------
# Run bot
# -----------------------
# Lấy token từ biến môi trường Railway
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ Không tìm thấy biến môi trường DISCORD_TOKEN trên Railway!")

bot.run(TOKEN)

import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import asyncio

from utils.data import get_user, DATA, save_data

# 🎣 Danh sách cá + giá trị
FISH_LIST = [
    ("🐟 Cá Trắm", random.randint(10, 30)),
    ("🐠 Cá Hề", random.randint(50, 100)),
    ("🐡 Cá Nóc", random.randint(10, 60)),
    ("🦈 Cá Mập Con", random.randint(20, 80)),
    ("🐬 Cá Heo Nhỏ", random.randint(30, 90)),
    ("🐳 Cá Voi Mini", random.randint(40, 100)),
    ("🦑 Mực", random.randint(10, 60)),
    ("🦐 Tôm", random.randint(30, 50)),
    ("🦞 Tôm Hùm", random.randint(20, 70)),
    ("🦀 Cua", random.randint(50, 80)),
    ("🐋 Cá Nhà Táng", random.randint(50, 100)),
    ("🐙 Bạch Tuộc", random.randint(10, 60)),
    ("🐊 Cá Sấu Mini", random.randint(30, 90)),
    ("🐌 Ốc Biển", random.randint(10, 20)),
    ("🦦 Rái Cá", random.randint(10, 50)),
]

# ⛏️ Danh sách quặng đá
STONE_LIST = [
    {"name": "💎 Kim Cương", "value": random.randint(10, 90)},
    {"name": "🔶 Thạch Anh Vàng", "value": random.randint(10, 90)},
    {"name": "🔷 Saphia Xanh", "value": random.randint(10, 90)},
    {"name": "🔹 Topaz", "value": random.randint(10, 90)},
    {"name": "⚪ Ngọc Trắng", "value": random.randint(10, 90)},
    {"name": "🟣 Amethyst", "value": random.randint(10, 90)},
    {"name": "🟢 Emerald", "value": random.randint(10, 90)},
    {"name": "🔴 Ruby", "value": random.randint(10, 90)},
    {"name": "🟠 Citrine", "value": random.randint(10, 90)},
    {"name": "🟡 Yellow Sapphire", "value": random.randint(10, 90)},
    {"name": "🟤 Garnet", "value": random.randint(10, 90)},
    {"name": "⚫ Obsidian", "value": random.randint(10, 90)},
    {"name": "🔵 Aquamarine", "value": random.randint(10, 90)},
    {"name": "🟣 Tanzanite", "value": random.randint(10, 90)},
    {"name": "🟢 Peridot", "value": random.randint(10, 90)},
]


class Work(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="work", description="💼 Làm việc để kiếm tiền (/work, /work fish, /work stone)")
    @app_commands.describe(job="Chọn công việc: thường, fish, stone")
    async def work(self, interaction: discord.Interaction, job: str = "normal"):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # Cooldown key riêng theo job
        cooldown_key = f"last_work_{job}"
        last_time = user_data.get(cooldown_key, 0)
        if now - last_time < 60:
            remaining = int(60 - (now - last_time))
            embed_cd = discord.Embed(
                title="⏳ Cooldown",
                description=f"Bạn phải đợi **{remaining}s** trước khi làm việc này tiếp!",
                color=discord.Color.orange()
            )
            return await interaction.response.send_message(embed=embed_cd, ephemeral=True)

        # Xử lý từng job
        if job == "fish":
            fish, price = random.choice(FISH_LIST)
            amount = random.randint(1, 20)
            earned = price * amount
            desc = f"🌊 Bạn đã câu được **{amount}x {fish}**\n💵 Giá mỗi con: **{price:,} xu**\n💰 Tổng: **{earned:,} xu**"
            color = discord.Color.blue()
            thumb = "https://cdn-icons-png.flaticon.com/512/616/616408.png"

        elif job == "stone":
            stone = random.choice(STONE_LIST)
            earned = stone["value"]
            desc = f"⛏️ Bạn đã đào được **{stone['name']}**\n💵 Giá trị: **{earned:,} xu**"
            color = discord.Color.purple()
            thumb = "https://cdn-icons-png.flaticon.com/512/616/616408.png"

        else:  # job thường
            earned = random.randint(50, 150)
            desc = f"🎉 Bạn vừa đi làm và nhận được **{earned:,} xu**"
            color = discord.Color.green()
            thumb = "https://cdn-icons-png.flaticon.com/512/1057/1057248.png"

        # Cập nhật tiền
        user_data["money"] += earned
        user_data[cooldown_key] = now
        save_data()

        # Embed kết quả
        embed = discord.Embed(
            title=f"💼 Công việc: {job.capitalize()}",
            description=desc,
            color=color
        )
        embed.add_field(name="💰 Số dư hiện tại", value=f"**{user_data['money']:,} xu**", inline=False)
        embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=thumb)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await asyncio.sleep(30)
        try:
            await message.delete()
        except:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Work(bot))

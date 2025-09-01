import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import time

from utils.data import get_user, DATA, save_data

# Tạo danh sách 15 quặng đá với giá trị ngẫu nhiên (theo chục và trăm, tổng ≤ 1000)
QUANG_DA_LIST = [
    {"name": "💎 Kim Cương", "value": random.randint(10, 90)},
    {"name": "🔶 Thạch Anh Vàng", "value": random.randint(10, 90)},
    {"name": "🔷 Saphia Xanh", "value": random.randint(10, 90)},
    {"name": "🔹 Topaz", "value": random.randint(10, 900)},
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

class WorkStore(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {}  # user_id : last_time

    @app_commands.command(name="workstore", description="Đào quặng đá và bán để nhận tiền ⛏️💰")
    async def workstore(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # Cooldown 60s
        if user_id in self.cooldowns and now - self.cooldowns[user_id] < 60:
            remaining = int(60 - (now - self.cooldowns[user_id]))
            return await interaction.response.send_message(
                f"⏳ Bạn phải đợi **{remaining}s** trước khi đào tiếp!", ephemeral=True
            )

        self.cooldowns[user_id] = now

        # Random đào ra 1 quặng
        quang = random.choice(QUANG_DA_LIST)
        quang_name = quang["name"]
        quang_value = quang["value"]

        # Cộng tiền cho người chơi
        user_data["money"] += quang_value
        save_data()

        # Embed hiển thị
        embed = discord.Embed(
            title="⛏️ Mini Game Đào Quặng",
            description=f"Bạn đã đào được **{quang_name}** 💎\nGiá trị: **{quang_value:,} Xu**",
            color=discord.Color.random()
        )
        embed.add_field(name="💰 Số Dư Hiện Tại", value=f"**{user_data['money']:,} Xu**", inline=False)
        embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây.")

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await asyncio.sleep(30)
        try:
            await message.delete()
        except:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(WorkStore(bot))

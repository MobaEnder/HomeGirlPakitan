import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import asyncio

from utils.data import get_user, DATA, save_data

# 🎣 Danh sách cá + giá trị
FISH_LIST = [
    ("🐟 Cá Trắm", random.randint(10, 300)),
    ("🐠 Cá Hề", random.randint(50, 500)),
    ("🐡 Cá Nóc", random.randint(100, 600)),
    ("🦈 Cá Mập Con", random.randint(200, 800)),
    ("🐬 Cá Heo Nhỏ", random.randint(300, 900)),
    ("🐳 Cá Voi Mini", random.randint(400, 1000)),
    ("🦑 Mực", random.randint(50, 400)),
    ("🦐 Tôm", random.randint(30, 350)),
    ("🦞 Tôm Hùm", random.randint(200, 700)),
    ("🦀 Cua", random.randint(50, 450)),
    ("🐋 Cá Nhà Táng", random.randint(500, 1000)),
    ("🐙 Bạch Tuộc", random.randint(150, 650)),
    ("🐊 Cá Sấu Mini", random.randint(300, 900)),
    ("🐌 Ốc Biển", random.randint(10, 200)),
    ("🦦 Rái Cá", random.randint(100, 500)),
]

class WorkFish(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="workfish", description="🎣 Câu cá kiếm tiền")
    async def workfish(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # Cooldown 60s
        if now - user_data.get("last_fish", 0) < 60:
            remaining = int(60 - (now - user_data["last_fish"]))
            embed_cd = discord.Embed(
                title="⏳ Cooldown",
                description=f"Bạn phải đợi **{remaining}s** trước khi đi câu tiếp!",
                color=discord.Color.orange()
            )
            embed_cd.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3515/3515305.png")
            return await interaction.response.send_message(embed=embed_cd, ephemeral=True)

        # Random cá
        fish, price = random.choice(FISH_LIST)
        amount = random.randint(1, 20)
        total_value = price * amount

        # Cập nhật user
        user_data["money"] += total_value
        user_data["last_fish"] = now
        save_data()

        # Embed kết quả
        embed = discord.Embed(
            title="🎣 Bạn vừa đi câu cá!",
            description=f"🌊 Bạn đã câu được **{amount}x {fish}**\n"
                        f"💵 Giá mỗi con: **{price:,} xu**\n"
                        f"💰 Tổng bán được: **{total_value:,} xu**",
            color=discord.Color.blue()
        )
        embed.add_field(name="💼 Số dư hiện tại", value=f"**{user_data['money']:,} xu**", inline=False)
        embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây")
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/616/616408.png")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await asyncio.sleep(30)
        try:
            await message.delete()
        except:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(WorkFish(bot))

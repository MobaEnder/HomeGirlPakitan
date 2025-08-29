import discord
from discord import app_commands
from discord.ext import commands
import time, random

from utils.data import get_user, DATA, save_data

JOBS = [
    "Nole Tư Bản 🌾",
    "Thợ Mỏ Fuba ⛏️",
    "Ngư Dân 🎣",
    "Thợ Săn Tre Em 🏹",
    "Code Wibu 💻",
    "Let Me Cook 🍳",
    "Phi Công Trẻ ✈️",
    "Ca Sĩ 🎤",
    "Họa Sĩ 🎨",
    "Nghiên Cứu 🔬",
    "Kiếm Khác ⚔️",
    "Wibu 📚",
    "Eodibiti 🏳️‍🌈",
    "MoiDen 👦🏿",
]

class SetJob(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setjob", description="👔 Chọn công việc để kiếm tiền")
    @app_commands.describe(job="Chọn nghề nghiệp")
    @app_commands.choices(job=[
        app_commands.Choice(name=job, value=job) for job in JOBS
    ])
    async def setjob(self, interaction: discord.Interaction, job: app_commands.Choice[str]):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # Cooldown 24h
        if user_data.get("last_setjob") and now - user_data["last_setjob"] < 86400:
            remaining = int(86400 - (now - user_data["last_setjob"]))
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)

            embed_cd = discord.Embed(
                title="⏳ Chờ Thời Gian Cooldown",
                description=f"Bạn phải đợi **{hours}h {minutes}m {seconds}s** nữa mới có thể đổi nghề!",
                color=discord.Color.orange()
            )
            embed_cd.set_footer(text="🛠️ Hãy quay lại sau để đổi nghề nghiệp")
            embed_cd.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1067/1067895.png")
            return await interaction.response.send_message(embed=embed_cd, ephemeral=True)

        # Random lương (100 → 500)
        salary = random.randint(100, 500)

        # Cập nhật thông tin nghề
        user_data["job"] = job.value
        user_data["salary"] = salary
        user_data["last_setjob"] = now
        save_data()

        # Embed hiển thị nghề vừa chọn
        embed = discord.Embed(
            title="✅ Bạn đã chọn nghề mới!",
            description=f"**{job.value}** 👔",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Lương mỗi lần làm việc", value=f"**{salary:,} Xu**", inline=False)
        embed.set_footer(text="🌟 Hãy làm việc chăm chỉ để kiếm thật nhiều xu!")
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1057/1057248.png")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SetJob(bot))

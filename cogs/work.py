import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import asyncio  # ← bắt buộc để dùng await asyncio.sleep()

from utils.data import get_user, DATA, save_data

class Work(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="work", description="💼 Làm việc kiếm tiền mỗi ngày")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # ✅ Kiểm tra nếu đang bị bắt (jailed)
        jailed_until = user_data.get("jailed_until", 0)
        if jailed_until > now:
            remaining = int(jailed_until - now)
            minutes, seconds = divmod(remaining, 60)
            embed_jail = discord.Embed(
                title="🚨 Bị Giam Giữ!",
                description=f"Bạn đang bị giam, không thể đi làm!\n⏳ Thời gian còn lại: **{minutes}m {seconds}s**",
                color=discord.Color.red()
            )
            embed_jail.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/565/565445.png")
            embed_jail.set_footer(text="🛑 Hãy chờ hết thời gian giam để làm việc lại.")
            return await interaction.response.send_message(embed=embed_jail, ephemeral=True)

        # Cooldown 60s
        if now - user_data.get("last_work", 0) < 60:
            remaining = int(60 - (now - user_data["last_work"]))
            embed_cd = discord.Embed(
                title="⏳ Cooldown",
                description=f"Bạn phải đợi **{remaining}s** trước khi làm việc tiếp!",
                color=discord.Color.orange()
            )
            embed_cd.set_footer(text="💼 Hãy quay lại sau để kiếm tiền tiếp.")
            embed_cd.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1057/1057248.png")
            return await interaction.response.send_message(embed=embed_cd, ephemeral=True)

        # Random tiền kiếm được
        earned = random.randint(50, 150)
        user_data["money"] += earned
        user_data["last_work"] = now
        save_data()

        # Embed kết quả
        embed = discord.Embed(
            title="💼 Bạn vừa đi làm!",
            description=f"🎉 Chúc mừng! Bạn kiếm được **{earned:,} xu**",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Số dư hiện tại", value=f"**{user_data['money']:,} xu**", inline=False)
        embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây")
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1057/1057248.png")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await asyncio.sleep(30)
        try:
            await message.delete()
        except:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Work(bot))

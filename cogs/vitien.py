import discord
from discord import app_commands
from discord.ext import commands
from utils.data import get_user, DATA, save_data

class ViTien(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="vitien", description="💰 Xem số dư của bạn hoặc người khác")
    @app_commands.describe(user="Người mà bạn muốn xem ví (tùy chọn)")
    async def vitien(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user

        user_data = get_user(DATA, user.id)

        balance = user_data.get("money", 0)
        job = user_data.get("job", "Chưa có nghề")
        baove = user_data.get("baove", 0)  # thêm số lượt bảo vệ

        embed = discord.Embed(
            title="💰 Ví Tiền",
            color=discord.Color.gold()
        )
        embed.add_field(name="👤 Chủ Ví", value=f"{user.mention}", inline=False)
        embed.add_field(name="💼 Nghề Nghiệp", value=f"**{job}**", inline=True)
        embed.add_field(name="💰 Số Dư", value=f"**{balance} Xu**", inline=True)
        embed.add_field(name="🛡️ Bảo Vệ", value=f"**{baove} lần**", inline=True)

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="🪙 Theo dõi số dư và bảo vệ của bạn mọi lúc!")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ViTien(bot))

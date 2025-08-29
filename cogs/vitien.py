import discord
from discord import app_commands
from discord.ext import commands
from utils.data import get_user, DATA, save_data

class ViTien(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="vitien", description="💰 Xem số dư của bạn")
    async def vitien(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        balance = user_data.get("money", 0)
        job = user_data.get("job", "Chưa có nghề")

        embed = discord.Embed(
            title="💰 Ví Tiền Của Bạn",
            color=discord.Color.blurple()
        )
        embed.add_field(name="👤 Người Dùng", value=f"{interaction.user.mention}", inline=False)
        embed.add_field(name="💼 Nghề Nghiệp", value=f"**{job}**", inline=True)
        embed.add_field(name="💰 Số Dư Hiện Tại", value=f"**{balance} Xu**", inline=True)
        embed.set_footer(text="🪙 Theo dõi số dư của bạn mọi lúc!")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ViTien(bot))

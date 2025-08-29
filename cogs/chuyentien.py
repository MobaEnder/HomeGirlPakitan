import discord
from discord import app_commands
from discord.ext import commands
import time
import asyncio

from utils.data import get_user, save_data, DATA

class ChuyenTien(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="chuyentien", description="💸 Chuyển tiền cho người khác")
    @app_commands.describe(
        member="Người nhận",
        amount="Số tiền muốn chuyển"
    )
    async def chuyentien(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        sender_id = interaction.user.id
        receiver_id = member.id

        if sender_id == receiver_id:
            return await interaction.response.send_message(
                "❌ Bạn không thể tự chuyển tiền cho chính mình!",
                ephemeral=True
            )

        sender_data = get_user(DATA, sender_id)
        receiver_data = get_user(DATA, receiver_id)
        now = time.time()

        # Cooldown 15s
        if now - sender_data.get("last_chuyentien", 0) < 15:
            remaining = int(15 - (now - sender_data["last_chuyentien"]))
            return await interaction.response.send_message(
                f"⏳ Bạn cần đợi **{remaining}s** mới có thể chuyển tiền tiếp!",
                ephemeral=True
            )

        if amount <= 0:
            return await interaction.response.send_message(
                "❌ Số tiền phải lớn hơn 0!",
                ephemeral=True
            )
        if sender_data["money"] < amount:
            return await interaction.response.send_message(
                "💸 Bạn không đủ tiền để chuyển!",
                ephemeral=True
            )

        # Cập nhật dữ liệu
        sender_data["money"] -= amount
        receiver_data["money"] += amount
        sender_data["last_chuyentien"] = now
        save_data()

        # Tạo embed kết quả
        embed = discord.Embed(
            title="💸 Chuyển Tiền Thành Công",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 Người Gửi", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="👤 Người Nhận", value=f"{member.mention}", inline=True)
        embed.add_field(name="💰 Số Tiền Chuyển", value=f"**{amount} Xu**", inline=False)
        embed.add_field(name="💳 Số Dư Hiện Tại", value=f"**{sender_data['money']} Xu**", inline=False)
        embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây.")

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Xóa sau 30s
        await asyncio.sleep(30)
        try:
            await message.delete()
        except discord.NotFound:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(ChuyenTien(bot))

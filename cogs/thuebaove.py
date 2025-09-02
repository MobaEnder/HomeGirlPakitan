import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from utils.data import get_user, save_data, DATA


# Giá thuê bảo vệ
BAOVE_PACKAGES = {
    1000: 1,   # 1000 xu → 1 lần
    5000: 2,   # 5000 xu → 2 lần
    10000: 3,  # 10000 xu → 3 lần
    20000: 4,  # 20000 xu → 4 lần
    30000: 5   # 30000 xu → 5 lần
}


class BinhAn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="thuebaove", description="🛡️ Thuê bảo vệ chống cướp")

    @group.command(name="mua", description="🛡️ Thuê bảo vệ với các gói khác nhau")
    @app_commands.describe(gia="Giá gói thuê bảo vệ (1000/5000/10000/20000/30000)")
    async def mua(self, interaction: discord.Interaction, gia: int):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        if gia not in BAOVE_PACKAGES:
            return await interaction.response.send_message("❌ Gói bảo vệ không hợp lệ!", ephemeral=True)

        so_lan = BAOVE_PACKAGES[gia]

        if user_data["money"] < gia:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để thuê bảo vệ!", ephemeral=True)

        # Trừ tiền + set lại số lần bảo vệ
        user_data["money"] -= gia
        user_data["baove"] = so_lan
        save_data()

        # Tạo embed thông báo
        embed = discord.Embed(
            title="🛡️ Thuê Bảo Vệ Thành Công!",
            description=(
                f"Bạn đã thuê gói **{so_lan} lần bảo vệ** với giá **{gia} xu**.\n\n"
                f"💰 Số dư mới: **{user_data['money']} xu**\n"
                f"🛡️ Lượt bảo vệ hiện tại: **{user_data['baove']} lần**"
            ),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3064/3064197.png")

        await interaction.response.send_message(embed=embed, ephemeral=False)

        # Tự xóa sau 30 giây
        await asyncio.sleep(30)
        try:
            m = await interaction.original_response()
            await m.delete()
        except:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(BinhAn(bot))

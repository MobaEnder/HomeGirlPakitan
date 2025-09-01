import discord
from discord import app_commands
from discord.ext import commands
import os

from utils.data import get_user, save_data, DATA

# Lấy danh sách ID admin từ biến môi trường (Railway Variables)
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]


def admin_only(interaction: discord.Interaction) -> bool:
    return interaction.user.id in ADMINS


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /setmoney
    @app_commands.command(name="setmoney", description="👑 Set tiền cho người chơi (Admin only)")
    @app_commands.check(admin_only)
    @app_commands.describe(user="Người cần chỉnh", amount="Số tiền mới")
    async def setmoney(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        data = get_user(DATA, user.id)
        data["money"] = amount
        save_data()
        await interaction.response.send_message(
            f"✅ Đã set tiền của {user.mention} = **{amount:,} xu**",
            ephemeral=True
        )

    # /addmoney
    @app_commands.command(name="addmoney", description="👑 Cộng thêm tiền cho người chơi (Admin only)")
    @app_commands.check(admin_only)
    @app_commands.describe(user="Người cần cộng", amount="Số tiền cộng thêm")
    async def addmoney(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        data = get_user(DATA, user.id)
        data["money"] += amount
        save_data()
        await interaction.response.send_message(
            f"💰 Đã cộng thêm **{amount:,} xu** cho {user.mention}.\nSố dư mới: **{data['money']:,} xu**",
            ephemeral=True
        )

    # /resetall
    @app_commands.command(name="resetall", description="⚠️ Xóa toàn bộ dữ liệu (Admin only)")
    @app_commands.check(admin_only)
    async def resetall(self, interaction: discord.Interaction):
        # Confirm trước khi xóa
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="✅ Đồng ý", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                global DATA
                DATA.clear()
                save_data()
                await interaction_btn.response.edit_message(content="🔥 Đã reset toàn bộ dữ liệu!", view=None)

            @discord.ui.button(label="❌ Hủy", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await interaction_btn.response.edit_message(content="❌ Đã hủy reset.", view=None)

        view = ConfirmView()
        await interaction.response.send_message(
            "⚠️ Bạn có chắc muốn **reset toàn bộ dữ liệu**? Hành động này không thể hoàn tác!",
            view=view,
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))

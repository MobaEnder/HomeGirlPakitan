import discord
from discord import app_commands
from discord.ext import commands

from utils.data import get_user, save_data, DATA
import os

# Lấy danh sách ID admin từ biến môi trường (Railway Variables)
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]

class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Hàm check admin
    def is_admin(self, user_id: int) -> bool:
        return user_id in ADMINS

    # /setmoney
    @app_commands.command(name="setmoney", description="👑 Set tiền cho người chơi")
    @app_commands.describe(user="Người cần chỉnh", amount="Số tiền mới")
    async def setmoney(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not self.is_admin(interaction.user.id):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)

        data = get_user(DATA, user.id)
        data["money"] = amount
        save_data()
        await interaction.response.send_message(
            f"✅ Đã set tiền của {user.mention} = **{amount:,} xu**"
        )

    # /addmoney
    @app_commands.command(name="addmoney", description="👑 Cộng thêm tiền cho người chơi")
    @app_commands.describe(user="Người cần cộng", amount="Số tiền cộng thêm")
    async def addmoney(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not self.is_admin(interaction.user.id):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)

        data = get_user(DATA, user.id)
        data["money"] += amount
        save_data()
        await interaction.response.send_message(
            f"💰 Đã cộng thêm **{amount:,} xu** cho {user.mention}.\nSố dư mới: **{data['money']:,} xu**"
        )

    # /checkmoney
    @app_commands.command(name="checkmoney", description="👑 Xem tiền của một user (admin)")
    @app_commands.describe(user="Người cần kiểm tra")
    async def checkmoney(self, interaction: discord.Interaction, user: discord.Member):
        if not self.is_admin(interaction.user.id):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)

        data = get_user(DATA, user.id)
        await interaction.response.send_message(
            f"📊 {user.mention} hiện có **{data['money']:,} xu**"
        )

    # /resetall
    @app_commands.command(name="resetall", description="⚠️ Xóa toàn bộ dữ liệu (admin only)")
    async def resetall(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user.id):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)

        # Confirm trước khi xóa
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None

            @discord.ui.button(label="✅ Đồng ý", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                global DATA
                DATA.clear()
                save_data()
                self.value = True
                await interaction_btn.response.edit_message(content="🔥 Đã reset toàn bộ dữ liệu!", view=None)

            @discord.ui.button(label="❌ Hủy", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                self.value = False
                await interaction_btn.response.edit_message(content="❌ Đã hủy reset.", view=None)

        view = ConfirmView()
        await interaction.response.send_message(
            "⚠️ Bạn có chắc muốn **reset toàn bộ dữ liệu**? Hành động này không thể hoàn tác!",
            view=view,
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))

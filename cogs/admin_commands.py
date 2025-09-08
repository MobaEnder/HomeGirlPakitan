import discord
from discord import app_commands
from discord.ext import commands
import os

from utils.data import get_user, save_data, DATA
from utils import rivens  # để clear inventory

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

    # /reset
    @app_commands.command(name="reset", description="⚠️ Reset dữ liệu (Admin only)")
    @app_commands.check(admin_only)
    @app_commands.describe(target="Chọn loại dữ liệu cần reset")
    @app_commands.choices(
        target=[
            app_commands.Choice(name="Money (tiền)", value="money"),
            app_commands.Choice(name="Inventory (Rivens)", value="inventory"),
            app_commands.Choice(name="Tất cả", value="all"),
        ]
    )
    async def reset(self, interaction: discord.Interaction, target: app_commands.Choice[str]):
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="✅ Đồng ý", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                global DATA
                if target.value == "money":
                    # reset toàn bộ tiền về 0
                    for uid, user_data in DATA.items():
                        user_data["money"] = 0
                    save_data()
                    msg = "🔥 Đã reset toàn bộ **tiền** về 0!"
                elif target.value == "inventory":
                    # reset toàn bộ rivens
                    rivens.DATA_RIVENS.clear()
                    rivens.save_rivens()
                    msg = "🔥 Đã xoá toàn bộ **inventory Riven**!"
                elif target.value == "all":
                    DATA.clear()
                    save_data()
                    rivens.DATA_RIVENS.clear()
                    rivens.save_rivens()
                    msg = "🔥 Đã reset toàn bộ dữ liệu (money + inventory)!"
                else:
                    msg = "⚠️ Lựa chọn không hợp lệ."
                await interaction_btn.response.edit_message(content=msg, view=None)

            @discord.ui.button(label="❌ Hủy", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await interaction_btn.response.edit_message(content="❌ Đã hủy reset.", view=None)

        view = ConfirmView()
        await interaction.response.send_message(
            f"⚠️ Bạn có chắc muốn reset dữ liệu **{target.name}**?",
            view=view,
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))

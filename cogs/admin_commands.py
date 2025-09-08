import discord
from discord import app_commands
from discord.ext import commands
import os

from utils.data import get_user, save_data, DATA
import utils.rivens as rivens

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
    @app_commands.command(name="resetall", description="⚠️ Reset dữ liệu (Admin only)")
    @app_commands.check(admin_only)
    async def resetall(self, interaction: discord.Interaction):
        class ResetType(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label="💸 Money", value="money", description="Reset toàn bộ tiền của người chơi"),
                    discord.SelectOption(label="🎴 Inventory Riven", value="inventory", description="Xoá toàn bộ Riven mod"),
                    discord.SelectOption(label="🔥 ALL", value="all", description="Reset cả money và Riven"),
                ]
                super().__init__(placeholder="Chọn loại dữ liệu cần reset...", options=options, min_values=1, max_values=1)

            async def callback(self, interaction_select: discord.Interaction):
                value = self.values[0]

                if value == "money":
                    DATA.clear()
                    save_data()
                    msg = "💸 Đã reset toàn bộ **money**!"
                elif value == "inventory":
                    rivens.RIVENS.clear()
                    rivens.save_rivens()
                    msg = "🎴 Đã xoá toàn bộ **inventory Riven**!"
                else:  # all
                    DATA.clear()
                    save_data()
                    rivens.RIVENS.clear()
                    rivens.save_rivens()
                    msg = "🔥 Đã reset toàn bộ dữ liệu (**money + inventory**)!"

                await interaction_select.response.edit_message(content=msg, view=None)

        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.add_item(ResetType())

        await interaction.response.send_message(
            "⚠️ Chọn loại dữ liệu bạn muốn **reset**:",
            view=ConfirmView(),
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))

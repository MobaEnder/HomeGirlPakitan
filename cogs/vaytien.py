import discord
from discord import app_commands
from discord.ext import commands
import time

from utils.data import get_user, DATA, save_data

class VayTien(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Lệnh vay tiền
    @app_commands.command(name="vaytien", description="Vay tiền từ nhà cái 💰 (100 - 500 xu)")
    @app_commands.describe(sotien="Số tiền muốn vay (100 - 500 xu)")
    async def vaytien(self, interaction: discord.Interaction, sotien: int):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        if sotien < 100 or sotien > 500:
            return await interaction.response.send_message(
                "⚠️ Bạn chỉ có thể vay từ **100** đến **500 xu**.", ephemeral=True
            )

        if "debt" in user_data and user_data["debt"].get("amount", 0) > 0:
            debt = user_data["debt"]
            due = int(debt["due_time"] - now)
            if due > 0:
                hours = due // 3600
                minutes = (due % 3600) // 60
                return await interaction.response.send_message(
                    f"🚨 Bạn vẫn còn nợ **{debt['amount']} xu**!\n"
                    f"⏳ Hạn trả còn: **{hours}h {minutes}m**.\n"
                    f"❌ Không thể vay thêm cho đến khi trả nợ.",
                    ephemeral=True
                )

        # Cấp tiền và ghi nợ
        user_data["money"] += sotien
        user_data["debt"] = {
            "amount": sotien,
            "due_time": now + 43200  # 12 giờ
        }
        save_data()

        await interaction.response.send_message(
            f"🏦 Bạn vừa vay **{sotien} xu** từ nhà cái.\n"
            f"💰 Số dư hiện tại: **{user_data['money']} xu**\n"
            f"⏳ Bạn cần trả nợ trong vòng **12 giờ** nếu không sẽ bị **cấm chơi mini game**!"
        )

    # Lệnh trả tiền
    @app_commands.command(name="tratien", description="Trả nợ cho nhà cái 💸")
    async def tratien(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        # Kiểm tra có nợ không
        if "debt" not in user_data or user_data["debt"].get("amount", 0) <= 0:
            return await interaction.response.send_message(
                "✅ Bạn không có khoản nợ nào cần trả!", ephemeral=True
            )

        debt = user_data["debt"]["amount"]

        # Kiểm tra tiền đủ không
        if user_data["money"] < debt:
            return await interaction.response.send_message(
                f"❌ Bạn không đủ tiền để trả nợ!\n"
                f"💰 Số dư hiện tại: **{user_data['money']} xu**\n"
                f"📉 Số tiền cần để trả: **{debt} xu**",
                ephemeral=True
            )

        # Trừ tiền và xoá nợ
        user_data["money"] -= debt
        user_data["debt"] = {"amount": 0, "due_time": 0}
        save_data()

        await interaction.response.send_message(
            f"💸 Bạn đã trả nợ thành công **{debt} xu** cho nhà cái!\n"
            f"💰 Số dư còn lại: **{user_data['money']} xu**\n"
            f"✅ Giờ bạn có thể tham gia các mini game bình thường."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(VayTien(bot))

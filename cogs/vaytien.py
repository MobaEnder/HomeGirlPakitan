import discord
from discord import app_commands
from discord.ext import commands
import time

from utils.data import get_user, DATA, save_data

class VayTien(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Lệnh vay tiền
    @app_commands.command(name="vaytien", description="💰 Vay tiền từ nhà cái (100 - 500 xu)")
    @app_commands.describe(sotien="Số tiền muốn vay (100 - 500 xu)")
    async def vaytien(self, interaction: discord.Interaction, sotien: int):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        if sotien < 100 or sotien > 500:
            embed = discord.Embed(
                title="⚠️ Không hợp lệ",
                description="Bạn chỉ có thể vay từ **100** đến **500 xu**.",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/565/565547.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if "debt" in user_data and user_data["debt"].get("amount", 0) > 0:
            debt = user_data["debt"]
            due = int(debt["due_time"] - now)
            if due > 0:
                hours = due // 3600
                minutes = (due % 3600) // 60
                embed = discord.Embed(
                    title="🚨 Bạn đang có khoản nợ!",
                    description=(
                        f"💸 Số tiền nợ: **{debt['amount']:,} xu**\n"
                        f"⏳ Hạn trả còn: **{hours}h {minutes}m**\n\n"
                        f"❌ Không thể vay thêm cho đến khi trả nợ!"
                    ),
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/6062/6062646.png")
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Cấp tiền và ghi nợ
        user_data["money"] += sotien
        user_data["debt"] = {
            "amount": sotien,
            "due_time": now + 43200  # 12 giờ
        }
        save_data()

        embed = discord.Embed(
            title="🏦 Vay tiền thành công!",
            description=(
                f"Bạn vừa vay **{sotien:,} xu** từ nhà cái.\n\n"
                f"💰 Số dư hiện tại: **{user_data['money']:,} xu**\n"
                f"⏳ Bạn cần trả nợ trong vòng **12 giờ** nếu không sẽ bị **cấm chơi mini game**!"
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/190/190411.png")
        await interaction.response.send_message(embed=embed)

    # Lệnh trả tiền
    @app_commands.command(name="tratien", description="💸 Trả nợ cho nhà cái")
    async def tratien(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        # Kiểm tra có nợ không
        if "debt" not in user_data or user_data["debt"].get("amount", 0) <= 0:
            embed = discord.Embed(
                title="✅ Không có nợ",
                description="Bạn không có khoản nợ nào cần trả!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1048/1048947.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        debt = user_data["debt"]["amount"]

        # Kiểm tra tiền đủ không
        if user_data["money"] < debt:
            embed = discord.Embed(
                title="❌ Không đủ tiền",
                description=(
                    f"💰 Số dư hiện tại: **{user_data['money']:,} xu**\n"
                    f"📉 Số tiền cần để trả: **{debt:,} xu**"
                ),
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/463/463612.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Trừ tiền và xoá nợ
        user_data["money"] -= debt
        user_data["debt"] = {"amount": 0, "due_time": 0}
        save_data()

        embed = discord.Embed(
            title="💸 Trả nợ thành công!",
            description=(
                f"Bạn đã trả nợ thành công **{debt:,} xu** cho nhà cái!\n\n"
                f"💰 Số dư còn lại: **{user_data['money']:,} xu**\n"
                f"✅ Giờ bạn có thể tham gia các mini game bình thường."
            ),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/929/929416.png")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(VayTien(bot))

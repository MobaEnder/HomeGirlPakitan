import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import time

from utils.data import get_user, DATA, save_data

class BauCua(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    animals = {
        "nai": "🦌 Nai",
        "bau": "🎍 Bầu",
        "ga": "🐓 Gà",
        "ca": "🐟 Cá",
        "cua": "🦀 Cua",
        "tom": "🦐 Tôm",
    }

    @app_commands.command(name="baucua", description="🎲 Chơi Mini Game Bầu Cua 🦀🐟🐓")
    @app_commands.describe(
        bet="Số tiền muốn cược",
        choice="Chọn con vật để cược"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="🦌 Nai", value="nai"),
        app_commands.Choice(name="🎍 Bầu", value="bau"),
        app_commands.Choice(name="🐓 Gà", value="ga"),
        app_commands.Choice(name="🐟 Cá", value="ca"),
        app_commands.Choice(name="🦀 Cua", value="cua"),
        app_commands.Choice(name="🦐 Tôm", value="tom"),
    ])
    async def baucua(self, interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # Cooldown 10s
        if now - user_data.get("last_baucua", 0) < 10:
            remaining = int(10 - (now - user_data["last_baucua"]))
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Chậm thôi!",
                    description=f"Bạn phải đợi **{remaining}s** mới có thể chơi lại!",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )

        # Kiểm tra số dư
        if bet <= 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Lỗi",
                    description="Số tiền cược phải lớn hơn **0 Xu**!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        if user_data["money"] < bet:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="💸 Không đủ tiền",
                    description=f"Bạn chỉ có **{user_data['money']} Xu**, không đủ để cược!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        # Trừ tiền cược
        user_data["money"] -= bet
        user_data["last_baucua"] = now
        save_data()

        # Gửi embed chờ
        embed = discord.Embed(
            title="🎲 Bầu Cua Đang Lắc...",
            description=f"💼 Bạn đã cược **{bet:,} Xu** vào **{self.animals[choice.value]}**",
            color=discord.Color.yellow()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3082/3082031.png")
        embed.set_footer(text="⏳ Vui lòng chờ 5s để xem kết quả!")
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Đếm ngược 5s
        for i in range(5, 0, -1):
            await asyncio.sleep(1)
            embed.title = f"🎲 Đang Lắc Bầu Cua... {i}s"
            await message.edit(embed=embed)

        # Lắc 3 con
        result = [random.choice(list(self.animals.keys())) for _ in range(3)]
        result_icons = " ".join(self.animals[r].split()[0] for r in result)

        # Đếm số lần trúng
        win_count = result.count(choice.value)

        if win_count > 0:
            reward = bet * win_count
            total_reward = bet + reward
            user_data["money"] += total_reward
            save_data()
            outcome = (
                f"🎉 Bạn trúng **{win_count} lần**!\n"
                f"💰 Nhận về **+{total_reward:,} Xu**"
            )
            color = discord.Color.green()
            thumb = "https://cdn-icons-png.flaticon.com/512/4315/4315445.png"
        else:
            outcome = f"💀 Bạn không trúng con nào!\n❌ Mất **{bet:,} Xu**"
            color = discord.Color.red()
            thumb = "https://cdn-icons-png.flaticon.com/512/463/463612.png"

        # Embed kết quả
        result_embed = discord.Embed(
            title="🎲 Kết Quả Bầu Cua",
            description=(
                f"**Kết quả:** {result_icons}\n\n"
                f"💼 **Bạn Cược:** {self.animals[choice.value]}\n"
                f"{outcome}\n\n"
                f"💳 **Số Dư Hiện Tại:** {user_data['money']:,} Xu"
            ),
            color=color
        )
        result_embed.set_thumbnail(url=thumb)
        result_embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30s.")

        await message.edit(embed=result_embed)

        # Xóa sau 30s
        await asyncio.sleep(30)
        try:
            await message.delete()
        except discord.NotFound:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(BauCua(bot))

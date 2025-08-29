import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import time

# Import hàm và data
from utils.data import get_user, DATA, save_data


class TaiXiu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="taixiu", description="Chơi Mini Game Tài Xỉu 🎲")
    @app_commands.describe(
        bet="Số tiền muốn cược",
        choice="Chọn Tài hoặc Xỉu"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Tài 🎲", value="tai"),
        app_commands.Choice(name="Xỉu 🎲", value="xiu"),
    ])
    async def taixiu(self, interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # Cooldown 10s
        if now - user_data.get("last_taixiu", 0) < 10:
            remaining = int(10 - (now - user_data["last_taixiu"]))
            return await interaction.response.send_message(
                f"⏳ Bạn phải đợi **{remaining}s** mới có thể chơi lại Tài Xỉu!",
                ephemeral=True
            )

        # Kiểm tra số dư
        if bet <= 0:
            return await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
        if user_data["money"] < bet:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để cược!", ephemeral=True)

        # Trừ tiền cược trước
        user_data["money"] -= bet
        user_data["last_taixiu"] = now
        save_data()

        # Embed chờ
        embed = discord.Embed(
            title="🎲 Tài Xỉu - Đang Lăn Xúc Xắc",
            description=f"💼 Bạn đã cược **{bet:,} xu** vào **{'Tài' if choice.value=='tai' else 'Xỉu'}**\n\n⏳ Đang lăn xúc xắc, vui lòng chờ...",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Đếm ngược 5s
        for i in range(5, 0, -1):
            await asyncio.sleep(1)
            embed.description = f"💼 Bạn đã cược **{bet:,} xu** vào **{'Tài' if choice.value=='tai' else 'Xỉu'}**\n\n⏳ Đang lăn xúc xắc... **{i}s**"
            await message.edit(embed=embed)

        # Lăn 3 xúc xắc
        dice = [random.randint(1, 6) for _ in range(3)]
        total = sum(dice)
        result = "tai" if total >= 11 else "xiu"

        # Icon xúc xắc
        dice_icons = {
            1: "⚀", 2: "⚁", 3: "⚂",
            4: "⚃", 5: "⚄", 6: "⚅",
        }
        dice_str = " ".join(dice_icons[d] for d in dice)

        # Kết quả
        if choice.value == result:
            reward = bet * 2
            user_data["money"] += reward
            save_data()
            outcome = f"🎉 Bạn Thắng! Nhận Được **+{reward:,} Xu**"
            color = discord.Color.green()
        else:
            outcome = f"💀 Bạn Thua! Mất **-{bet:,} Xu**"
            color = discord.Color.red()

        # Hiển thị kết quả bằng Embed
        result_embed = discord.Embed(
            title="🎲 Kết Quả Tài Xỉu",
            color=color
        )
        result_embed.add_field(name="🎲 Xúc Xắc", value=f"{dice_str}", inline=False)
        result_embed.add_field(name="📊 Tổng Điểm", value=f"**{total}** → **{'Tài' if result=='tai' else 'Xỉu'}**", inline=False)
        result_embed.add_field(name="💼 Bạn Chọn", value=f"{'Tài' if choice.value=='tai' else 'Xỉu'}", inline=True)
        result_embed.add_field(name="💬 Kết Luận", value=outcome, inline=False)
        result_embed.add_field(name="🪙 Số Dư Hiện Tại", value=f"**{user_data['money']:,} Xu**", inline=False)
        result_embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây.")

        await message.edit(embed=result_embed)

        # Xóa tin nhắn sau 30s
        await asyncio.sleep(30)
        try:
            await message.delete()
        except discord.NotFound:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(TaiXiu(bot))

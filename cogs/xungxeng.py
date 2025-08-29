import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta
import asyncio

from utils.data import get_user, save_data, DATA

EMOJIS = ["🍒", "🍋", "🔔", "🍇", "💎", "⭐"]


def get_slot_cooldown(user):
    last = user.get("last_slot", "1970-01-01T00:00:00")
    last_time = datetime.fromisoformat(last)
    elapsed = datetime.utcnow() - last_time
    cd = timedelta(seconds=10)   # cooldown 10s
    return None if elapsed >= cd else cd - elapsed


def roll_slots():
    """Quay slot với tỉ lệ Jackpot 20%"""
    r = random.random()  # 0.0 → 1.0
    if r < 0.2:  # 🎉 Jackpot 20%
        symbol = random.choice(EMOJIS)
        return [symbol, symbol, symbol]

    elif r < 0.5:  # 🥳 30% ra 2 cái trùng
        symbol = random.choice(EMOJIS)
        other = random.choice([e for e in EMOJIS if e != symbol])
        pos = random.sample([0, 1, 2], 2)  # chọn 2 vị trí giống nhau
        result = [""] * 3
        for p in pos:
            result[p] = symbol
        for i in range(3):
            if result[i] == "":
                result[i] = other
        return result

    else:  # 😢 50% random bình thường (có thể ra 1 hoặc 0 cái trùng)
        return [random.choice(EMOJIS) for _ in range(3)]


class XungXeng(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="xungxeng", description="🎰 Quay xèng may mắn để thử vận may!")
    @app_commands.describe(
        amount="Số tiền bạn muốn đặt cược",
        pick="Chọn biểu tượng bạn muốn đặt cược (🍒, 🍋, 🔔, 🍇, 💎, ⭐)"
    )
    @app_commands.choices(
        pick=[
            app_commands.Choice(name="🍒 Cheri", value="🍒"),
            app_commands.Choice(name="🍋 Chanh", value="🍋"),
            app_commands.Choice(name="🔔 Chuông", value="🔔"),
            app_commands.Choice(name="🍇 Nho", value="🍇"),
            app_commands.Choice(name="💎 Kim Cương", value="💎"),
            app_commands.Choice(name="⭐ Ngôi Sao", value="⭐"),
        ]
    )
    async def xungxeng(self, interaction: discord.Interaction, amount: int, pick: app_commands.Choice[str]):
        uid = interaction.user.id
        user = get_user(DATA, uid)

        if not user:
            return await interaction.response.send_message("❌ Bạn chưa có hồ sơ!", ephemeral=True)

        cd = get_slot_cooldown(user)
        if cd:
            m, s = divmod(int(cd.total_seconds()), 60)
            return await interaction.response.send_message(
                f"⏳ Bạn cần chờ {m} phút {s} giây để quay tiếp!", ephemeral=True)

        if amount <= 0:
            return await interaction.response.send_message("❌ Số tiền không hợp lệ!", ephemeral=True)

        if user["money"] < amount:
            return await interaction.response.send_message("❌ Bạn không đủ xu!", ephemeral=True)

        await interaction.response.send_message("🎰 Bắt đầu quay xèng...", ephemeral=False)
        msg = await interaction.original_response()

        # Quay với tỉ lệ Jackpot 20%
        slots = ["❓", "❓", "❓"]
        final_result = roll_slots()

        for i in range(3):
            await asyncio.sleep(2)
            slots[i] = final_result[i]
            anim_embed = discord.Embed(
                title="🎰 Đang quay...",
                description=" | ".join(slots),
                color=discord.Color.orange()
            )
            await msg.edit(embed=anim_embed)

        await asyncio.sleep(1)

        # Tính kết quả
        symbol = pick.value
        count = final_result.count(symbol)
        if count == 3:
            win = amount * 3   # Jackpot ăn x3
            result_text = f"🎉 JACKPOT! Ba {symbol} trùng khớp!"
        elif count == 2:
            win = amount * 2
            result_text = f"🥳 Hai {symbol} trùng khớp!"
        elif count == 1:
            win = amount
            result_text = f"😐 Một {symbol}, hoàn tiền."
        else:
            win = 0
            result_text = f"😢 Không có {symbol} nào, thua rồi..."

        # Cập nhật dữ liệu
        user["money"] -= amount
        user["money"] += win
        user["last_slot"] = datetime.utcnow().isoformat()
        save_data()

        # Hiển thị kết quả
        result_embed = discord.Embed(title="🎰 Kết quả Xèng May Mắn", color=discord.Color.gold())
        result_embed.add_field(name="Kết quả", value=" | ".join(final_result), inline=False)
        result_embed.add_field(name="Bạn chọn", value=f"{symbol}", inline=True)
        result_embed.add_field(name="💬 Kết luận", value=result_text, inline=False)
        result_embed.add_field(name="💰 Tiền cược", value=f"{amount:,} xu", inline=True)
        result_embed.add_field(name="🏆 Nhận được", value=f"{win:,} xu", inline=True)
        result_embed.add_field(name="🪙 Số dư", value=f"{user['money']:,} xu", inline=False)

        await msg.edit(embed=result_embed)


async def setup(bot):
    await bot.add_cog(XungXeng(bot))

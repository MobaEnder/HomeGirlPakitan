import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from utils.data import DATA  # dùng bộ nhớ RAM đã load/autosave

# =========================
# Cấu hình bậc xếp hạng
# =========================
TIERS = [
    (0,     3000,  "Đồng",             "🟤"),
    (30001,  60000,  "Bạc",            "⬜"),
    (60001,  100000, "Vàng",           "🟨"),
    (100001, 200000, "Lục bảo",        "🟩"),
    (200001, 500000, "Kim cương",      "🟪"),
    (500001, float("inf"), "Đế vương", "🟥"),
]

def get_tier(money: int):
    for low, high, name, emoji in TIERS:
        if low <= money <= high:
            return name, emoji
    return "Vô danh", "💠"

def fmt_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")

class BangXepHang(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bangxephang", description="🏆 Bảng xếp hạng top 10 người giàu nhất")
    async def bangxephang(self, interaction: discord.Interaction):
        guild = interaction.guild

        # defer để tránh lỗi Unknown interaction
        await interaction.response.defer(thinking=False, ephemeral=False)

        users = []
        for uid_str, u in DATA.items():
            try:
                money = int(u.get("money", 0))
            except (TypeError, ValueError):
                money = 0
            users.append((uid_str, money))

        if not users:
            return await interaction.followup.send(
                "😶 Chưa có dữ liệu người chơi nào để xếp hạng!",
                ephemeral=True
            )

        users.sort(key=lambda x: x[1], reverse=True)
        top10 = users[:10]

        title_bar = "✨💰 **BẢNG XẾP HẠNG ĐẠI GIA** 💰✨"
        subtitle = "Top 10 người giàu nhất server • Cập nhật theo số dư hiện tại"

        embed = discord.Embed(
            title="🏆 TOP RICH LIST",
            description=f"{subtitle}\n\n",
            color=discord.Color.gold()
        )

        icon_url = guild.icon.url if guild and guild.icon else None
        embed.set_author(name="Casino Hub", icon_url=icon_url)
        embed.set_thumbnail(url="https://em-content.zobj.net/source/microsoft-teams/337/money-bag_1f4b0.png")
        embed.set_footer(text="⏳ Tin nhắn sẽ tự xoá sau 60 giây")

        lines = []
        for idx, (uid_str, money) in enumerate(top10, start=1):
            tier_name, tier_emoji = get_tier(money)

            if idx == 1:
                rank_icon = "🥇"
            elif idx == 2:
                rank_icon = "🥈"
            elif idx == 3:
                rank_icon = "🥉"
            else:
                rank_icon = f"#{idx}"

            display = f"<@{uid_str}>"
            member = None
            try:
                if guild:
                    member = guild.get_member(int(uid_str)) or await guild.fetch_member(int(uid_str))
            except Exception:
                member = None
            if member:
                if idx <= 3:
                    name_txt = f"**{member.display_name}**"
                else:
                    name_txt = f"{member.display_name}"
            else:
                name_txt = f"Người chơi `{uid_str}`"

            line = (
                f"{rank_icon} {tier_emoji} **{tier_name}** • "
                f"{name_txt} — **{fmt_num(money)} xu**"
            )
            lines.append(line)

        embed.add_field(name=title_bar, value="\n".join(lines), inline=False)

        embed.add_field(
            name="🎖️ Huy hiệu",
            value="🟤 Đồng • ⬜ Bạc • 🟨 Vàng • 🟩 Lục bảo • 🟪 Kim cương • 🟥 Đế vương",
            inline=False
        )

        msg = await interaction.followup.send(embed=embed, wait=True)

        try:
            for left in range(10, 0, -1):
                await asyncio.sleep(5)
                embed.set_footer(text=f"⏳ Tự xoá sau {left*5}s")
                await msg.edit(embed=embed)
        except discord.HTTPException:
            pass

        await asyncio.sleep(10)
        try:
            await msg.delete()
        except discord.NotFound:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(BangXepHang(bot))

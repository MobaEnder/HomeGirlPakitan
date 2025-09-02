import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import asyncio

from utils.data import get_user, DATA, save_data

# 🎣 Danh sách cá (tên chỉ để hiển thị; giá trị sẽ random 10-150)
FISH_LIST = [
    "🐟 Cá Trắm",
    "🐠 Cá Hề",
    "🐡 Cá Nóc",
    "🦈 Cá Mập Con",
    "🐬 Cá Heo Nhỏ",
    "🐳 Cá Voi Mini",
    "🦑 Mực",
    "🦐 Tôm",
    "🦞 Tôm Hùm",
    "🦀 Cua",
    "🐋 Cá Nhà Táng",
    "🐙 Bạch Tuộc",
    "🐊 Cá Sấu Mini",
    "🐌 Ốc Biển",
    "🦦 Rái Cá",
]

# ⛏️ Danh sách quặng (tên chỉ để hiển thị; giá trị sẽ random 10-150)
STONE_LIST = [
    "💎 Kim Cương",
    "🔶 Thạch Anh Vàng",
    "🔷 Saphia Xanh",
    "🔹 Topaz",
    "⚪ Ngọc Trắng",
    "🟣 Amethyst",
    "🟢 Emerald",
    "🔴 Ruby",
    "🟠 Citrine",
    "🟡 Yellow Sapphire",
    "🟤 Garnet",
    "⚫ Obsidian",
    "🔵 Aquamarine",
    "🟣 Tanzanite",
    "🟢 Peridot",
]


class WorkAll(commands.Cog):
    """/work chạy 3 hoạt động: làm việc, câu cá, đào đá — hiển thị gộp 1 embed"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="work", description="💼 Làm việc (thực hiện: làm việc, câu cá, đào đá cùng lúc)")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        now = time.time()

        # Nếu đang bị giam giữ -> không thể làm gì
        jailed_until = user_data.get("jailed_until", 0)
        if jailed_until > now:
            remaining = int(jailed_until - now)
            mins, secs = divmod(remaining, 60)
            embed_jail = discord.Embed(
                title="🚨 Bị Giam Giữ",
                description=f"Bạn đang bị giam, không thể làm việc.\n⏳ Thời gian còn lại: **{mins}m {secs}s**",
                color=discord.Color.red()
            )
            embed_jail.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/565/565445.png")
            return await interaction.response.send_message(embed=embed_jail, ephemeral=True)

        # Cooldown kiểm tra cho từng hoạt động (60s mỗi hoạt động)
        keys = {
            "normal": user_data.get("last_work_normal", 0),
            "fish": user_data.get("last_work_fish", 0),
            "stone": user_data.get("last_work_stone", 0),
        }
        remaining_map = {}
        cooldown_sec = 60
        blocked = False
        for k, t in keys.items():
            left = int(max(0, cooldown_sec - (now - t)))
            if left > 0:
                blocked = True
                remaining_map[k] = left

        if blocked:
            # Nếu 1 trong 3 vẫn cooldown -> báo ephemeral và không chạy
            lines = []
            names = {"normal": "Làm việc", "fish": "Câu cá", "stone": "Đào đá"}
            for k in ["normal", "fish", "stone"]:
                if k in remaining_map:
                    left = remaining_map[k]
                    m, s = divmod(left, 60)
                    if m > 0:
                        timestr = f"{m}m {s}s"
                    else:
                        timestr = f"{s}s"
                    lines.append(f"• **{names[k]}**: còn **{timestr}**")
                else:
                    lines.append(f"• **{names[k]}**: sẵn sàng ✅")

            embed_cd = discord.Embed(
                title="⏳ Có hoạt động đang hồi chiêu",
                description="\n".join(lines),
                color=discord.Color.orange()
            )
            embed_cd.set_footer(text="Tất cả 3 hoạt động cần sẵn sàng để sử dụng /work đồng thời.")
            return await interaction.response.send_message(embed=embed_cd, ephemeral=True)

        # Tất cả 3 hoạt động sẵn sàng -> thực hiện cả 3
        # 1) Làm việc (normal): random 10-150
        earned_work = random.randint(10, 150)

        # 2) Câu cá: chọn 1 loài, value random 10-150
        fish_name = random.choice(FISH_LIST)
        fish_value = random.randint(10, 150)
        # để thêm chút biến thiên, số lượng cá 1-3 nhưng tổng không vượt 150
        fish_amount = random.randint(1, 3)
        earned_fish = fish_value * fish_amount
        if earned_fish > 150:
            earned_fish = random.randint(10, 150)

        # 3) Đào đá: chọn 1 quặng, value random 10-150
        stone_name = random.choice(STONE_LIST)
        earned_stone = random.randint(10, 150)

        # Tổng cộng
        total_earned = earned_work + earned_fish + earned_stone

        # Cập nhật tiền & thời gian cooldown riêng cho từng hoạt động
        user_data["money"] = user_data.get("money", 0) + total_earned
        user_data["last_work_normal"] = now
        user_data["last_work_fish"] = now
        user_data["last_work_stone"] = now
        save_data()

        # Tạo embed gọn, thoáng, đẹp
        emb = discord.Embed(
            title="💼 Kết quả /work — Đã thực hiện 3 hoạt động",
            description=(
                "Bạn vừa hoàn thành **3 hoạt động** trong 1 lần gọi `/work`:\n\n"
            ),
            color=discord.Color.blurple()
        )

        # Cá nhân hóa hiển thị từng dòng với khoảng cách thoáng
        emb.add_field(
            name="💼 Làm việc",
            value=f"• Thu nhập: **{earned_work:,} xu**\n• Mô tả: Đi làm ăn lương ngẫu nhiên",
            inline=False
        )

        emb.add_field(
            name="🎣 Câu cá",
            value=f"• Tên: **{fish_name}** ×{fish_amount}\n• Thu nhập: **{earned_fish:,} xu**",
            inline=False
        )

        emb.add_field(
            name="⛏️ Đào đá",
            value=f"• Tên: **{stone_name}**\n• Thu nhập: **{earned_stone:,} xu**",
            inline=False
        )

        emb.add_field(
            name="🔸 Tổng nhận",
            value=f"**{total_earned:,} xu**",
            inline=False
        )

        emb.add_field(
            name="💳 Số dư hiện tại",
            value=f"**{user_data['money']:,} xu**",
            inline=False
        )

        emb.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây — giữ kênh gọn gàng ✨")
        emb.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1057/1057248.png")
        emb.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        # Gửi embed rồi tự xóa sau 30s
        await interaction.response.send_message(embed=emb)
        message = await interaction.original_response()
        await asyncio.sleep(30)
        try:
            await message.delete()
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(WorkAll(bot))

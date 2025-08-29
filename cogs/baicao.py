import discord
from discord import app_commands
from discord.ext import commands
import random, asyncio, time

from utils.data import get_user, save_data, DATA


ROOMS = {}  # Lưu phòng tạm trong RAM


def tinh_diem(ba):
    """Tính điểm bài cào (3 lá, mỗi lá 1-10 điểm)"""
    return sum(ba) % 10


class JoinButton(discord.ui.View):
    def __init__(self, room_id: str):
        super().__init__(timeout=None)
        self.room_id = room_id

    @discord.ui.button(label="🎴 Tham gia", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        if self.room_id not in ROOMS:
            return await interaction.response.send_message("❌ Phòng không tồn tại!", ephemeral=True)

        room = ROOMS[self.room_id]

        if room["started"]:
            return await interaction.response.send_message("❌ Phòng đã bắt đầu!", ephemeral=True)

        if user_id in room["players"]:
            return await interaction.response.send_message("❌ Bạn đã tham gia rồi!", ephemeral=True)

        if len(room["players"]) >= room["so_nguoi"]:
            return await interaction.response.send_message("❌ Phòng đã đủ người!", ephemeral=True)

        # check tiền cược
        if user_data["money"] < room["cuoc"]:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để tham gia!", ephemeral=True)

        room["players"].append(user_id)
        await interaction.response.send_message(f"✅ {interaction.user.mention} đã tham gia phòng {self.room_id}")

        # Nếu đủ người → bắt đầu
        if len(room["players"]) == room["so_nguoi"]:
            room["started"] = True
            await start_game(interaction, self.room_id)


async def start_game(interaction: discord.Interaction, room_id: str):
    room = ROOMS[room_id]
    players = room["players"]
    cuoc = room["cuoc"]

    # Trừ tiền cược của tất cả
    for uid in players:
        get_user(DATA, uid)["money"] -= cuoc
    save_data()

    # Gửi embed ban đầu
    embed = discord.Embed(
        title=f"🎴 Phòng {room_id} đã đủ người!",
        description=f"Trò chơi sẽ bắt đầu sau **7** giây...",
        color=discord.Color.yellow()
    )
    msg = await interaction.followup.send(embed=embed, wait=True)

    # Đếm ngược trong cùng 1 embed
    for i in range(7, 0, -1):
        embed.description = f"Trò chơi sẽ bắt đầu sau **{i}** giây..."
        await msg.edit(embed=embed)
        await asyncio.sleep(1)

    # Chia bài & tính điểm
    ket_qua = {}
    for uid in players:
        bai = [random.randint(1, 10) for _ in range(3)]
        diem = tinh_diem(bai)
        ket_qua[uid] = {"bai": bai, "diem": diem}

    # Tìm người thắng
    max_diem = max(p["diem"] for p in ket_qua.values())
    winners = [uid for uid, info in ket_qua.items() if info["diem"] == max_diem]

    # Tổng tiền thắng
    tong_tien = cuoc * len(players)
    tien_moi_nguoi = tong_tien // len(winners)

    # Cộng tiền cho người thắng
    for uid in winners:
        get_user(DATA, uid)["money"] += tien_moi_nguoi
    save_data()

    # Tạo embed kết quả
    result_embed = discord.Embed(
        title="🎴 Kết quả Bài Cào 🎴",
        color=discord.Color.green()
    )
    for uid, info in ket_qua.items():
        member = await interaction.guild.fetch_member(uid)
        result_embed.add_field(
            name=member.display_name,
            value=f"🃏 Bài: {info['bai']} | ⭐ Điểm: **{info['diem']}**",
            inline=False
        )

    if len(winners) == 1:
        win_member = await interaction.guild.fetch_member(winners[0])
        result_embed.add_field(
            name="🏆 Người thắng",
            value=f"{win_member.mention} (+{tong_tien} xu)",
            inline=False
        )
    else:
        result_embed.add_field(
            name="🤝 Đồng thắng",
            value=" ".join([f"<@{uid}>" for uid in winners]) + f"\n(+{tien_moi_nguoi} xu mỗi người)",
            inline=False
        )

    await msg.edit(embed=result_embed)

    # Xóa phòng
    del ROOMS[room_id]


class BaiCao(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="baicao", description="🎴 Chơi bài cào")

    @group.command(name="taophong", description="🎴 Tạo phòng bài cào")
    @app_commands.describe(so_nguoi="Số người chơi (2-4)", cuoc="Số tiền cược")
    async def taophong(self, interaction: discord.Interaction, so_nguoi: int, cuoc: int):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        if user_data["money"] < cuoc:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để tạo phòng!", ephemeral=True)

        if so_nguoi not in [2, 3, 4]:
            return await interaction.response.send_message("❌ Chỉ được tạo phòng từ 2-4 người!", ephemeral=True)

        room_id = str(int(time.time()))
        ROOMS[room_id] = {
            "owner": user_id,
            "so_nguoi": so_nguoi,
            "cuoc": cuoc,
            "players": [user_id],
            "started": False
        }

        view = JoinButton(room_id)
        await interaction.response.send_message(
            f"🎴 {interaction.user.mention} đã tạo phòng **{room_id}**\n"
            f"👥 Số người: **{so_nguoi}**\n"
            f"💰 Tiền cược: **{cuoc} xu**\n"
            f"👉 Bấm nút bên dưới để tham gia!",
            view=view
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(BaiCao(bot))

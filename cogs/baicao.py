import discord
from discord import app_commands
from discord.ext import commands
import random, asyncio

from utils.data import get_user, save_data, DATA

ROOMS = {}  # Lưu phòng tạm trong RAM


def tinh_diem(ba):
    return sum(ba) % 10


class JoinButton(discord.ui.View):
    def __init__(self, room_id: int):
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

        if user_data["money"] < room["cuoc"]:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để tham gia!", ephemeral=True)

        # Người chơi tham gia
        room["players"].append(user_id)
        await interaction.response.send_message(f"✅ {interaction.user.mention} đã tham gia!")

        # Nếu đủ người → bắt đầu
        if len(room["players"]) == room["so_nguoi"]:
            room["started"] = True
            await start_game(interaction, self.room_id)


async def start_game(interaction: discord.Interaction, room_id: int):
    room = ROOMS[room_id]
    players = room["players"]
    cuoc = room["cuoc"]

    # Trừ tiền cược
    for uid in players:
        get_user(DATA, uid)["money"] -= cuoc
    save_data()

    # Đếm ngược trong embed
    embed = discord.Embed(
        title="🎴 Ván Bài Cào sắp bắt đầu 🎴",
        description=f"⏳ Chuẩn bị...",
        color=discord.Color.gold()
    )
    msg = await interaction.followup.send(embed=embed, wait=True)

    for i in range(5, 0, -1):
        embed.description = f"⏳ Trò chơi bắt đầu sau **{i}** giây..."
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

    # Cộng tiền
    for uid in winners:
        get_user(DATA, uid)["money"] += tien_moi_nguoi
    save_data()

    # Tạo embed kết quả
    result_embed = discord.Embed(
        title="🏆 Kết quả Bài Cào 🏆",
        color=discord.Color.green()
    )
    for uid, info in ket_qua.items():
        member = await interaction.guild.fetch_member(uid)
        money = get_user(DATA, uid)["money"]
        result_embed.add_field(
            name=member.display_name,
            value=f"🃏 Bài: {info['bai']} | ⭐ Điểm: **{info['diem']}**\n💰 Số dư mới: **{money} xu**",
            inline=False
        )

    if len(winners) == 1:
        win_member = await interaction.guild.fetch_member(winners[0])
        result_embed.add_field(
            name="👑 Người thắng",
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

    # Xóa phòng sau 30s
    await asyncio.sleep(30)
    await msg.delete()
    del ROOMS[room_id]


class BaiCao(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="baicao", description="🎴 Chơi bài cào")

    @group.command(name="taophong", description="🎴 Tạo phòng bài cào")
    @app_commands.describe(so_nguoi="Số người chơi (1-4, 1 = đấu nhà cái)", cuoc="Số tiền cược")
    async def taophong(self, interaction: discord.Interaction, so_nguoi: int, cuoc: int):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        if user_data["money"] < cuoc:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để tạo phòng!", ephemeral=True)

        if so_nguoi not in [1, 2, 3, 4]:
            return await interaction.response.send_message("❌ Chỉ được tạo phòng từ 1-4 người!", ephemeral=True)

        # Tạo ID phòng ngắn
        import random
        room_id = random.randint(0, 100)
        while room_id in ROOMS:
            room_id = random.randint(0, 100)

        ROOMS[room_id] = {
            "owner": user_id,
            "so_nguoi": so_nguoi,
            "cuoc": cuoc,
            "players": [user_id],
            "started": False
        }

        view = JoinButton(room_id)
        embed = discord.Embed(
            title="🎴 Phòng Bài Cào 🎴",
            description=f"👤 Chủ phòng: {interaction.user.mention}\n"
                        f"👥 Số người: **{so_nguoi}**\n"
                        f"💰 Tiền cược: **{cuoc} xu**\n\n"
                        f"👉 Bấm nút bên dưới để tham gia!",
            color=discord.Color.blurple()
        )
        msg = await interaction.response.send_message(embed=embed, view=view)
        # Xóa phòng sau 30s nếu chưa chơi
        await asyncio.sleep(30)
        if room_id in ROOMS and not ROOMS[room_id]["started"]:
            del ROOMS[room_id]
            m = await interaction.original_response()
            await m.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(BaiCao(bot))

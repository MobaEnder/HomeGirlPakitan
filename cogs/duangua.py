import discord
from discord import app_commands
from discord.ext import commands
import random, asyncio, secrets

from utils.data import get_user, save_data, DATA

ROOMS = {}  # lưu các phòng đua ngựa


class HorseButtons(discord.ui.View):
    def __init__(self, room_id: str):
        super().__init__(timeout=180)
        self.room_id = room_id
        for i in range(1, 8):
            self.add_item(
                discord.ui.Button(
                    label=f"🐎 Ngựa {i}",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"horse_{i}"
                )
            )
        for child in self.children:
            child.callback = self.button_callback

    async def button_callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        room = ROOMS[self.room_id]

        if room["started"]:
            return await interaction.response.send_message("❌ Phòng đã bắt đầu!", ephemeral=True)

        if user_id in room["players"]:
            return await interaction.response.send_message("❌ Bạn đã chọn ngựa rồi!", ephemeral=True)

        # kiểm tra tiền cược
        user_data = get_user(DATA, user_id)
        if user_data["money"] < room["cuoc"]:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để tham gia!", ephemeral=True)

        # trừ tiền
        user_data["money"] -= room["cuoc"]
        save_data()

        horse = int(interaction.data["custom_id"].split("_")[1])
        room["players"][user_id] = horse

        await interaction.response.send_message(
            f"✅ {interaction.user.mention} đã chọn **Ngựa {horse}**", ephemeral=False
        )

        # nếu đủ số người → bắt đầu
        if len(room["players"]) == room["so_nguoi"]:
            room["started"] = True
            await start_race(interaction, self.room_id)


async def start_race(interaction: discord.Interaction, room_id: str):
    room = ROOMS[room_id]

    msg = await interaction.followup.send(f"🐎 Phòng **{room_id}** đã đủ người! Bắt đầu sau 5 giây...")
    for i in range(5, 0, -1):
        await msg.edit(content=f"🐎 Cuộc đua bắt đầu sau **{i}s**...")
        await asyncio.sleep(1)

    # danh sách ngựa
    track_length = 20
    positions = [0] * 7
    race_msg = await interaction.followup.send("🏁 **ĐUA NGỰA** 🏁\n")
    winner = None

    while not winner:
        await asyncio.sleep(1)
        move_horse = random.randint(0, 6)
        positions[move_horse] += random.randint(1, 3)
        if positions[move_horse] >= track_length:
            positions[move_horse] = track_length
            winner = move_horse + 1

        text = "🏁 **ĐUA NGỰA** 🏁\n"
        for i in range(7):
            track = "·" * positions[i] + "🐎" + "·" * (track_length - positions[i])
            text += f"Ngựa {i+1}: {track}\n"

        await race_msg.edit(content=text)

    # tìm người thắng cược
    winners = [uid for uid, horse in room["players"].items() if horse == winner]
    prize = room["cuoc"] * 4

    result_text = f"\n🏆 **Ngựa {winner} đã về đích!**\n"
    if winners:
        for uid in winners:
            get_user(DATA, uid)["money"] += prize
        save_data()
        result_text += f"🎉 Người thắng: {' '.join([f'<@{uid}>' for uid in winners])} (+{prize} xu mỗi người)"
    else:
        result_text += "❌ Không ai đoán đúng!"

    result_msg = await interaction.followup.send(result_text)

    # xoá phòng
    if room_id in ROOMS:
        del ROOMS[room_id]

    # tự xoá toàn bộ sau 30s
    await asyncio.sleep(30)
    for m in [msg, race_msg, result_msg]:
        try:
            await m.delete()
        except:
            pass


class DuaNgua(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="duangua", description="🐎 Đua ngựa")

    @group.command(name="taophong", description="🐎 Tạo phòng đua ngựa")
    @app_commands.describe(so_nguoi="Số người chơi (2-10)", cuoc="Số tiền cược")
    async def taophong(self, interaction: discord.Interaction, so_nguoi: int, cuoc: int):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        if so_nguoi < 2 or so_nguoi > 10:
            return await interaction.response.send_message("❌ Số người chơi phải từ 2 đến 10!", ephemeral=True)

        if user_data["money"] < cuoc:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để tạo phòng!", ephemeral=True)

        # tạo ID phòng ngắn gọn (6 ký tự hex)
        room_id = secrets.token_hex(3).upper()
        ROOMS[room_id] = {
            "owner": user_id,
            "so_nguoi": so_nguoi,
            "cuoc": cuoc,
            "players": {},
            "started": False
        }

        view = HorseButtons(room_id)
        embed = discord.Embed(
            title="🐎 Phòng Đua Ngựa",
            description=(
                f"👑 Chủ phòng: {interaction.user.mention}\n"
                f"👥 Số người: **{so_nguoi}**\n"
                f"💰 Tiền cược: **{cuoc} xu**\n\n"
                f"👉 Nhấn nút để chọn ngựa bạn muốn đặt cược!"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Mã phòng: {room_id}")

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(DuaNgua(bot))

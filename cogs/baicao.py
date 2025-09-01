import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import json
import os

DATA_FILE = "data.json"
ROOMS = {}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=4)

def get_user(data, user_id):
    if str(user_id) not in data:
        data[str(user_id)] = {"money": 10000}
    return data[str(user_id)]

DATA = load_data()

def tinh_diem(bai):
    return sum(bai) % 10

class JoinButton(discord.ui.View):
    def __init__(self, room_id):
        super().__init__(timeout=30)
        self.room_id = room_id

    @discord.ui.button(label="Tham gia phòng 🎮", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        room = ROOMS.get(self.room_id)
        if not room:
            return await interaction.response.send_message("❌ Phòng không tồn tại!", ephemeral=True)

        if interaction.user.id in room["players"]:
            return await interaction.response.send_message("❌ Bạn đã trong phòng!", ephemeral=True)

        if len(room["players"]) >= room["so_nguoi"]:
            return await interaction.response.send_message("❌ Phòng đã đủ người!", ephemeral=True)

        room["players"].append(interaction.user.id)
        await interaction.response.send_message(f"✅ {interaction.user.mention} đã tham gia phòng!")

        if len(room["players"]) == room["so_nguoi"]:
            await start_game(interaction, self.room_id)

async def start_game(interaction: discord.Interaction, room_id: int, bot_vs_dealer=False):
    room = ROOMS[room_id]
    players = room["players"]
    cuoc = room["cuoc"]

    # Trừ tiền cược
    for uid in players:
        get_user(DATA, uid)["money"] -= cuoc
    save_data()

    embed = discord.Embed(title="🎴 Ván Bài Cào sắp bắt đầu 🎴", color=discord.Color.gold())
    msg = await interaction.followup.send(embed=embed, wait=True)

    for i in range(5, 0, -1):
        embed.description = f"⏳ Trò chơi bắt đầu sau **{i}** giây..."
        await msg.edit(embed=embed)
        await asyncio.sleep(1)

    ket_qua = {}
    for uid in players:
        bai = [random.randint(1, 10) for _ in range(3)]
        ket_qua[uid] = {"bai": bai, "diem": tinh_diem(bai)}

    if bot_vs_dealer:
        dealer_bai = [random.randint(1, 10) for _ in range(3)]
        ket_qua["dealer"] = {"bai": dealer_bai, "diem": tinh_diem(dealer_bai)}

    # Xác định người thắng
    max_diem = max(info["diem"] for info in ket_qua.values())
    winners = [uid for uid, info in ket_qua.items() if info["diem"] == max_diem]

    tong_tien = cuoc * (2 if bot_vs_dealer else len(players))
    tien_moi_nguoi = tong_tien // len(winners)

    if bot_vs_dealer:
        if "dealer" in winners:
            # Nhà cái thắng
            pass
        else:
            for uid in winners:
                get_user(DATA, uid)["money"] += tong_tien
        save_data()
    else:
        for uid in winners:
            get_user(DATA, uid)["money"] += tien_moi_nguoi
        save_data()

    # Hiển thị kết quả
    result_embed = discord.Embed(title="🏆 Kết quả Bài Cào 🏆", color=discord.Color.green())
    for uid, info in ket_qua.items():
        if uid == "dealer":
            result_embed.add_field(
                name="🤖 Nhà Cái",
                value=f"🃏 {info['bai']} | ⭐ {info['diem']}",
                inline=False
            )
        else:
            member = await interaction.guild.fetch_member(uid)
            money = get_user(DATA, uid)["money"]
            result_embed.add_field(
                name=member.display_name,
                value=f"🃏 {info['bai']} | ⭐ {info['diem']}\n💰 {money} xu",
                inline=False
            )

    await msg.edit(embed=result_embed)
    await asyncio.sleep(30)
    await msg.delete()
    del ROOMS[room_id]

class BaiCao(commands.Cog):
    def __init__(self, bot):
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

        if so_nguoi == 1:
            await interaction.response.send_message(f"🎴 Bạn đã tạo phòng đấu với **Nhà Cái** (cược {cuoc} xu)!")
            await start_game(interaction, room_id, bot_vs_dealer=True)
            return

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
        await asyncio.sleep(30)
        if room_id in ROOMS and not ROOMS[room_id]["started"]:
            del ROOMS[room_id]
            m = await interaction.original_response()
            await m.delete()

async def setup(bot):
    await bot.add_cog(BaiCao(bot))

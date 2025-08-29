import discord
from discord import app_commands
from discord.ext import commands
import random, asyncio, time
from utils.data import get_user, DATA, save_data

ROOMS = {}
MAX_HEALTH = 3
TRACK_LEN = 12  # chiều dài track

class DaGaButtons(discord.ui.View):
    def __init__(self, room_id: str):
        super().__init__(timeout=60)
        self.room_id = room_id
        self.add_item(discord.ui.Button(label="🐓 Gà Đỏ", style=discord.ButtonStyle.danger, custom_id="red"))
        self.add_item(discord.ui.Button(label="🐓 Gà Vàng", style=discord.ButtonStyle.primary, custom_id="yellow"))
        for child in self.children:
            child.callback = self.button_callback

    async def button_callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        room = ROOMS[self.room_id]

        if user_id not in room["allowed"]:
            return await interaction.response.send_message("❌ Bạn không được tham gia phòng này!", ephemeral=True)
        if user_id in room["players"]:
            return await interaction.response.send_message("❌ Bạn đã chọn gà rồi!", ephemeral=True)

        chosen_color = interaction.data["custom_id"]
        if chosen_color in [p["color"] for p in room["players"].values()]:
            return await interaction.response.send_message("❌ Con gà này đã được chọn!", ephemeral=True)

        user_data = get_user(DATA, user_id)
        if user_data["money"] < room["cuoc"]:
            return await interaction.response.send_message("💸 Bạn không đủ tiền tham gia!", ephemeral=True)

        # Trừ tiền và lưu lựa chọn
        user_data["money"] -= room["cuoc"]
        save_data()
        room["players"][user_id] = {"color": chosen_color, "health": MAX_HEALTH}

        confirm_msg = await interaction.response.send_message(
            f"✅ {interaction.user.mention} đã chọn **Gà {'Đỏ' if chosen_color=='red' else 'Vàng'}**", ephemeral=False
        )
        await asyncio.sleep(5)
        try: await confirm_msg.delete()
        except: pass

        if len(room["players"]) == 2 and not room["started"]:
            room["started"] = True
            try: await interaction.message.delete()
            except: pass
            await start_daga(interaction, self.room_id)

async def start_daga(interaction: discord.Interaction, room_id: str):
    room = ROOMS[room_id]
    players = list(room["players"].keys())
    bets = room["cuoc"]

    pos = {players[0]: 0, players[1]: TRACK_LEN}
    velocities = {players[0]: 1, players[1]: -1}

    msg = await interaction.followup.send("🐓 **Trận Đấu Đang Diễn Ra** 🐓")

    for t in range(15):
        await asyncio.sleep(0.7)

        # Cập nhật vị trí
        for p in players:
            pos[p] += velocities[p]
            if pos[p] < 0: pos[p]=0
            if pos[p] > TRACK_LEN: pos[p]=TRACK_LEN

        # Va chạm -> giảm máu + đẩy ngẫu nhiên
        if abs(pos[players[0]] - pos[players[1]]) <= 0:
            room["players"][players[0]]["health"] -= 1
            room["players"][players[1]]["health"] -= 1
            # đẩy nhau ngẫu nhiên
            velocities[players[0]] = random.choice([-1,1])
            velocities[players[1]] = -velocities[players[0]]

        # Tạo track
        track = ""
        for i in range(TRACK_LEN+1):
            char = "·"
            if i==pos[players[0]] and i==pos[players[1]]:
                char="💥🐓💥"
            elif i==pos[players[0]]:
                char="🔴" if room["players"][players[0]]["color"]=="red" else "🟡"
            elif i==pos[players[1]]:
                char="🔴" if room["players"][players[1]]["color"]=="red" else "🟡"
            track += char

        health0 = "❤️"*room["players"][players[0]]["health"]
        health1 = "❤️"*room["players"][players[1]]["health"]

        text = f"🏁 **Đá Gà 1v1** 🏁\n{track}\n\n" \
               f"{interaction.guild.get_member(players[0]).mention} Máu: {health0}\n" \
               f"{interaction.guild.get_member(players[1]).mention} Máu: {health1}"

        await msg.edit(content=text)

        if room["players"][players[0]]["health"]<=0 or room["players"][players[1]]["health"]<=0:
            break

    # Xác định thắng thua
    if room["players"][players[0]]["health"]>room["players"][players[1]]["health"]:
        winner, loser = players[0], players[1]
    elif room["players"][players[1]]["health"]>room["players"][players[0]]["health"]:
        winner, loser = players[1], players[0]
    else:
        winner = random.choice(players)
        loser = players[0] if winner==players[1] else players[1]

    winner_data = get_user(DATA, winner)
    winner_data["money"] += bets*2
    save_data()

    await msg.delete()

    embed = discord.Embed(
        title="🏆 Kết Quả Đá Gà",
        description=(
            f"👑 Người Thắng: {interaction.guild.get_member(winner).mention} "
            f"(**Gà {'Đỏ' if room['players'][winner]['color']=='red' else 'Vàng'}**)\n"
            f"❌ Người Thua: {interaction.guild.get_member(loser).mention} "
            f"(**Gà {'Đỏ' if room['players'][loser]['color']=='red' else 'Vàng'}**)\n"
            f"💰 Thắng: **{bets*2} Xu**"
        ),
        color=discord.Color.gold()
    )
    embed.add_field(name="💳 Số Dư Người Thắng", value=f"**{winner_data['money']} Xu**", inline=False)
    embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây")
    final_msg = await interaction.followup.send(embed=embed)

    await asyncio.sleep(30)
    try: await final_msg.delete()
    except: pass
    if room_id in ROOMS: del ROOMS[room_id]

class DaGa(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="daga", description="🐓 Mini Game Đá Gà")

    @group.command(name="taophong", description="🏁 Tạo phòng đá gà 2 người")
    @app_commands.describe(member="Người chơi thứ 2", cuoc="Số tiền cược")
    async def taophong(self, interaction: discord.Interaction, member: discord.Member, cuoc: int):
        creator_id = interaction.user.id
        if member.id == creator_id:
            return await interaction.response.send_message("❌ Bạn không thể tạo phòng với chính mình!", ephemeral=True)

        creator_data = get_user(DATA, creator_id)
        member_data = get_user(DATA, member.id)
        if creator_data["money"]<cuoc:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để tạo phòng!", ephemeral=True)
        if member_data["money"]<cuoc:
            return await interaction.response.send_message(f"💸 {member.mention} không đủ tiền tham gia!", ephemeral=True)

        room_id = str(int(time.time()))
        ROOMS[room_id] = {"creator": creator_id, "allowed":[creator_id,member.id],"cuoc":cuoc,"players":{},"started":False}

        view = DaGaButtons(room_id)
        embed = discord.Embed(
            title="🏁 Phòng Đá Gà 1v1",
            description=f"💰 Tiền cược: **{cuoc} Xu**\n"
                        f"👥 Người chơi: {interaction.user.mention} và {member.mention}\n\n"
                        f"👉 Nhấn nút chọn Gà **Đỏ** hoặc **Vàng** (mỗi người 1 con)",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(DaGa(bot))

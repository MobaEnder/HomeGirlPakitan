import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

rooms = {}  # lưu trữ phòng {room_id: {...}}

class JoinView(discord.ui.View):
    def __init__(self, room_id, bet):
        super().__init__(timeout=None)
        self.room_id = room_id
        self.bet = bet

    @discord.ui.button(label="🎮 Tham gia", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        room = rooms.get(self.room_id)
        if not room:
            return await interaction.response.send_message("⚠️ Phòng không tồn tại!", ephemeral=True)

        if interaction.user.id in room["players"]:
            return await interaction.response.send_message("❌ Bạn đã tham gia phòng này rồi!", ephemeral=True)

        if len(room["players"]) >= room["max_players"]:
            return await interaction.response.send_message("⚠️ Phòng đã đầy!", ephemeral=True)

        room["players"][interaction.user.id] = {
            "user": interaction.user,
            "hand": [],
            "stand": False
        }

        # Cập nhật danh sách người chơi
        players_text = "\n".join([p["user"].mention for p in room["players"].values()])
        embed = discord.Embed(
            title=f"🃏 Phòng Xì Dách #{self.room_id}",
            description=f"💵 Tiền cược: **{room['bet']} xu**\n"
                        f"👥 Người chơi:\n{players_text}",
            color=discord.Color.green()
        )

        await room["message"].edit(embed=embed, view=self)

        # Nếu đủ số người chơi → bắt đầu sau 5s
        if len(room["players"]) == room["max_players"]:
            await interaction.response.send_message("✅ Đã đủ người, game sẽ bắt đầu sau **5s**!", ephemeral=True)
            await asyncio.sleep(5)
            await start_game(room)

async def start_game(room):
    deck = [str(v) + s for v in range(2, 11) for s in ["♠", "♥", "♦", "♣"]]
    deck += [v + s for v in ["J", "Q", "K", "A"] for s in ["♠", "♥", "♦", "♣"]]
    random.shuffle(deck)
    room["deck"] = deck

    # Chia 2 lá cho mỗi người
    for player in room["players"].values():
        player["hand"] = [deck.pop(), deck.pop()]

    await next_turn(room)

def calculate_score(hand):
    value = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        if rank in ["J", "Q", "K"]:
            value += 10
        elif rank == "A":
            value += 11
            aces += 1
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

async def next_turn(room):
    players = list(room["players"].values())
    if room.get("turn", 0) >= len(players):
        await end_game(room)
        return

    player = players[room["turn"]]
    user = player["user"]
    hand = player["hand"]
    score = calculate_score(hand)

    embed = discord.Embed(
        title=f"🎴 Lượt của {user.display_name}",
        description=f"🃏 Bài: {', '.join(hand)}\n"
                    f"⭐ Điểm hiện tại: **{score}**",
        color=discord.Color.blurple()
    )

    view = TurnView(room, user.id)
    await room["message"].edit(embed=embed, view=view)

class TurnView(discord.ui.View):
    def __init__(self, room, user_id):
        super().__init__(timeout=30)
        self.room = room
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="🎴 Bốc thêm", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.room["players"][self.user_id]
        card = self.room["deck"].pop()
        player["hand"].append(card)

        score = calculate_score(player["hand"])
        if score > 21:
            player["stand"] = True
            await interaction.response.send_message("💥 Bạn đã **quá 21 (Cháy)**!", ephemeral=True)
            self.room["turn"] += 1
            await next_turn(self.room)
        else:
            await interaction.response.send_message(f"🃏 Bạn rút được: **{card}** (Điểm: {score})", ephemeral=True)

    @discord.ui.button(label="✋ Dừng", style=discord.ButtonStyle.danger)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.room["players"][self.user_id]
        player["stand"] = True
        await interaction.response.send_message("✅ Bạn đã chọn **Dừng**.", ephemeral=True)
        self.room["turn"] += 1
        await next_turn(self.room)

async def end_game(room):
    results = []
    for player in room["players"].values():
        score = calculate_score(player["hand"])
        results.append((player["user"], score, player["hand"]))

    # Tìm người thắng
    valid = [(u, s, h) for (u, s, h) in results if s <= 21]
    if not valid:
        winner_text = "❌ Không ai thắng, tất cả đều cháy!"
    else:
        winner = max(valid, key=lambda x: x[1])
        winner_text = f"🏆 Người thắng: {winner[0].mention} với **{winner[1]} điểm** ({', '.join(winner[2])})"

    desc = "\n".join([f"{u.mention}: {s} điểm ({', '.join(h)})" for u, s, h in results])

    embed = discord.Embed(
        title="🎉 Kết quả Xì Dách",
        description=f"{desc}\n\n{winner_text}",
        color=discord.Color.gold()
    )
    await room["message"].edit(embed=embed, view=None)
    await asyncio.sleep(30)
    await room["message"].delete()
    del rooms[room["id"]]

class XiJack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="xijack", description="🎲 Chơi Xì Dách (Blackjack)")
    @app_commands.describe(
        players="Số người chơi (2-5)",
        bet="Số tiền cược"
    )
    async def xijack(self, interaction: discord.Interaction, players: int, bet: int):
        if players < 2 or players > 5:
            return await interaction.response.send_message("⚠️ Chỉ được chơi từ 2 đến 5 người!", ephemeral=True)

        room_id = len(rooms) + 1
        rooms[room_id] = {
            "id": room_id,
            "bet": bet,
            "max_players": players,
            "players": {interaction.user.id: {"user": interaction.user, "hand": [], "stand": False}},
            "turn": 0
        }

        embed = discord.Embed(
            title=f"🃏 Phòng Xì Dách #{room_id}",
            description=f"💵 Tiền cược: **{bet} xu**\n"
                        f"👥 Người chơi:\n{interaction.user.mention}\n\n"
                        f"👉 Bấm nút để tham gia!",
            color=discord.Color.green()
        )

        view = JoinView(room_id, bet)
        msg = await interaction.channel.send(embed=embed, view=view)  # ✅ dùng channel.send thay vì response
        rooms[room_id]["message"] = msg

        await interaction.response.send_message(f"✅ Phòng #{room_id} đã được tạo!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(XiJack(bot))

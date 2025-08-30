import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import time

from utils.data import get_user, DATA, save_data

# Bộ bài
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUES = {
    "A": 11, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

rooms = {}

class Xijack(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def calculate_score(self, hand):
        score = sum(VALUES[card[:-1]] for card in hand)
        aces = sum(1 for card in hand if card.startswith("A"))
        while score > 21 and aces:
            score -= 10
            aces -= 1
        return score

    def draw_card(self, deck):
        return deck.pop(random.randint(0, len(deck) - 1))

    @app_commands.command(name="xijack", description="🃏 Mini game Xì Dách (Blackjack)")
    async def xijack(self, interaction: discord.Interaction, players: int, bet: int):
        if players < 2 or players > 5:
            return await interaction.response.send_message("⚠️ Phòng phải từ **2–5 người**!", ephemeral=True)

        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        if bet <= 0 or user_data["money"] < bet:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để đặt cược!", ephemeral=True)

        room_id = interaction.channel.id
        if room_id in rooms:
            return await interaction.response.send_message("❌ Phòng này đã có game Xì Dách đang diễn ra!", ephemeral=True)

        # Tạo phòng
        rooms[room_id] = {
            "owner": user_id,
            "bet": bet,
            "max_players": players,
            "players": {user_id: {"hand": [], "stand": False}},
            "deck": [r + s for r in RANKS for s in SUITS],
            "turn_order": [],
            "current_turn": 0,
            "pot": 0,
            "message": None
        }

        embed = discord.Embed(
            title="🎰 Xì Dách (Blackjack)",
            description=f"💵 Tiền cược: **{bet} xu**\n👥 Người chơi: **{len(rooms[room_id]['players'])}/{players}**\n\n➡️ Nhấn **Tham gia** để vào phòng!",
            color=discord.Color.gold()
        )
        view = JoinView(room_id, self)

        msg = await interaction.response.send_message(embed=embed, view=view)
        rooms[room_id]["message"] = await interaction.original_response()


class JoinView(discord.ui.View):
    def __init__(self, room_id, cog):
        super().__init__(timeout=None)
        self.room_id = room_id
        self.cog = cog

    @discord.ui.button(label="🎮 Tham gia", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        room = rooms.get(self.room_id)
        if not room:
            return await interaction.response.send_message("❌ Phòng đã đóng!", ephemeral=True)

        user_id = interaction.user.id
        if user_id in room["players"]:
            return await interaction.response.send_message("⚠️ Bạn đã tham gia phòng rồi!", ephemeral=True)

        if len(room["players"]) >= room["max_players"]:
            return await interaction.response.send_message("⚠️ Phòng đã đủ người!", ephemeral=True)

        user_data = get_user(DATA, user_id)
        if user_data["money"] < room["bet"]:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để tham gia!", ephemeral=True)

        room["players"][user_id] = {"hand": [], "stand": False}
        room["pot"] += room["bet"]
        user_data["money"] -= room["bet"]
        save_data()

        # Update embed
        embed = discord.Embed(
            title="🎰 Xì Dách (Blackjack)",
            description=f"💵 Tiền cược: **{room['bet']} xu**\n👥 Người chơi: **{len(room['players'])}/{room['max_players']}**\n\n➡️ Nhấn **Tham gia** để vào phòng!",
            color=discord.Color.gold()
        )
        await room["message"].edit(embed=embed, view=self)

        # Nếu đủ người → bắt đầu
        if len(room["players"]) == room["max_players"]:
            await self.start_game(room, interaction)

    async def start_game(self, room, interaction):
        await room["message"].edit(content="⏳ Game bắt đầu sau **5s**...", view=None)
        await asyncio.sleep(5)

        # Chia bài
        for _ in range(2):
            for uid in room["players"]:
                card = self.cog.draw_card(room["deck"])
                room["players"][uid]["hand"].append(card)

        room["turn_order"] = list(room["players"].keys())
        room["current_turn"] = 0

        await self.next_turn(room, interaction)

    async def next_turn(self, room, interaction):
        if room["current_turn"] >= len(room["turn_order"]):
            return await self.end_game(room, interaction)

        uid = room["turn_order"][room["current_turn"]]
        player_hand = room["players"][uid]["hand"]
        score = self.cog.calculate_score(player_hand)

        if score > 21:  # cháy
            room["players"][uid]["stand"] = True
            room["current_turn"] += 1
            return await self.next_turn(room, interaction)

        embed = discord.Embed(
            title="🎴 Lượt chơi",
            description=f"👤 {interaction.guild.get_member(uid).mention}\nBài: {' '.join(player_hand)}\nĐiểm: **{score}**",
            color=discord.Color.blue()
        )
        view = ActionView(room, self.cog, interaction)
        await room["message"].edit(embed=embed, view=view)


class ActionView(discord.ui.View):
    def __init__(self, room, cog, interaction):
        super().__init__(timeout=20)
        self.room = room
        self.cog = cog
        self.interaction = interaction

    @discord.ui.button(label="🎴 Bốc thêm", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = self.room["turn_order"][self.room["current_turn"]]
        if interaction.user.id != uid:
            return await interaction.response.send_message("⛔ Không phải lượt của bạn!", ephemeral=True)

        card = self.cog.draw_card(self.room["deck"])
        self.room["players"][uid]["hand"].append(card)
        await self.cog.bot.get_cog("Xijack").next_turn(self.room, self.interaction)

    @discord.ui.button(label="✋ Dừng", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = self.room["turn_order"][self.room["current_turn"]]
        if interaction.user.id != uid:
            return await interaction.response.send_message("⛔ Không phải lượt của bạn!", ephemeral=True)

        self.room["players"][uid]["stand"] = True
        self.room["current_turn"] += 1
        await self.cog.bot.get_cog("Xijack").next_turn(self.room, self.interaction)


    async def end_game(self, room, interaction):
        results = []
        winner = None
        best_score = 0

        for uid, pdata in room["players"].items():
            score = self.cog.calculate_score(pdata["hand"])
            results.append(f"👤 {interaction.guild.get_member(uid).mention} → {' '.join(pdata['hand'])} ({score})")
            if score <= 21 and score > best_score:
                best_score = score
                winner = uid

        embed = discord.Embed(
            title="🏆 Kết quả Xì Dách",
            description="\n".join(results),
            color=discord.Color.green()
        )

        if winner:
            get_user(DATA, winner)["money"] += room["pot"]
            save_data()
            embed.add_field(name="🥇 Người thắng", value=interaction.guild.get_member(winner).mention, inline=False)
        else:
            embed.add_field(name="💥 Không ai thắng", value="Tất cả đều cháy!", inline=False)

        await room["message"].edit(embed=embed, view=None)
        del rooms[interaction.channel.id]

        await asyncio.sleep(30)
        try:
            await room["message"].delete()
        except:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Xijack(bot))

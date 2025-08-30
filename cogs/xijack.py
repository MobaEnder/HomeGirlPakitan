import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

# ------------------ VIEW: JOIN GAME ------------------ #
class JoinView(discord.ui.View):
    def __init__(self, cog, room):
        super().__init__(timeout=None)
        self.cog = cog
        self.room = room

    @discord.ui.button(label="🎮 Tham gia", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.room["players"]:
            await interaction.response.send_message("❌ Bạn đã tham gia rồi!", ephemeral=True)
            return
        if len(self.room["players"]) >= self.room["max_players"]:
            await interaction.response.send_message("❌ Phòng đã đầy!", ephemeral=True)
            return

        self.room["players"].append(interaction.user)

        embed = discord.Embed(
            title=f"♠️ Phòng Xì Dách - Cược {self.room['bet']} Xu",
            description=f"👥 Người chơi ({len(self.room['players'])}/{self.room['max_players']}):\n" +
                        "\n".join([p.mention for p in self.room["players"]]),
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)


# ------------------ VIEW: ACTION (HIT / STAND) ------------------ #
class ActionView(discord.ui.View):
    def __init__(self, cog, room, player):
        super().__init__(timeout=20)
        self.cog = cog
        self.room = room
        self.player = player

    @discord.ui.button(label="🎴 Bốc thêm", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player:
            await interaction.response.send_message("⏳ Không phải lượt của bạn!", ephemeral=True)
            return

        card = random.choice(self.cog.deck)
        self.room["hands"][interaction.user].append(card)

        score = self.cog.calculate_score(self.room["hands"][interaction.user])
        if score > 21:  # Cháy
            await interaction.response.send_message(f"💥 Bạn đã **quá 21 điểm** (Cháy)!", ephemeral=True)
            await self.cog.next_turn(self.room, interaction)
        else:
            hand_str = " | ".join(self.room["hands"][interaction.user])
            embed = discord.Embed(
                title=f"♠️ Lượt của bạn ({interaction.user.display_name})",
                description=f"🃏 Bài: {hand_str}\n✨ Điểm: {score}",
                color=discord.Color.blurple()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="✋ Dừng", style=discord.ButtonStyle.danger)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player:
            await interaction.response.send_message("⏳ Không phải lượt của bạn!", ephemeral=True)
            return

        await interaction.response.send_message("✅ Bạn đã chọn DỪNG!", ephemeral=True)
        await self.cog.next_turn(self.room, interaction)


# ------------------ MAIN COG ------------------ #
class Xijack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rooms = {}
        self.deck = self.generate_deck()

    def generate_deck(self):
        suits = ["♠", "♥", "♦", "♣"]
        values = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        return [f"{v}{s}" for s in suits for v in values]

    def calculate_score(self, hand):
        value_map = {"A": 11, "J": 10, "Q": 10, "K": 10}
        score = 0
        aces = 0
        for card in hand:
            v = card[:-1]
            if v in value_map:
                score += value_map[v]
                if v == "A":
                    aces += 1
            else:
                score += int(v)
        while score > 21 and aces:
            score -= 10
            aces -= 1
        return score

    @app_commands.command(name="xijack", description="♠️ Tạo phòng Xì Dách (Có nhà cái)")
    async def xijack(self, interaction: discord.Interaction, so_nguoi: int, tien_cuoc: int):
        if so_nguoi < 2 or so_nguoi > 5:
            await interaction.response.send_message("❌ Số người chơi phải từ 2 đến 5!", ephemeral=True)
            return

        room = {
            "host": interaction.user,
            "players": [interaction.user],
            "max_players": so_nguoi,
            "bet": tien_cuoc,
            "hands": {},
            "turn": -1,
            "message": None,
            "dealer": []  # Nhà cái
        }
        self.rooms[interaction.channel.id] = room

        embed = discord.Embed(
            title=f"♠️ Phòng Xì Dách - Cược {tien_cuoc} Xu",
            description=f"👥 Người chơi (1/{so_nguoi}):\n{interaction.user.mention}\n\n🏦 Nhà cái: BOT",
            color=discord.Color.blurple()
        )
        view = JoinView(self, room)
        msg = await interaction.response.send_message(embed=embed, view=view)
        room["message"] = await interaction.original_response()

        # Chờ cho tới khi đủ người
        async def wait_for_players():
            while len(room["players"]) < room["max_players"]:
                await asyncio.sleep(1)

            # Khi đủ người -> bắt đầu game
            await asyncio.sleep(5)
            await self.start_game(room, interaction)

        self.bot.loop.create_task(wait_for_players())

    async def start_game(self, room, interaction: discord.Interaction):
        # Chia 2 lá cho mỗi người
        for player in room["players"]:
            room["hands"][player] = [random.choice(self.deck), random.choice(self.deck)]
            # Gửi riêng cho từng người
            hand = room["hands"][player]
            score = self.calculate_score(hand)
            embed = discord.Embed(
                title="♠️ Bài Của Bạn",
                description=f"🃏 Bài: {' | '.join(hand)}\n✨ Điểm: {score}",
                color=discord.Color.blurple()
            )
            try:
                await player.send(embed=embed)
            except:
                pass

        # Nhà cái có 2 lá (1 ẩn, 1 mở)
        room["dealer"] = [random.choice(self.deck), random.choice(self.deck)]

        room["turn"] = -1
        await self.next_turn(room, interaction)

    async def next_turn(self, room, interaction: discord.Interaction):
        players = room["players"]
        room["turn"] += 1

        if room["turn"] < len(players):
            current_player = players[room["turn"]]
            hand = room["hands"][current_player]
            score = self.calculate_score(hand)
            hand_str = " | ".join(hand)

            embed = discord.Embed(
                title="♠️ Xì Dách - Lượt Của Bạn",
                description=f"👉 {current_player.mention}, đây là bài của bạn.\n🃏 {hand_str}\n✨ Điểm: {score}",
                color=discord.Color.blurple()
            )
            view = ActionView(self, room, current_player)
            await current_player.send(embed=embed, view=view)

        else:
            await self.finish_game(room, interaction)

    async def finish_game(self, room, interaction: discord.Interaction):
        # Nhà cái bốc bài tới khi >= 17
        while self.calculate_score(room["dealer"]) < 17:
            room["dealer"].append(random.choice(self.deck))
        dealer_score = self.calculate_score(room["dealer"])

        results = [f"🏦 **Nhà cái**: {' | '.join(room['dealer'])} = {dealer_score}"]
        winner_list = []

        for player, hand in room["hands"].items():
            score = self.calculate_score(hand)
            hand_str = " | ".join(hand)
            if score > 21:
                results.append(f"{player.mention}: {hand_str} = {score} ❌ (Cháy)")
            elif dealer_score > 21 or score > dealer_score:
                results.append(f"{player.mention}: {hand_str} = {score} ✅ Thắng Nhà Cái")
                winner_list.append(player)
            elif score == dealer_score:
                results.append(f"{player.mention}: {hand_str} = {score} ➖ Hòa")
            else:
                results.append(f"{player.mention}: {hand_str} = {score} ❌ Thua")

        embed = discord.Embed(
            title="🎉 Kết Quả Ván Xì Dách",
            description="\n".join(results),
            color=discord.Color.green()
        )

        await room["message"].edit(embed=embed, view=None)
        await asyncio.sleep(30)
        try:
            await room["message"].delete()
        except:
            pass
        del self.rooms[interaction.channel.id]


async def setup(bot: commands.Bot):
    await bot.add_cog(Xijack(bot))

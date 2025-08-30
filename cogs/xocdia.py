import discord
from discord.ext import commands
import random
import asyncio
from utils.data import get_user, save_data, DATA

class JoinView(discord.ui.View):
    def __init__(self, room, embed, cog):
        super().__init__(timeout=None)
        self.room = room
        self.embed = embed
        self.cog = cog

    @discord.ui.button(label="🎮 Tham gia", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.room["players"]:
            await interaction.response.send_message("❌ Bạn đã tham gia rồi!", ephemeral=True)
            return

        if len(self.room["players"]) >= self.room["max_players"]:
            await interaction.response.send_message("❌ Phòng đã đầy!", ephemeral=True)
            return

        self.room["players"][interaction.user.id] = {"choice": None}
        self.embed.set_field_at(1, name="👥 Người chơi",
                                value="\n".join(f"<@{uid}>" for uid in self.room["players"].keys()),
                                inline=False)
        await interaction.response.edit_message(embed=self.embed, view=self)

        # đủ người chơi thì bắt đầu
        if len(self.room["players"]) == self.room["max_players"]:
            await asyncio.sleep(3)
            await self.cog.start_game(self.room)


class ChoiceView(discord.ui.View):
    def __init__(self, room, player_id, cog):
        super().__init__(timeout=20)
        self.room = room
        self.player_id = player_id
        self.cog = cog

    @discord.ui.select(placeholder="🔴 Chọn số mặt đỏ", options=[
        discord.SelectOption(label=str(i), value=str(i)) for i in range(5)
    ])
    async def select_red(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.room["players"][self.player_id]["red"] = int(select.values[0])
        await interaction.response.defer()

    @discord.ui.select(placeholder="⚪ Chọn số mặt trắng", options=[
        discord.SelectOption(label=str(i), value=str(i)) for i in range(5)
    ])
    async def select_white(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.room["players"][self.player_id]["white"] = int(select.values[0])
        await interaction.response.defer()

    @discord.ui.button(label="✅ Xác nhận", style=discord.ButtonStyle.primary)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        red = self.room["players"][self.player_id].get("red", 0)
        white = self.room["players"][self.player_id].get("white", 0)
        if red + white != 4:
            await interaction.response.send_message("❌ Tổng số mặt phải bằng 4!", ephemeral=True)
            return

        self.room["players"][self.player_id]["choice"] = (red, white)
        await interaction.response.send_message(
            f"🎲 Bạn đã chọn: **{red} đỏ - {white} trắng**", ephemeral=True
        )

        # check nếu tất cả đã chọn
        if all(p["choice"] for p in self.room["players"].values()):
            await self.cog.reveal_result(self.room)


class XocDia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rooms = {}

    @commands.command()
    async def xocdia(self, ctx, max_players: int, bet: int):
        """Tạo phòng xóc đĩa: /xocdia <số_người (2-4)> <số_tiền_cược>"""
        if max_players < 2 or max_players > 4:
            await ctx.send("❌ Số người chơi phải từ 2 đến 4!")
            return

        embed = discord.Embed(
            title="🥢 XÓC ĐĨA 🎲",
            description=f"💰 Tiền cược: **{bet} xu**\n👥 Người chơi tối đa: **{max_players}**",
            color=discord.Color.gold()
        )
        embed.add_field(name="💼 Chủ phòng", value=f"<@{ctx.author.id}>", inline=False)
        embed.add_field(name="👥 Người chơi", value=f"<@{ctx.author.id}>", inline=False)

        room = {
            "owner": ctx.author.id,
            "max_players": max_players,
            "bet": bet,
            "players": {ctx.author.id: {"choice": None}}
        }

        self.rooms[ctx.channel.id] = room
        view = JoinView(room, embed, self)
        msg = await ctx.send(embed=embed, view=view)
        room["message"] = msg

    async def start_game(self, room):
        embed = discord.Embed(
            title="🥢 Xóc Đĩa - Đặt cược",
            description="🔮 Hãy chọn số mặt đỏ và trắng (tổng = 4)",
            color=discord.Color.blue()
        )

        await room["message"].edit(embed=embed, view=None)

        # gửi choice view cho từng người
        for pid in room["players"].keys():
            player = room["message"].channel.guild.get_member(pid)
            view = ChoiceView(room, pid, self)
            await room["message"].channel.send(
                f"👉 <@{pid}> hãy chọn dự đoán của bạn:", view=view
            )

    async def reveal_result(self, room):
        # kết quả random
        coins = [random.choice(["🔴", "⚪"]) for _ in range(4)]
        reds = coins.count("🔴")
        whites = coins.count("⚪")

        embed = discord.Embed(
            title="🥢 KẾT QUẢ XÓC ĐĨA 🎲",
            description=f"🪙 Kết quả: {' '.join(coins)}\n🔴 {reds} đỏ - ⚪ {whites} trắng",
            color=discord.Color.green()
        )

        winners = []
        bet = room["bet"]

        for pid, data in room["players"].items():
            choice = data["choice"]
            if not choice:
                continue

            num_red, num_white = choice
            # bắt buộc phải đoán đúng tuyệt đối
            if (num_red, num_white) == (reds, whites):
                multiplier = {1: 2, 2: 4, 3: 8, 4: 16}[num_red] if num_red in [1, 2, 3, 4] else 16
                reward = bet * multiplier
                user_data = get_user(DATA, pid)
                user_data["money"] += reward
                winners.append(f"<@{pid}> thắng 🎉 +{reward} xu")
            else:
                user_data = get_user(DATA, pid)
                user_data["money"] -= bet

        if winners:
            embed.add_field(name="🏆 Người thắng", value="\n".join(winners), inline=False)
        else:
            embed.add_field(name="😢 Không ai đoán đúng", value="Tiền cược đã mất!", inline=False)

        await room["message"].channel.send(embed=embed, delete_after=30)
        save_data()
        del self.rooms[room["message"].channel.id]


async def setup(bot):
    await bot.add_cog(XocDia(bot))

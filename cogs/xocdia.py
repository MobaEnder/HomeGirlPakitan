import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from utils.data import get_user, DATA, save_data


class JoinView(discord.ui.View):
    def __init__(self, cog, room_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.room_id = room_id

    @discord.ui.button(label="🎮 Tham gia", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        room = self.cog.rooms.get(self.room_id)
        if not room:
            return await interaction.response.send_message("❌ Phòng không tồn tại!", ephemeral=True)

        if interaction.user.id in room["players"]:
            return await interaction.response.send_message("⚠️ Bạn đã tham gia phòng này rồi!", ephemeral=True)

        if len(room["players"]) >= room["max_players"]:
            return await interaction.response.send_message("❌ Phòng đã đầy!", ephemeral=True)

        # Thêm người chơi
        room["players"][interaction.user.id] = {"choice": None}

        # Cập nhật embed
        embed = room["message"].embeds[0]
        if len(embed.fields) > 1:
            embed.remove_field(-1)

        embed.add_field(
            name="👥 Người chơi",
            value="\n".join(f"<@{uid}>" for uid in room["players"].keys()),
            inline=False
        )

        await room["message"].edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Bạn đã tham gia phòng **{self.room_id}**!", ephemeral=True)

        if len(room["players"]) == room["max_players"]:
            await self.cog.start_game(self.room_id)


class ChoiceView(discord.ui.View):
    def __init__(self, cog, room_id):
        super().__init__(timeout=15)
        self.cog = cog
        self.room_id = room_id

    @discord.ui.select(
        placeholder="🎲 Chọn số đỏ (0-4)",
        options=[discord.SelectOption(label=str(i), value=str(i)) for i in range(5)]
    )
    async def select_number(self, interaction: discord.Interaction, select: discord.ui.Select):
        num_red = int(select.values[0])
        num_white = 4 - num_red
        self.cog.rooms[self.room_id]["players"][interaction.user.id]["choice"] = (num_red, num_white)

        await interaction.response.send_message(
            f"🥢 Bạn đã chọn **{num_red} đỏ - {num_white} trắng**", ephemeral=True
        )


class XocDia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rooms = {}

    @app_commands.command(name="xocdia", description="🎲 Tạo phòng xóc đĩa")
    async def xocdia(self, interaction: discord.Interaction, so_nguoi: int, tien_cuoc: int):
        if so_nguoi < 2 or so_nguoi > 4:
            return await interaction.response.send_message("❌ Số người chơi phải từ 2-4.", ephemeral=True)

        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        if user_data["money"] < tien_cuoc:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để tạo phòng.", ephemeral=True)

        room_id = f"room_{interaction.id}"
        self.rooms[room_id] = {
            "host": user_id,
            "max_players": so_nguoi,
            "bet": tien_cuoc,
            "players": {user_id: {"choice": None}},
            "message": None
        }

        embed = discord.Embed(
            title="🎲 Xóc Đĩa Mini Game",
            description=f"🥢 Người tạo: <@{user_id}>\n💰 Cược: **{tien_cuoc} xu**\n👥 Số người: **{so_nguoi}**",
            color=discord.Color.gold()
        )
        embed.add_field(name="👥 Người chơi", value=f"<@{user_id}>", inline=False)

        view = JoinView(self, room_id)
        msg = await interaction.response.send_message(embed=embed, view=view)
        self.rooms[room_id]["message"] = await interaction.original_response()

    async def start_game(self, room_id):
        room = self.rooms.get(room_id)
        if not room:
            return

        msg = room["message"]

        # Nhà cái xóc đĩa (ẩn kết quả)
        coins = [random.choice(["🔴", "⚪"]) for _ in range(4)]
        room["result"] = coins

        embed = discord.Embed(
            title="🥢 Xóc Đĩa Bắt Đầu!",
            description="🎲 Nhà cái đã xóc xong 4 đồng xu!\nMời người chơi chọn.",
            color=discord.Color.green()
        )

        choice_view = ChoiceView(self, room_id)
        await msg.edit(embed=embed, view=choice_view)

        # Chờ 15s cho mọi người chọn
        await asyncio.sleep(15)

        # Đếm ngược mở bát
        for i in range(5, 0, -1):
            embed.description = f"⏳ Nhà cái sẽ mở bát sau **{i}** giây..."
            await msg.edit(embed=embed, view=None)
            await asyncio.sleep(1)

        # Mở bát
        reds = room["result"].count("🔴")
        whites = 4 - reds
        result_text = f"Kết quả: {' '.join(room['result'])} → **{reds} đỏ - {whites} trắng**"

        winners = []
        bet = room["bet"]

        for pid, data in room["players"].items():
            choice = data["choice"]
            if not choice:
                continue

            num_red, num_white = choice
            correct = 0
            if num_red <= reds:
                correct += num_red
            if num_white <= whites:
                correct += num_white

            if correct > 0:
                multiplier = {1: 2, 2: 4, 3: 8, 4: 16}.get(correct, 0)
                reward = bet * multiplier
                user_data = get_user(DATA, pid)
                user_data["money"] += reward
                winners.append((pid, reward))
            else:
                user_data = get_user(DATA, pid)
                user_data["money"] -= bet

        save_data()

        result_embed = discord.Embed(
            title="🥢 Kết Quả Xóc Đĩa",
            description=f"{result_text}",
            color=discord.Color.red()
        )
        if winners:
            result_embed.add_field(
                name="🎉 Người thắng",
                value="\n".join([f"<@{pid}> +{reward} xu" for pid, reward in winners]),
                inline=False
            )
        else:
            result_embed.add_field(name="💀 Không ai thắng!", value="😭 Toang hết!", inline=False)

        await msg.edit(embed=result_embed, view=None, delete_after=30)

        del self.rooms[room_id]


async def setup(bot):
    await bot.add_cog(XocDia(bot))

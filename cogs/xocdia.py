import discord
from discord.ext import commands
from discord import app_commands
import asyncio, random
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
            return await interaction.response.send_message("❌ Bạn đã tham gia rồi!", ephemeral=True)

        if len(room["players"]) >= room["max_players"]:
            return await interaction.response.send_message("❌ Phòng đã đủ người!", ephemeral=True)

        room["players"][interaction.user.id] = None  # chưa chọn
        await interaction.response.send_message(f"✅ {interaction.user.mention} đã tham gia!", ephemeral=True)

        embed = room["message"].embeds[0]
        embed.set_field_at(2, name="👥 Người chơi", value="\n".join(f"<@{uid}>" for uid in room["players"].keys()), inline=False)
        await room["message"].edit(embed=embed, view=self)

        # nếu đủ người
        if len(room["players"]) == room["max_players"]:
            await asyncio.sleep(5)
            await self.cog.start_game(room)


class ChoiceView(discord.ui.View):
    def __init__(self, cog, room, user_id):
        super().__init__(timeout=20)
        self.cog = cog
        self.room = room
        self.user_id = user_id

    @discord.ui.select(
        placeholder="🎲 Chọn số mặt đỏ (0–4)",
        options=[discord.SelectOption(label=f"{i} Đỏ - {4-i} Trắng", value=str(i)) for i in range(5)]
    )
    async def select_choice(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)

        choice = int(select.values[0])
        self.room["players"][self.user_id] = choice
        await interaction.response.send_message(f"✅ Bạn đã chọn **{choice} Đỏ – {4-choice} Trắng**", ephemeral=True)

        # kiểm tra tất cả đã chọn
        if all(v is not None for v in self.room["players"].values()):
            await self.cog.reveal_result(self.room)


class XocDia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rooms = {}

    @app_commands.command(name="xocdia", description="🎲 Tạo phòng xóc đĩa")
    async def xocdia(self, interaction: discord.Interaction, so_nguoi: int, tien_cuoc: int):
        if so_nguoi < 2 or so_nguoi > 4:
            return await interaction.response.send_message("❌ Chỉ được tạo phòng từ 2–4 người!", ephemeral=True)

        if tien_cuoc <= 0:
            return await interaction.response.send_message("❌ Tiền cược phải lớn hơn 0!", ephemeral=True)

        room_id = interaction.id
        embed = discord.Embed(
            title="🥢🎲 Phòng Xóc Đĩa",
            description=f"**Người tạo:** {interaction.user.mention}\n💰 Tiền cược: **{tien_cuoc} Xu**\n👥 Số người: **{so_nguoi}**",
            color=discord.Color.gold()
        )
        embed.add_field(name="📜 Trạng thái", value="Đang chờ người chơi tham gia...", inline=False)
        embed.add_field(name="👥 Người chơi", value=f"{interaction.user.mention}", inline=False)

        msg = await interaction.response.send_message(embed=embed, view=JoinView(self, room_id))
        msg = await interaction.original_response()

        self.rooms[room_id] = {
            "host": interaction.user.id,
            "max_players": so_nguoi,
            "bet": tien_cuoc,
            "players": {interaction.user.id: None},
            "message": msg,
            "result": None
        }

    async def start_game(self, room):
        # random kết quả
        result = [random.choice(["Đỏ", "Trắng"]) for _ in range(4)]
        room["result"] = result

        embed = discord.Embed(
            title="🥢🎲 Xóc Đĩa Bắt Đầu",
            description="Nhà cái đã xóc đĩa, hãy chọn dự đoán của bạn!",
            color=discord.Color.red()
        )
        embed.add_field(name="👥 Người chơi", value="\n".join(f"<@{uid}>" for uid in room["players"].keys()), inline=False)
        await room["message"].edit(embed=embed, view=None)

        # gửi lựa chọn riêng cho từng người
        for uid in room["players"]:
            user = self.bot.get_user(uid)
            if user:
                try:
                    await user.send(embed=discord.Embed(
                        title="🎲 Chọn số mặt đỏ",
                        description="Chọn số mặt **Đỏ (0–4)**, số còn lại sẽ là **Trắng**.",
                        color=discord.Color.blurple()
                    ), view=ChoiceView(self, room, uid))
                except:
                    pass  # nếu user tắt DM thì thôi

    async def reveal_result(self, room):
        # đếm ngược mở bát
        for i in range(5, 0, -1):
            await room["message"].edit(embed=discord.Embed(
                title="🥢🎲 Sắp mở bát!",
                description=f"Kết quả sẽ mở trong **{i}** giây...",
                color=discord.Color.orange()
            ))
            await asyncio.sleep(1)

        reds = room["result"].count("Đỏ")
        whites = 4 - reds
        embed = discord.Embed(
            title="🥢🎲 Kết Quả Xóc Đĩa",
            description=f"Kết quả: **{reds} Đỏ – {whites} Trắng**",
            color=discord.Color.green()
        )

        bet = room["bet"]
        winners = []
        for uid, choice in room["players"].items():
            if choice == reds:
                # số trúng = số đỏ đúng
                reward = bet * (2 ** choice)  # x2, x4, x8, x16
                user_data = get_user(DATA, uid)
                user_data["money"] = user_data.get("money", 0) + reward
                winners.append(f"<@{uid}> 🎉 +{reward} Xu")
            else:
                user_data = get_user(DATA, uid)
                user_data["money"] = user_data.get("money", 0) - bet

        save_data()
        if winners:
            embed.add_field(name="🏆 Người Thắng", value="\n".join(winners), inline=False)
        else:
            embed.add_field(name="💸 Kết quả", value="Không ai đoán đúng!", inline=False)

        await room["message"].edit(embed=embed, view=None, delete_after=30)
        del self.rooms[room["message"].id]


async def setup(bot: commands.Bot):
    await bot.add_cog(XocDia(bot))

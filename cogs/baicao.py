import discord
from discord.ext import commands
import random
import asyncio

from data_manager import DATA, get_user, save_data

class JoinView(discord.ui.View):
    def __init__(self, cog, channel_id, timeout=30):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.channel_id = channel_id

    @discord.ui.button(label="🎮 Tham gia", style=discord.ButtonStyle.success)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        room = self.cog.rooms.get(self.channel_id)
        if not room:
            return await interaction.response.send_message("❌ Phòng đã đóng!", ephemeral=True)

        uid = interaction.user.id
        if uid in room["players"]:
            return await interaction.response.send_message("❌ Bạn đã tham gia rồi!", ephemeral=True)

        if len(room["players"]) >= 4:
            return await interaction.response.send_message("❌ Phòng đã đủ 4 người!", ephemeral=True)

        user = get_user(DATA, str(uid))
        if user["money"] < room["bet"]:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để tham gia!", ephemeral=True)

        room["players"].append(uid)
        await interaction.response.send_message(f"✅ {interaction.user.mention} đã tham gia phòng!", ephemeral=False)


class Baicao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rooms = {}  # {channel_id: {"bet": int, "players": [user_id]}}

    @commands.hybrid_command(name="baicao", description="Chơi Bài Cào (1v1 Nhà Cái hoặc Tạo phòng 2-4 người)")
    async def baicao(self, ctx, mode: str = None, bet: int = None):
        if mode is None and bet is None:
            return await ctx.reply("❌ Dùng `/baicao <số tiền>` để chơi với Nhà Cái\n❌ Hoặc `/baicao phong <số tiền>` để tạo phòng!", ephemeral=True)

        # --- Chơi 1v1 với Nhà Cái ---
        if mode is None and bet is not None:
            await self.play_with_dealer(ctx, bet)
            return

        # --- Tạo phòng ---
        if mode == "phong" and bet:
            if ctx.channel.id in self.rooms:
                return await ctx.reply("❌ Kênh này đã có phòng đang chờ!", ephemeral=True)

            user = get_user(DATA, str(ctx.author.id))
            if user["money"] < bet:
                return await ctx.reply("❌ Bạn không đủ tiền để tạo phòng!", ephemeral=True)

            self.rooms[ctx.channel.id] = {"bet": bet, "players": [ctx.author.id]}

            embed = discord.Embed(
                title="🎴 Phòng Bài Cào được tạo!",
                description=f"💰 Tiền cược: **{bet:,} xu**\n👥 Người chơi: {ctx.author.mention}\n\n⏳ Nhấn nút bên dưới để tham gia (tối đa 4 người, tối thiểu 2).",
                color=discord.Color.blurple()
            )
            view = JoinView(self, ctx.channel.id, timeout=30)
            msg = await ctx.reply(embed=embed, view=view)

            # Đợi 30s
            await asyncio.sleep(30)

            # Sau 30s kiểm tra phòng
            room = self.rooms.get(ctx.channel.id)
            if room and len(room["players"]) >= 2:
                await self.start_room(ctx, room)
            else:
                await ctx.send("❌ Phòng không đủ người, bị hủy!")
                if ctx.channel.id in self.rooms:
                    del self.rooms[ctx.channel.id]
            await msg.edit(view=None)  # tắt nút sau khi xong

    # ====== Chơi với Nhà Cái ======
    async def play_with_dealer(self, ctx, bet: int):
        user = get_user(DATA, str(ctx.author.id))
        if bet <= 0:
            return await ctx.reply("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
        if user["money"] < bet:
            return await ctx.reply("❌ Bạn không đủ tiền để cược!", ephemeral=True)

        user["money"] -= bet
        save_data()

        def deal(): return [random.randint(1, 10) for _ in range(3)]
        player_cards, dealer_cards = deal(), deal()
        ps, ds = sum(player_cards) % 10, sum(dealer_cards) % 10

        if ps > ds:
            win_amount = bet * 2
            user["money"] += win_amount
            result_text = f"🎉 Bạn thắng! +{win_amount:,} xu"
        elif ps < ds:
            result_text = f"💀 Bạn thua! -{bet:,} xu"
        else:
            user["money"] += bet
            result_text = "🤝 Hoà! Nhận lại tiền cược"

        save_data()

        embed = discord.Embed(title="🎴 Kết quả Bài Cào", color=discord.Color.gold())
        embed.add_field(name=f"👤 {ctx.author.display_name}", value=f"{player_cards} → **{ps} điểm**", inline=True)
        embed.add_field(name="🏦 Nhà Cái", value=f"{dealer_cards} → **{ds} điểm**", inline=True)
        embed.add_field(name="📊 Kết quả", value=f"{result_text}\n💰 Số dư mới: **{user['money']:,} xu**", inline=False)
        msg = await ctx.reply(embed=embed)
        await asyncio.sleep(30)
        try: await msg.delete()
        except: pass

    # ====== Bắt đầu phòng nhiều người ======
    async def start_room(self, ctx, room):
        bet = room["bet"]
        dealer_cards = [random.randint(1, 10) for _ in range(3)]
        dealer_score = sum(dealer_cards) % 10

        result_embed = discord.Embed(title="🎴 Kết quả Phòng Bài Cào", color=discord.Color.green())
        result_embed.add_field(name="🏦 Nhà Cái", value=f"{dealer_cards} → **{dealer_score} điểm**", inline=False)

        for uid in room["players"]:
            user = get_user(DATA, str(uid))
            if user["money"] < bet:
                result_embed.add_field(name=f"👤 <@{uid}>", value="❌ Không đủ tiền!", inline=False)
                continue

            user["money"] -= bet
            cards = [random.randint(1, 10) for _ in range(3)]
            score = sum(cards) % 10

            if score > dealer_score:
                win_amount = bet * 2
                user["money"] += win_amount
                outcome = f"🎉 Thắng! +{win_amount:,} xu"
            elif score < dealer_score:
                outcome = f"💀 Thua! -{bet:,} xu"
            else:
                user["money"] += bet
                outcome = "🤝 Hoà! Nhận lại tiền"

            result_embed.add_field(
                name=f"👤 <@{uid}>",
                value=f"{cards} → **{score} điểm**\n{outcome}\n💰 Số dư: {user['money']:,} xu",
                inline=False
            )

        save_data()
        del self.rooms[ctx.channel.id]

        msg = await ctx.send(embed=result_embed)
        await asyncio.sleep(60)
        try: await msg.delete()
        except: pass


async def setup(bot):
    await bot.add_cog(Baicao(bot))

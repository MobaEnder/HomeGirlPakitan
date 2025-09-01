import discord
from discord import app_commands
from discord.ext import commands
import asyncio, random

from utils.data import get_user, save_data, DATA

CHOICES = {
    "✌️ Kéo": "scissors",
    "✊ Búa": "rock",
    "✋ Bao": "paper"
}

RESULTS = {
    ("rock", "scissors"): 1,
    ("scissors", "paper"): 1,
    ("paper", "rock"): 1,
    ("scissors", "rock"): 2,
    ("paper", "scissors"): 2,
    ("rock", "paper"): 2,
}

class KeoBuaBao(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="keobuabao", description="✌️✊✋ Chơi Kéo-Búa-Bao với nhà cái hoặc người chơi khác")
    @app_commands.describe(bet="Số tiền cược", opponent="Đối thủ (để trống nếu muốn chơi với nhà cái)")
    async def keobuabao(self, interaction: discord.Interaction, bet: int, opponent: discord.Member = None):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        if bet <= 0:
            return await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
        if user_data["money"] < bet:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để cược!", ephemeral=True)

        if opponent and opponent.id == user_id:
            return await interaction.response.send_message("❌ Bạn không thể chơi với chính mình!", ephemeral=True)

        if opponent:  # chơi với người
            opp_data = get_user(DATA, opponent.id)
            if opp_data["money"] < bet:
                return await interaction.response.send_message(f"❌ {opponent.mention} không đủ tiền để cược!", ephemeral=True)
        else:
            opp_data = None

        embed = discord.Embed(
            title="✌️✊✋ Kéo - Búa - Bao",
            description=(
                f"💼 Tiền cược: **{bet:,} xu**\n"
                f"👑 Người chơi: {interaction.user.mention}\n"
                f"🤖 Đối thủ: {opponent.mention if opponent else 'Nhà cái'}\n\n"
                f"Hãy chọn đi nào!"
            ),
            color=discord.Color.orange()
        )

        class ChoiceView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=15)
                self.choice = None

            async def handle_choice(self, interaction_btn: discord.Interaction, choice: str):
                if interaction_btn.user.id != user_id:
                    return await interaction_btn.response.send_message("⛔ Không phải lượt của bạn!", ephemeral=True)
                self.choice = choice
                for child in self.children:
                    child.disabled = True
                await interaction_btn.response.edit_message(content=f"✅ Bạn đã chọn **{choice}**", view=self)
                self.stop()

            @discord.ui.button(label="✌️ Kéo", style=discord.ButtonStyle.primary)
            async def scissors(self, i, b):
                await self.handle_choice(i, "scissors")

            @discord.ui.button(label="✊ Búa", style=discord.ButtonStyle.primary)
            async def rock(self, i, b):
                await self.handle_choice(i, "rock")

            @discord.ui.button(label="✋ Bao", style=discord.ButtonStyle.primary)
            async def paper(self, i, b):
                await self.handle_choice(i, "paper")

        view = ChoiceView()
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        await view.wait()

        if not view.choice:
            return await message.edit(content="⏳ Hết thời gian chọn! Trận đấu bị hủy.", embed=None, view=None)

        player_choice = view.choice
        opponent_choice = None

        if opponent:  # chơi với người
            opponent_choice = random.choice(["rock", "paper", "scissors"])  # giả lập đối thủ auto chọn
        else:  # nhà cái
            opponent_choice = random.choice(["rock", "paper", "scissors"])

        # animation 3s
        anim_icons = ["✌️", "✊", "✋"]
        for _ in range(3):
            await asyncio.sleep(1)
            await message.edit(content=f"⏳ Tung... {random.choice(anim_icons)}")

        # Kết quả
        result = None
        if player_choice == opponent_choice:
            result = 0
        else:
            result = RESULTS.get((player_choice, opponent_choice), None)

        if result == 1:  # user thắng
            user_data["money"] += bet
            if opponent:
                opp_data["money"] -= bet
            outcome_text = f"🎉 {interaction.user.mention} **thắng** và nhận **+{bet:,} xu**!"
            color = discord.Color.green()
        elif result == 2:  # đối thủ thắng
            user_data["money"] -= bet
            if opponent:
                opp_data["money"] += bet
            outcome_text = f"💀 {interaction.user.mention} **thua** và mất **-{bet:,} xu**!"
            color = discord.Color.red()
        else:  # hoà
            outcome_text = "😅 Trận đấu **hòa**! Hai bên giữ nguyên tiền."
            color = discord.Color.yellow()

        save_data()

        final_embed = discord.Embed(
            title="📊 Kết Quả Kéo - Búa - Bao",
            description=(
                f"👤 {interaction.user.mention}: **{player_choice}**\n"
                f"🤖 {opponent.mention if opponent else 'Nhà cái'}: **{opponent_choice}**\n\n"
                f"{outcome_text}\n\n"
                f"💰 Số dư mới: **{user_data['money']:,} xu**"
            ),
            color=color
        )
        final_embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30s.")

        await message.edit(content=None, embed=final_embed, view=None)
        await asyncio.sleep(30)
        try:
            await message.delete()
        except:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(KeoBuaBao(bot))

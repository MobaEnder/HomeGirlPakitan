import discord
from discord import app_commands
from discord.ext import commands
import random, asyncio

from utils.data import get_user, save_data, DATA


class LatXu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="latxu", description="🪙 Thử vận may với trò lật xu")
    @app_commands.describe(amount="Số tiền muốn cược")
    async def latxu(self, interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        user = get_user(DATA, user_id)

        # Check tiền
        if amount <= 0:
            return await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
        if user["money"] < amount:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để cược!", ephemeral=True)

        # Trừ tiền trước
        user["money"] -= amount
        save_data()

        # Embed tung xu
        embed = discord.Embed(
            title="🪙 Lật Xu May Rủi",
            description=f"{interaction.user.mention} đã cược **{amount:,} xu**.\n\n"
                        f"Đồng xu đang quay trên không... ⏳",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://i.imgur.com/uqp5Gbt.gif")  # gif xu quay
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(3)

        # Kết quả random
        result = random.choice(["xấp", "ngửa"])

        # View chọn nút
        class GuessView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.result = result
                self.amount = amount
                self.user = user
                self.author_id = user_id

            async def handle_guess(self, interaction_btn: discord.Interaction, guess: str):
                if interaction_btn.user.id != self.author_id:
                    return await interaction_btn.response.send_message("❌ Đây không phải lượt của bạn!", ephemeral=True)

                if guess == self.result:
                    # thắng → gấp đôi
                    win_amount = self.amount * 2
                    self.user["money"] += win_amount
                    save_data()
                    embed = discord.Embed(
                        title="🎉 Chiến Thắng!",
                        description=f"🪙 Kết quả: **{self.result.upper()}**\n"
                                    f"Bạn đã đoán đúng và nhận được **{win_amount:,} xu**!\n\n"
                                    f"💼 Số dư hiện tại: **{self.user['money']:,} xu**",
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(url="https://i.imgur.com/um3uW1P.png")  # icon vui
                else:
                    # thua → mất luôn
                    save_data()
                    embed = discord.Embed(
                        title="💀 Thua Rồi!",
                        description=f"🪙 Kết quả: **{self.result.upper()}**\n"
                                    f"Bạn đã đoán sai và mất **{self.amount:,} xu**!\n\n"
                                    f"💼 Số dư hiện tại: **{self.user['money']:,} xu**",
                        color=discord.Color.red()
                    )
                    embed.set_thumbnail(url="https://i.imgur.com/4H0Y3m1.png")  # icon buồn

                await interaction_btn.response.edit_message(embed=embed, view=None, delete_after=30)

            @discord.ui.button(label="Mặt Xấp", style=discord.ButtonStyle.primary, emoji="🪙")
            async def guess_heads(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.handle_guess(interaction_btn, "xấp")

            @discord.ui.button(label="Mặt Ngửa", style=discord.ButtonStyle.success, emoji="🌕")
            async def guess_tails(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.handle_guess(interaction_btn, "ngửa")

        # Embed mời đoán
        embed2 = discord.Embed(
            title="🤔 Đoán Kết Quả!",
            description=f"🪙 Đồng xu đang úp trên bàn...\n"
                        f"👉 {interaction.user.mention}, chọn **Mặt Xấp** hoặc **Mặt Ngửa**!",
            color=discord.Color.blurple()
        )
        embed2.set_thumbnail(url="https://i.imgur.com/uqp5Gbt.gif")
        await interaction.edit_original_response(embed=embed2, view=GuessView())


async def setup(bot: commands.Bot):
    await bot.add_cog(LatXu(bot))

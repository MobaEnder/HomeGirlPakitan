import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

from utils.data import get_user, DATA, save_data

class CuaBom(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="cuabom", description="Chơi Mini Game Cưa Bom 💣")
    @app_commands.describe(bet="Số tiền muốn cược")
    async def cuabom(self, interaction: discord.Interaction, bet: int):
        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)

        if bet <= 0:
            return await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
        if user_data["money"] < bet:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để cược!", ephemeral=True)

        # Trừ tiền cược
        user_data["money"] -= bet
        save_data()

        embed = discord.Embed(
            title="💣 Cưa Bom - Bắt Đầu!",
            description=f"💼 Bạn cược **{bet:,} xu**\n\nCưa bom để nhân đôi, hoặc dừng lại.\n\n🔹 Lần 1: 100% thắng\n🔹 Lần 2: 70% thắng\n🔹 Lần 3+: 50% thắng",
            color=discord.Color.orange()
        )

        class CuaBomView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.current_bet = bet
                self.round = 1
                self.stopped = False

            async def end_game(self, message):
                embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây.")
                await message.edit(embed=embed, view=None)
                await asyncio.sleep(30)
                try:
                    await message.delete()
                except:
                    pass

            @discord.ui.button(label="Cưa Bom 🔪", style=discord.ButtonStyle.danger)
            async def cuabom_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                # Xác suất thắng
                if self.round == 1:
                    win = True
                elif self.round == 2:
                    win = random.random() < 0.7
                else:
                    win = random.random() < 0.5

                if win:
                    self.current_bet *= 2
                    self.round += 1
                    embed.title = "💣 Cưa Bom - Tiếp Tục!"
                    embed.description = f"✅ Cưa thành công! Số tiền hiện tại: **{self.current_bet:,} xu**\n\nCưa tiếp hoặc nhấn 'Dừng lại' (nếu đủ vòng) để nhận tiền."
                    embed.color = discord.Color.green()
                    await interaction_button.response.edit_message(embed=embed, view=self)
                else:
                    embed.title = "💥 BÙM! Bom Nổ!"
                    embed.description = f"💀 Bạn mất **{self.current_bet:,} xu**"
                    embed.color = discord.Color.red()
                    self.stopped = True
                    await self.end_game(message)

            @discord.ui.button(label="Dừng Lại ✋", style=discord.ButtonStyle.success)
            async def stop_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                # Lần 1 → nhận lại tiền cược ban đầu
                if self.round == 1:
                    user_data["money"] += bet
                    save_data()
                    embed.title = "🪙 Bạn Đã Dừng Lại Lần 1"
                    embed.description = f"🎉 Nhận lại **{bet:,} xu** (chưa nhân đôi)."
                    embed.color = discord.Color.blue()
                    self.stopped = True
                    await self.end_game(message)
                    return

                # Lần 2 & 3 → không thể dừng
                if self.round in [2, 3]:
                    return await interaction_button.response.send_message(
                        f"⛔ Bạn phải tiếp tục cưa! Không thể dừng lần {self.round}.", ephemeral=True
                    )

                # Lần 4 trở đi → được chọn dừng
                user_data["money"] += self.current_bet
                save_data()
                embed.title = "🪙 Bạn Đã Dừng Lại!"
                embed.description = f"🎉 Nhận **{self.current_bet:,} xu** an toàn."
                embed.color = discord.Color.blue()
                self.stopped = True
                await self.end_game(message)

        view = CuaBomView()
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(CuaBom(bot))

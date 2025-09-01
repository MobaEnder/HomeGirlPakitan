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

        # Trừ tiền cược ban đầu
        user_data["money"] -= bet
        save_data()

        embed = discord.Embed(
            title="💣 Cưa Bom - Bắt Đầu!",
            description=(
                f"💼 Bạn cược **{bet:,} xu**\n\n"
                f"Cưa bom để nhân số tiền theo từng vòng, hoặc dừng lại.\n\n"
                f"🔹 Lần 1: 100% thắng (x1.25)\n"
                f"🔹 Lần 2: 70% thắng (x1.5)\n"
                f"🔹 Lần 3: 50% thắng (x1.75)\n"
                f"🔹 Lần 4+: giảm dần tỉ lệ, nhân thêm x0.25 mỗi lần"
            ),
            color=discord.Color.orange()
        )

        class CuaBomView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.base_bet = bet
                self.current_reward = bet  # số tiền hiện tại có thể nhận
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

            def get_real_chance(self):
                """Tỉ lệ thắng thật sự"""
                if self.round == 1:
                    return 1.0
                elif self.round == 2:
                    return 0.7
                elif self.round == 3:
                    return 0.4   # thật sự 40%
                else:
                    # từ lần 4 trở đi: 0.4 - 0.1*(round-3)
                    return max(0, 0.4 - 0.1 * (self.round - 3))

            def get_display_chance(self):
                """Tỉ lệ hiển thị cho người chơi (đánh lừa)"""
                if self.round == 3:
                    return 0.5  # hiển thị 50% dù thật là 40%
                return self.get_real_chance()

            def calc_multiplier(self):
                """Hệ số nhân theo vòng"""
                return 1.0 + 0.25 * self.round

            @discord.ui.button(label="Cưa Bom 🔪", style=discord.ButtonStyle.danger)
            async def cuabom_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                win_chance = self.get_real_chance()
                win = random.random() < win_chance

                if win:
                    self.current_reward = int(self.base_bet * self.calc_multiplier())
                    self.round += 1

                    next_display = int(self.base_bet * self.calc_multiplier())
                    embed.title = "💣 Cưa Bom - Tiếp Tục!"
                    embed.description = (
                        f"✅ Cưa thành công!\n"
                        f"💰 Tiền hiện tại: **{self.current_reward:,} xu**\n\n"
                        f"➡️ Lần {self.round}: {int(self.get_display_chance()*100)}% thắng "
                        f"(x{1 + 0.25*self.round:.2f})"
                    )
                    embed.color = discord.Color.green()
                    await interaction_button.response.edit_message(embed=embed, view=self)
                else:
                    embed.title = "💥 BÙM! Bom Nổ!"
                    embed.description = f"💀 Bạn mất hết số tiền cược (**{self.base_bet:,} xu**)"
                    embed.color = discord.Color.red()
                    self.stopped = True
                    await self.end_game(message)

            @discord.ui.button(label="Dừng Lại ✋", style=discord.ButtonStyle.success)
            async def stop_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                # Cho phép dừng ở mọi vòng > 1
                user_data["money"] += self.current_reward
                save_data()
                embed.title = "🪙 Bạn Đã Dừng Lại!"
                embed.description = f"🎉 Nhận **{self.current_reward:,} xu** an toàn."
                embed.color = discord.Color.blue()
                self.stopped = True
                await self.end_game(message)

        view = CuaBomView()
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(CuaBom(bot))

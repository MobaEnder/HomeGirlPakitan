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
                f"Cưa bom để nhân tiền, hoặc dừng lại.\n\n"
                f"🔹 Lần 1: 100% thắng (x2)\n"
                f"🔹 Lần 2: 70% thắng (x3)\n"
                f"🔹 Lần 3: 50% thắng (x4)\n"
                f"🔹 Lần 4: 45% thắng (x5)\n"
                f"🔹 Lần 5+: giảm 5% mỗi lần (x6, x7 ...)\n\n"
                f"⚠️ Chỉ từ lần 4 trở đi mới được dừng lại!"
            ),
            color=discord.Color.orange()
        )

        class CuaBomView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.current_money = bet   # tiền hiện tại
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

            def get_win_chance(self):
                """Tỉ lệ thắng theo vòng"""
                if self.round == 1:
                    return 1.0
                elif self.round == 2:
                    return 0.7
                elif self.round == 3:
                    return 0.45
                elif self.round == 4:
                    return 0.40
                else:
                    chance = 0.40 - 0.05 * (self.round - 4)
                    return max(0, chance)

            @discord.ui.button(label="Cưa Bom 🔪", style=discord.ButtonStyle.danger)
            async def cuabom_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                # Tỉ lệ thắng
                win_chance = self.get_win_chance()
                win = random.random() < win_chance

                if win:
                    # Nhân tiền theo vòng (lần 1 x2, lần 2 x3, ...)
                    self.current_money = bet * (self.round + 1)
                    self.round += 1

                    embed.title = "💣 Cưa Bom - Tiếp Tục!"
                    embed.description = (
                        f"✅ Cưa thành công!\n"
                        f"💰 Tiền hiện tại: **{self.current_money:,} xu**\n\n"
                        f"👉 Bạn muốn tiếp tục hay dừng lại?"
                    )
                    embed.color = discord.Color.green()
                    await interaction_button.response.edit_message(embed=embed, view=self)

                else:
                    # Thua → mất hết
                    embed.title = "💥 BÙM! Bom Nổ!"
                    embed.description = f"💀 Bạn mất sạch số tiền cược (**{bet:,} xu**)."
                    embed.color = discord.Color.red()
                    self.stopped = True
                    await self.end_game(message)

            @discord.ui.button(label="Dừng Lại ✋", style=discord.ButtonStyle.success)
            async def stop_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                if self.round < 4:
                    return await interaction_button.response.send_message(
                        "⛔ Bạn chưa thể dừng lại! Chỉ từ **lần 4** mới được dừng.", ephemeral=True
                    )

                # Cộng tiền vào user
                user_data["money"] += self.current_money
                save_data()

                embed.title = "🪙 Bạn Đã Dừng Lại!"
                embed.description = (
                    f"🎉 Nhận an toàn **{self.current_money:,} xu**!\n\n"
                    f"💼 Số dư mới: **{user_data['money']:,} xu**"
                )
                embed.color = discord.Color.blue()
                self.stopped = True
                await self.end_game(message)

        view = CuaBomView()
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(CuaBom(bot))

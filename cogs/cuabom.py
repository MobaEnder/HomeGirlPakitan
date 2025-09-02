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
                f"🔹 Lần 1: 100% thắng → x2\n"
                f"🔹 Lần 2: 80% thắng → ×0.75 tiền trước đó\n"
                f"🔹 Lần 3: 50% thắng → ×0.75 tiền trước đó\n"
                f"🔹 Lần 4+: 40% thắng → ×0.75 tiền trước đó\n\n"
                f"⚠️ Chỉ được dừng ngay **lần đầu** (cảnh báo) hoặc từ **lần 4** trở đi!"
            ),
            color=discord.Color.orange()
        )

        class CuaBomView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)
                self.current_money = bet
                self.round = 1
                self.stopped = False
                self.message = None

            def get_win_chance(self):
                if self.round == 1:
                    return 1.0
                elif self.round == 2:
                    return 0.8
                elif self.round == 3:
                    return 0.5
                else:
                    return 0.4

            def next_reward(self):
                """Tính tiền vòng tiếp theo"""
                if self.round == 1:
                    return self.current_money * 2  # lần 1 x2
                else:
                    return int(self.current_money * 0.75)

            async def end_game(self):
                embed.set_footer(text="⏳ Tin nhắn sẽ tự xóa sau 30 giây.")
                await self.message.edit(embed=embed, view=None)
                await asyncio.sleep(30)
                try:
                    await self.message.delete()
                except:
                    pass

            @discord.ui.button(label="Cưa Bom 🔪", style=discord.ButtonStyle.danger)
            async def cuabom_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                win_chance = self.get_win_chance()
                win = random.random() < win_chance

                if win:
                    self.current_money = self.next_reward()
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
                    embed.title = "💥 BÙM! Bom Nổ!"
                    embed.description = f"💀 Bạn mất sạch số tiền cược (**{bet:,} xu**)."
                    embed.color = discord.Color.red()
                    self.stopped = True
                    await self.end_game()

            @discord.ui.button(label="Dừng Lại ✋", style=discord.ButtonStyle.success)
            async def stop_button(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if self.stopped:
                    return await interaction_button.response.send_message("⚠️ Trò chơi đã kết thúc!", ephemeral=True)

                # chỉ cho phép dừng ở lần đầu (cảnh báo) hoặc từ lần 4 trở đi
                if self.round == 1:
                    warning = (
                        "⚠️ Dừng ngay lần đầu đồng nghĩa với việc **chỉ nhận lại số tiền cược**, "
                        "không có lợi nhuận!\nBạn có chắc muốn dừng?"
                    )
                    await interaction_button.response.send_message(warning, ephemeral=True)
                    # trả lại tiền cược
                    user_data["money"] += bet
                elif self.round >= 4:
                    user_data["money"] += self.current_money
                else:
                    return await interaction_button.response.send_message(
                        "⛔ Bạn chưa thể dừng lại! Chỉ được dừng **ngay lần đầu** hoặc từ **lần 4**.", ephemeral=True
                    )

                save_data()
                embed.title = "🪙 Bạn Đã Dừng Lại!"
                embed.description = (
                    f"🎉 Nhận an toàn **{self.current_money:,} xu**!\n\n"
                    f"💼 Số dư mới: **{user_data['money']:,} xu**"
                )
                embed.color = discord.Color.blue()
                self.stopped = True
                await self.end_game()

        view = CuaBomView()
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(CuaBom(bot))

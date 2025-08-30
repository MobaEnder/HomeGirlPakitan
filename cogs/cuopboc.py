import discord
from discord import app_commands
from discord.ext import commands
import random, time
from utils.data import get_user, save_data, DATA

# cooldown dictionary (user_id : timestamp)
COOLDOWN_CUOPBOC = {}


class CuopBoc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="cuopboc", description="💰 Cướp bóc người khác")

    @group.command(name="thucthi", description="💰 Thử cướp bóc người khác")
    @app_commands.describe(nguoi="Người bạn muốn cướp")
    async def thucthi(self, interaction: discord.Interaction, nguoi: discord.Member):
        user_id = interaction.user.id
        target_id = nguoi.id
        now = time.time()

        # check cooldown
        if user_id in COOLDOWN_CUOPBOC and now < COOLDOWN_CUOPBOC[user_id]:
            remaining = int(COOLDOWN_CUOPBOC[user_id] - now)
            mins, secs = divmod(remaining, 60)
            embed = discord.Embed(
                title="⏳ Đang hồi chiêu",
                description=f"Bạn phải chờ **{mins} phút {secs} giây** nữa mới có thể cướp tiếp!",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3502/3502458.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        thief = get_user(DATA, user_id)
        target = get_user(DATA, target_id)

        # check target nghèo
        if target["money"] < 100:
            embed = discord.Embed(
                title="❌ Thất bại",
                description=f"{nguoi.mention} quá nghèo, không thể cướp!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/857/857681.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # đặt cooldown 1 tiếng
        COOLDOWN_CUOPBOC[user_id] = now + 3600  

        # xác suất thành công 30%
        success = random.random() < 0.3

        if success:
            # số tiền cướp được: 3% - 6% tiền của target
            percent = random.uniform(0.03, 0.06)
            stolen = int(target["money"] * percent)
            stolen = max(100, min(stolen, target["money"]))  # ít nhất 100 xu

            target["money"] -= stolen
            thief["money"] += stolen
            save_data()

            embed = discord.Embed(
                title="💼 Cướp thành công!",
                description=(
                    f"{interaction.user.mention} đã cướp từ {nguoi.mention}!\n\n"
                    f"💰 Số tiền: **{stolen:,} xu**\n"
                    f"📊 Tỉ lệ: **{percent*100:.2f}%** tài sản của {nguoi.mention}\n\n"
                    f"🎉 Tiền đã được cộng vào ví của bạn!"
                ),
                color=discord.Color.green()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/616/616408.png")
            embed.add_field(name="📥 Số dư mới của bạn", value=f"**{thief['money']:,} xu**", inline=True)
            embed.add_field(name="📤 Số dư của nạn nhân", value=f"**{target['money']:,} xu**", inline=True)
            return await interaction.response.send_message(embed=embed)

        else:
            # thất bại → bị bắt vào đồn
            jailed_until = now + 240  # 4 phút
            thief["jailed_until"] = jailed_until
            save_data()

            embed = discord.Embed(
                title="🚨 Cướp thất bại!",
                description=(
                    f"{interaction.user.mention} bị công an bắt khi đang cố cướp {nguoi.mention}! \n\n"
                    f"⛓️ Bạn sẽ **không thể `/work` trong 4 phút**."
                ),
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/190/190411.png")
            embed.add_field(name="📥 Số dư của bạn", value=f"**{thief['money']:,} xu**", inline=True)
            embed.add_field(name="📤 Số dư của mục tiêu", value=f"**{target['money']:,} xu**", inline=True)
            return await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CuopBoc(bot))

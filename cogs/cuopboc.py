import discord
from discord import app_commands
from discord.ext import commands
import random, time, asyncio

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
            return await interaction.response.send_message(
                f"⏳ Bạn phải chờ {mins} phút {secs} giây nữa mới có thể cướp tiếp!", ephemeral=True
            )

        thief = get_user(DATA, user_id)
        target = get_user(DATA, target_id)

        # check target nghèo
        if target["money"] < 100:
            return await interaction.response.send_message("❌ Đối phương quá nghèo, không thể cướp!", ephemeral=True)

        # đặt cooldown 1 tiếng
        COOLDOWN_CUOPBOC[user_id] = now + 3600  

        # xác suất thành công 30%
        success = random.random() < 0.3

        if success:
            stolen = random.randint(100, min(800, target["money"]))
            target["money"] -= stolen
            thief["money"] += stolen
            save_data()
            return await interaction.response.send_message(
                f"💰 {interaction.user.mention} đã **cướp thành công {stolen} xu** từ {nguoi.mention}! 🎉"
            )
        else:
            # thất bại → bị bắt vào đồn
            jailed_until = now + 240  # 4 phút
            thief["jailed_until"] = jailed_until
            save_data()
            return await interaction.response.send_message(
                f"🚨 {interaction.user.mention} bị công an bắt khi đang cố cướp {nguoi.mention}! "
                f"Bạn sẽ không thể `/work` trong 4 phút."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(CuopBoc(bot))

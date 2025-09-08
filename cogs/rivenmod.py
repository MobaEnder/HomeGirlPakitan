# cogs/rivenmod.py
import discord
from discord import app_commands
from discord.ext import commands
import random

from utils.data import get_user, DATA, save_data
from utils.rivens import add_riven, get_user_rivens, load_rivens, delete_riven, save_rivens

COST_CREATE = 10000   # tạo mới
COST_REROLL = 3500    # reroll trong preview
MAX_RIVENS = 10

DISPO_RANGES = {
    5: (1.31, 1.55),
    4: (1.11, 1.30),
    3: (0.90, 1.10),
    2: (0.70, 0.89),
    1: (0.50, 0.69),
}

ICON = {
    "primary": "🔫",
    "secondary": "🎯",
    "melee": "⚔️",
    "companion": "🐾",
    "archgun": "💥",
}

AFFIX_POOL = {
    "melee": ["Additional Combo Count Chance","Chance to not gain Combo Count","Damage vs Corpus","Damage vs Grineer","Damage vs Infested",
        "Cold","Combo Duration","Critical Chance","Critical Chance on Slide Attack","Critical Damage","Melee Damage","Electricity",
        "Heat","Finisher Damage","Attack Speed","Initial Combo","Impact","Heavy Attack Efficiency","Toxin","Puncture","Range",
        "Slash","Status Chance","Status Duration"],
    "primary": ["Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Slash","Status Chance","Status Duration","Multishot","Magazine Capacity","Projectile speed",
        "Punch Through","Reload Speed","Weapon Recoil","Zoom","Magazine Capacity","Projectile speed"],
    "secondary": ["Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Slash","Status Chance","Status Duration","Multishot",
        "Punch Through","Reload Speed","Weapon Recoil","Zoom","Magazine Capacity","Projectile speed"],
    "companion": ["Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Slash","Status Chance","Status Duration","Multishot","Reload Speed","Magazine Capacity"],
    "archgun": ["Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Status Chance","Status Duration","Multishot",
        "Reload Speed","Weapon Recoil","Zoom","Magazine Capacity"]
}

# ===== Helpers =====
def pick_disposition_value(dot: int) -> float:
    lo, hi = DISPO_RANGES.get(dot, (0.9, 1.1))
    return round(random.uniform(lo, hi), 2)

def generate_id(existing_ids=None) -> int:
    if existing_ids is None:
        existing_ids = set()
    else:
        existing_ids = set(x for x in existing_ids if isinstance(x, int))
    while True:
        rid = random.randint(1000, 9999)
        if rid not in existing_ids:
            return rid

def _roll_affixes(slot: str, dot: int) -> list[dict]:
    pool = AFFIX_POOL.get(slot)
    if not pool:
        raise ValueError(f"Không có affix cho slot '{slot}'")
    k = random.randint(2, 4)
    chosen = random.sample(pool, k=k)
    dispo_val = pick_disposition_value(dot)
    affixes = []
    for i, stat in enumerate(chosen):
        value = round(random.uniform(5, 50) * dispo_val, 2)
        negative = (k == 4 and i == 3)
        affixes.append({
            "label": stat,
            "value": value,
            "percent": True,
            "negative": negative
        })
    return affixes

def generate_riven(slot, weapon_name, dot, user_id, mr=None, cap=None, rerolls=0, rid=None):
    inv = get_user_rivens(user_id) or []
    existing_ids = {r.get("id") for r in inv if isinstance(r, dict) and isinstance(r.get("id"), int)}
    rid = rid if rid is not None else generate_id(existing_ids)
    affixes = _roll_affixes(slot, dot)
    return {
        "id": rid,
        "weapon": weapon_name,
        "slot": slot,
        "disposition": dot,
        "mr": mr if mr is not None else random.randint(8, 16),
        "capacity": cap if cap is not None else random.randint(8, 18),
        "affixes": affixes,
        "rerolls": rerolls
    }

def nice_val(a: dict) -> str:
    sign = "-" if a.get("negative") else "+"
    v = f"{a['value']:.2f}".rstrip("0").rstrip(".")
    return f"**{sign}{v}% {a['label']}**"

def build_embed(riven: dict, user_money: int) -> discord.Embed:
    icon = ICON.get(riven["slot"], "💎")
    stats_text = "\n".join(nice_val(a) for a in riven["affixes"])
    desc = (
        f"**ID:** `{riven['id']}`\n"
        f"**Vũ khí:** {riven['weapon']}    **Loại:** {riven['slot'].capitalize()}\n"
        f"**Disposition:** {riven['disposition']}\n"
        f"**MR:** {riven['mr']}    **Cap:** {riven['capacity']}\n"
        f"**Rerolls:** {riven['rerolls']}\n\n"
        f"── **Stats** ──\n{stats_text}"
    )
    emb = discord.Embed(title=f"{icon} Riven Mod (Preview)", description=desc, color=discord.Color.purple())
    emb.set_footer(text=f"💰 Số dư: {user_money:,} xu")
    return emb

# ===== View cho preview =====
class RivenPreviewView(discord.ui.View):
    def __init__(self, bot, user_id, riven, user_data, message=None):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.riven = riven
        self.user_data = user_data
        self.message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Đây không phải Riven của bạn!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🔒 Lưu vào kho", style=discord.ButtonStyle.success)
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inv = get_user_rivens(self.user_id)
        if len(inv) >= MAX_RIVENS:
            return await interaction.response.send_message("📦 Kho đã đầy (10)!", ephemeral=True)
        add_riven(self.user_id, self.riven)
        await interaction.response.send_message(f"✅ Đã lưu Riven ID `{self.riven['id']}` vào kho!", ephemeral=True)
        if self.message:
            await self.message.delete()
        self.stop()

    @discord.ui.button(label="🎲 Reroll (3500 xu)", style=discord.ButtonStyle.primary)
    async def reroll_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_data.get("money", 0) < COST_REROLL:
            return await interaction.response.send_message("💸 Bạn không đủ xu để reroll!", ephemeral=True)
        self.user_data["money"] -= COST_REROLL
        save_data()
        self.riven["affixes"] = _roll_affixes(self.riven["slot"], self.riven["disposition"])
        self.riven["rerolls"] += 1
        emb = build_embed(self.riven, self.user_data["money"])
        await interaction.response.edit_message(embed=emb, view=self)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except:
                pass
        self.stop()

# ===== View cho reroll với Giữ / Reroll =====
class RivenRerollView(discord.ui.View):
    def __init__(self, bot, user_id, riven, user_data, message=None):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.riven = riven
        self.user_data = user_data
        self.message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Đây không phải Riven của bạn!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="💾 Giữ Riven", style=discord.ButtonStyle.success)
    async def keep_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"✅ Đã giữ Riven ID `{self.riven['id']}`.", ephemeral=True)
        if self.message:
            try:
                await self.message.delete()
            except: pass
        self.stop()

    @discord.ui.button(label="🎲 Reroll (3500 xu)", style=discord.ButtonStyle.primary)
    async def reroll_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_data.get("money", 0) < COST_REROLL:
            return await interaction.response.send_message("💸 Bạn không đủ xu để reroll!", ephemeral=True)
        self.user_data["money"] -= COST_REROLL
        save_data()
        self.riven["affixes"] = _roll_affixes(self.riven["slot"], self.riven["disposition"])
        self.riven["rerolls"] = self.riven.get("rerolls", 0) + 1
        save_rivens()
        emb = build_embed(self.riven, self.user_data["money"])
        await interaction.response.edit_message(embed=emb, view=self)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except:
                pass
        self.stop()

# ===== Cog =====
class RivenModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_rivens()

    @app_commands.command(name="rivenmod", description="Tạo Riven Mod (10000 xu, preview)")
    @app_commands.describe(weapon="Tên vũ khí")
    @app_commands.choices(
        slot=[
            app_commands.Choice(name="Primary", value="primary"),
            app_commands.Choice(name="Secondary", value="secondary"),
            app_commands.Choice(name="Melee", value="melee"),
            app_commands.Choice(name="Companion", value="companion"),
            app_commands.Choice(name="Archgun", value="archgun"),
        ],
        dot=[
            app_commands.Choice(name="1", value=1),
            app_commands.Choice(name="2", value=2),
            app_commands.Choice(name="3", value=3),
            app_commands.Choice(name="4", value=4),
            app_commands.Choice(name="5", value=5),
        ]
    )
    async def rivenmod(self, interaction: discord.Interaction, weapon: str, slot: app_commands.Choice[str], dot: app_commands.Choice[int]):
        user_data = get_user(DATA, interaction.user.id)
        if user_data.get("money", 0) < COST_CREATE:
            return await interaction.response.send_message(f"💸 Cần {COST_CREATE:,} xu để tạo riven.", ephemeral=True)

        user_data["money"] -= COST_CREATE
        save_data()

        riven = generate_riven(slot.value, weapon, dot.value, interaction.user.id)
        emb = build_embed(riven, user_data["money"])
        view = RivenPreviewView(self.bot, interaction.user.id, riven, user_data)

        await interaction.response.send_message(embed=emb, view=view)
        msg = await interaction.original_response()
        view.message = msg

    @app_commands.command(name="reroll", description="Reroll Riven theo ID (3500 xu)")
    async def reroll_cmd(self, interaction: discord.Interaction, rid: int):
        user_data = get_user(DATA, interaction.user.id)
        inv = get_user_rivens(interaction.user.id) or []
        riven = next((rv for rv in inv if rv.get("id") == rid), None)
        if not riven:
            return await interaction.response.send_message(
                f"⚠️ Không tìm thấy Riven ID `{rid}` trong kho.", ephemeral=True
            )

        emb = build_embed(riven, user_data.get("money", 0))
        view = RivenRerollView(self.bot, interaction.user.id, riven, user_data)
        await interaction.response.send_message(
            f"🔄 Preview Riven ID `{rid}` trước khi reroll:", embed=emb, view=view, ephemeral=True
        )
        msg = await interaction.original_response()
        view.message = msg

    @app_commands.command(name="inventory", description="Xem kho Riven")
    async def inventory(self, interaction: discord.Interaction):
        inv = get_user_rivens(interaction.user.id) or []
        if not inv:
            return await interaction.response.send_message("📭 Kho Riven trống!", ephemeral=True)

        emb = discord.Embed(title=f"📦 Kho Riven ({len(inv)}/{MAX_RIVENS})", color=discord.Color.gold())
        for rv in inv:
            icon = ICON.get(rv.get("slot"), "💎")
            stats = " • ".join(nice_val(a) for a in rv.get("affixes", []))
            emb.add_field(
                name=f"{icon} ID {rv.get('id')} — {rv.get('weapon')}",
                value=f"{stats}\n🔄 Rerolls: {rv.get('rerolls', 0)}",
                inline=False
            )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="xoariven", description="Xoá Riven theo ID")
    async def xoariven(self, interaction: discord.Interaction, rid: int):
        if delete_riven(interaction.user.id, rid):
            await interaction.response.send_message(f"🗑️ Đã xoá Riven ID `{rid}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Không tìm thấy Riven ID `{rid}`.", ephemeral=True)

    @app_commands.command(name="showriven", description="Hiển thị thông tin chi tiết của Riven theo ID")
    async def showriven(self, interaction: discord.Interaction, rid: int):
        inv = get_user_rivens(interaction.user.id) or []
        riven = next((rv for rv in inv if rv.get("id") == rid), None)
        if not riven:
            return await interaction.response.send_message(
                f"⚠️ Không tìm thấy Riven ID `{rid}` trong kho của bạn.", ephemeral=True
            )
        user_data = get_user(DATA, interaction.user.id)
        emb = build_embed(riven, user_data.get("money", 0))
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="traderiven", description="Chuyển Riven cho người khác")
    @app_commands.describe(user="Người nhận Riven")
    async def traderiven(self, interaction: discord.Interaction, rid: int, user: discord.User):
        if interaction.user.id == user.id:
            return await interaction.response.send_message("⚠️ Bạn không thể chuyển Riven cho chính mình.", ephemeral=True)

        inv = get_user_rivens(interaction.user.id) or []
        riven = next((rv for rv in inv if rv.get("id") == rid), None)
        if not riven:
            return await interaction.response.send_message(
                f"⚠️ Không tìm thấy Riven ID `{rid}` trong kho của bạn.", ephemeral=True
            )

        recipient_inv = get_user_rivens(user.id) or []
        if len(recipient_inv) >= MAX_RIVENS:
            return await interaction.response.send_message(
                f"⚠️ Kho của {user.mention} đã đầy!", ephemeral=True
            )

        delete_riven(interaction.user.id, rid)
        add_riven(user.id, riven)
        save_rivens()
        await interaction.response.send_message(
            f"✅ Đã chuyển Riven ID `{rid}` cho {user.mention}.", ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(RivenModCog(bot))

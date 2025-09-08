# cogs/rivenmod.py
import discord
from discord import app_commands
from discord.ext import commands
import random

from utils.data import get_user, DATA, save_data
from utils.rivens import add_riven, get_user_rivens, load_rivens, delete_riven, save_rivens

COST_ROLL = 3000
MAX_RIVENS = 10

# disposition ranges (dot 1-5 -> hệ số random trong khoảng)
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

# affix pool theo slot
AFFIX_POOL = {
    "melee": [
        "Additional Combo Count Chance","Chance to not gain Combo Count","Damage vs Corpus","Damage vs Grineer","Damage vs Infested",
        "Cold","Combo Duration","Critical Chance","Critical Chance on Slide Attack","Critical Damage","Melee Damage","Electricity",
        "Heat","Finisher Damage","Attack Speed","Initial Combo","Impact","Heavy Attack Efficiency","Toxin","Puncture","Range",
        "Slash","Status Chance","Status Duration"
    ],
    "primary": [
        "Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Slash","Status Chance","Status Duration","Multishot",
        "Punch Through","Reload Speed","Weapon Recoil","Zoom"
    ],
    "secondary": [
        "Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Slash","Status Chance","Status Duration","Multishot",
        "Punch Through","Reload Speed","Weapon Recoil","Zoom"
    ],
    "companion": [
        "Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Slash","Status Chance","Status Duration","Multishot","Reload Speed"
    ],
    "archgun": [
        "Ammo Maximum","Damage vs Corpus","Damage vs Grineer","Damage vs Infested","Cold","Critical Chance","Critical Damage","Damage",
        "Electricity","Heat","Fire Rate","Impact","Toxin","Puncture","Slash","Status Chance","Status Duration","Multishot",
        "Punch Through","Reload Speed","Weapon Recoil","Zoom"
    ]
}

# ----- Helpers -----
def pick_disposition_value(dot: int) -> float:
    lo, hi = DISPO_RANGES.get(dot, (0.9, 1.1))
    return round(random.uniform(lo, hi), 2)

def generate_id(existing_ids: list[int]) -> int:
    while True:
        rid = random.randint(1000, 9999)
        if rid not in existing_ids:
            return rid

def _roll_affixes(slot: str, dot: int) -> list[dict]:
    """
    Random 2-4 affix. Nếu có 4 affix thì affix thứ 4 bắt buộc là dòng âm.
    Giá trị được scale theo dot thông qua pick_disposition_value(dot).
    """
    pool = AFFIX_POOL.get(slot, [])
    if not pool:
        raise ValueError(f"Không có affix cho slot '{slot}'")

    k = random.randint(2, 4)
    if k > len(pool):
        k = len(pool)
    chosen = random.sample(pool, k=k)

    dispo_val = pick_disposition_value(dot)
    affixes = []
    for i, stat in enumerate(chosen):
        value = round(random.uniform(5, 50) * dispo_val, 2)
        negative = (k == 4 and i == 3)  # dòng thứ 4 là malus
        affixes.append({
            "label": stat,
            "value": value,
            "percent": True,
            "negative": negative
        })
    return affixes

def generate_riven(slot, weapon_name, name, dot, user_id, mr=None, cap=None, rerolls=0, rid=None):
    inv = get_user_rivens(user_id)
    rid = rid or generate_id([r["id"] for r in inv])
    affixes = _roll_affixes(slot, dot)
    return {
        "id": rid,
        "weapon": weapon_name,
        "name": name or "(không tên)",
        "slot": slot,
        "disposition": dot,  # lưu dot 1-5
        "mr": mr if mr is not None else random.randint(8, 16),
        "capacity": cap if cap is not None else random.randint(8, 18),
        "affixes": affixes,
        "rerolls": rerolls
    }

def nice_val(a: dict) -> str:
    sign = "-" if a.get("negative") else "+"
    v = f"{a['value']:.2f}".rstrip("0").rstrip(".")
    return f"{sign}{v}% {a['label']}"

def build_embed(riven: dict, user_money: int) -> discord.Embed:
    icon = ICON.get(riven["slot"], "💎")
    stats_text = "\n".join(nice_val(a) for a in riven["affixes"])
    desc = (
        f"**ID:** {riven['id']}\n"
        f"**Tên:** `{riven['name']}`\n"
        f"**Vũ khí:** {riven['weapon']}    **Loại:** {riven['slot'].capitalize()}\n"
        f"**Disposition:** {riven['disposition']}\n"
        f"**MR:** {riven['mr']}    **Cap:** {riven['capacity']}\n"
        f"**Rerolls:** {riven['rerolls']}\n\n"
        f"── Stats ──\n{stats_text}"
    )
    emb = discord.Embed(title=f"{icon} Riven Mod", description=desc, color=discord.Color.purple())
    emb.set_footer(text=f"💰 Số dư hiện tại: {user_money:,} xu")
    return emb

# ----- Cog -----
class RivenModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_rivens()

    @app_commands.command(name="rivenmod", description="Tạo Riven Mod (3000 xu)")
    @app_commands.describe(weapon="Tên vũ khí", name="Tên Riven")
    @app_commands.choices(
        slot=[
            app_commands.Choice(name="Primary", value="primary"),
            app_commands.Choice(name="Secondary", value="secondary"),
            app_commands.Choice(name="Melee", value="melee"),
            app_commands.Choice(name="Companion", value="companion"),
            app_commands.Choice(name="Archgun", value="archgun"),
        ],
        dot=[
            app_commands.Choice(name="1 (Yếu nhất)", value=1),
            app_commands.Choice(name="2", value=2),
            app_commands.Choice(name="3", value=3),
            app_commands.Choice(name="4", value=4),
            app_commands.Choice(name="5 (Mạnh nhất)", value=5),
        ]
    )
    async def rivenmod(self, interaction: discord.Interaction, weapon: str, name: str, slot: app_commands.Choice[str], dot: app_commands.Choice[int]):
        user_data = get_user(DATA, interaction.user.id)
        if user_data.get("money", 0) < COST_ROLL:
            return await interaction.response.send_message(f"💸 Cần {COST_ROLL:,} xu.", ephemeral=True)

        inv = get_user_rivens(interaction.user.id)
        if len(inv) >= MAX_RIVENS:
            return await interaction.response.send_message("📦 Kho đã đầy (10). Hãy xoá bớt bằng `/xoariven <id>`.", ephemeral=True)

        # trừ tiền & lưu
        user_data["money"] -= COST_ROLL
        save_data()

        # tạo riven
        riven = generate_riven(slot.value, weapon, name, dot.value, interaction.user.id)
        add_riven(interaction.user.id, riven)  # save_rivens() đã được gọi bên trong add nếu bạn cài vậy, an toàn thêm save_rivens() cũng được

        emb = build_embed(riven, user_data["money"])
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="inventory", description="Xem kho Riven của bạn (tối đa 10)")
    async def inventory(self, interaction: discord.Interaction):
        inv = get_user_rivens(interaction.user.id)
        if not inv:
            return await interaction.response.send_message("📭 Kho Riven trống!", ephemeral=True)

        emb = discord.Embed(title=f"📦 Kho Riven của {interaction.user.display_name} ({len(inv)}/{MAX_RIVENS})", color=discord.Color.gold())
        for rv in inv:
            icon = ICON.get(rv["slot"], "💎")
            stats = " • ".join(nice_val(a) for a in rv["affixes"])
            emb.add_field(
                name=f"{icon} ID {rv['id']} — {rv['name']} ({rv['weapon']})",
                value=f"{stats}\n🔄 Rerolls: {rv['rerolls']}",
                inline=False
            )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="xoariven", description="Xoá 1 Riven theo ID")
    async def xoariven(self, interaction: discord.Interaction, rid: int):
        if delete_riven(interaction.user.id, rid):
            await interaction.response.send_message(f"🗑️ Đã xoá Riven ID `{rid}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Không tìm thấy Riven ID `{rid}`.", ephemeral=True)

    @app_commands.command(name="reroll", description="Reroll lại Riven theo ID (3000 xu) — giữ nguyên MR, Cap, Dispo")
    async def reroll(self, interaction: discord.Interaction, rid: int):
        user_data = get_user(DATA, interaction.user.id)
        if user_data.get("money", 0) < COST_ROLL:
            return await interaction.response.send_message("💸 Bạn không đủ xu để reroll.", ephemeral=True)

        inv = get_user_rivens(interaction.user.id)
        target = next((rv for rv in inv if rv.get("id") == rid), None)
        if not target:
            return await interaction.response.send_message(f"❌ Không tìm thấy Riven với ID `{rid}`.", ephemeral=True)

        # trừ tiền
        user_data["money"] -= COST_ROLL
        save_data()

        # reroll: GIỮ MR, Cap, Slot, Dot, ID — random lại affixes, tăng rerolls
        target["affixes"] = _roll_affixes(target["slot"], target["disposition"])
        target["rerolls"] = target.get("rerolls", 0) + 1
        save_rivens()

        emb = build_embed(target, user_data["money"])
        await interaction.response.send_message(embed=emb)

async def setup(bot: commands.Bot):
    await bot.add_cog(RivenModCog(bot))

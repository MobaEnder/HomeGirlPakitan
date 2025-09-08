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

# affix pool theo slot (theo bạn cung cấp)
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

def generate_id(existing_ids=None) -> int:
    """
    Tạo ID 4 chữ số không trùng. existing_ids có thể là set/list/None.
    """
    if existing_ids is None:
        existing_ids = set()
    else:
        # đảm bảo là set các int hợp lệ
        existing_ids = set(x for x in existing_ids if isinstance(x, int))
    while True:
        rid = random.randint(1000, 9999)
        if rid not in existing_ids:
            return rid

def _roll_affixes(slot: str, dot: int) -> list[dict]:
    """
    Random 2-4 affix. Nếu có 4 affix thì affix thứ 4 bắt buộc là malus.
    """
    pool = AFFIX_POOL.get(slot)
    if not pool:
        raise ValueError(f"Không có affix cho slot '{slot}'. Hãy thêm vào AFFIX_POOL.")
    k = random.randint(2, 4)
    if k > len(pool):
        k = len(pool)
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

def generate_riven(slot, weapon_name, name, dot, user_id, mr=None, cap=None, rerolls=0, rid=None):
    """
    Tạo riven mới, an toàn với dữ liệu inventory có format khác.
    """
    inv = get_user_rivens(user_id) or []
    # Lấy tập ID hợp lệ từ inventory (bảo vệ nếu có item lỗi)
    existing_ids = { r.get("id") for r in inv if isinstance(r, dict) and isinstance(r.get("id"), int) }
    rid = rid if rid is not None else generate_id(existing_ids)
    affixes = _roll_affixes(slot, dot)
    return {
        "id": rid,
        "weapon": weapon_name,
        "name": name or "(không tên)",
        "slot": slot,
        "disposition": dot,
        "mr": mr if mr is not None else random.randint(8, 16),
        "capacity": cap if cap is not None else random.randint(8, 18),
        "affixes": affixes,
        "rerolls": rerolls
    }

def nice_val(a: dict) -> str:
    try:
        sign = "-" if a.get("negative") else "+"
        v = f"{a['value']:.2f}".rstrip("0").rstrip(".")
        return f"{sign}{v}% {a['label']}"
    except Exception:
        # phòng hờ dữ liệu affix không đầy đủ
        label = a.get("label", "<unknown>")
        return f"{label}"

def build_embed(riven: dict, user_money: int) -> discord.Embed:
    icon = ICON.get(riven.get("slot"), "💎")
    stats_text = "\n".join(nice_val(a) for a in riven.get("affixes", []))
    desc = (
        f"**ID:** {riven.get('id')}\n"
        f"**Tên:** `{riven.get('name')}`\n"
        f"**Vũ khí:** {riven.get('weapon')}    **Loại:** {riven.get('slot', '').capitalize()}\n"
        f"**Disposition:** {riven.get('disposition')}\n"
        f"**MR:** {riven.get('mr')}    **Cap:** {riven.get('capacity')}\n"
        f"**Rerolls:** {riven.get('rerolls', 0)}\n\n"
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

        inv = get_user_rivens(interaction.user.id) or []
        if len(inv) >= MAX_RIVENS:
            return await interaction.response.send_message("📦 Kho đã đầy (10). Hãy xoá bớt bằng `/xoariven <id>`.", ephemeral=True)

        # trừ tiền & lưu
        user_data["money"] -= COST_ROLL
        save_data()

        # tạo riven
        try:
            riven = generate_riven(slot.value, weapon, name, dot.value, interaction.user.id)
        except Exception as e:
            # lỗi do pool/affix thiếu
            return await interaction.response.send_message(f"❌ Lỗi khi tạo riven: {e}", ephemeral=True)

        add_riven(interaction.user.id, riven)

        emb = build_embed(riven, user_data["money"])
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="inventory", description="Xem kho Riven của bạn (tối đa 10)")
    async def inventory(self, interaction: discord.Interaction):
        inv = get_user_rivens(interaction.user.id) or []
        if not inv:
            return await interaction.response.send_message("📭 Kho Riven trống!", ephemeral=True)

        emb = discord.Embed(title=f"📦 Kho Riven của {interaction.user.display_name} ({len(inv)}/{MAX_RIVENS})", color=discord.Color.gold())
        for rv in inv:
            icon = ICON.get(rv.get("slot"), "💎")
            stats = " • ".join(nice_val(a) for a in rv.get("affixes", []))
            emb.add_field(
                name=f"{icon} ID {rv.get('id')} — {rv.get('name')} ({rv.get('weapon')})",
                value=f"{stats}\n🔄 Rerolls: {rv.get('rerolls', 0)}",
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

        inv = get_user_rivens(interaction.user.id) or []
        target = next((rv for rv in inv if isinstance(rv, dict) and rv.get("id") == rid), None)
        if not target:
            return await interaction.response.send_message(f"❌ Không tìm thấy Riven với ID `{rid}`.", ephemeral=True)

        # trừ tiền
        user_data["money"] -= COST_ROLL
        save_data()

        # reroll: giữ MR, Cap, Slot, Dot, ID — random lại affixes, tăng rerolls
        try:
            target["affixes"] = _roll_affixes(target.get("slot"), target.get("disposition"))
        except Exception as e:
            return await interaction.response.send_message(f"❌ Lỗi khi roll: {e}", ephemeral=True)

        target["rerolls"] = target.get("rerolls", 0) + 1
        save_rivens()

        emb = build_embed(target, user_data["money"])
        await interaction.response.send_message(embed=emb)

async def setup(bot: commands.Bot):
    await bot.add_cog(RivenModCog(bot))

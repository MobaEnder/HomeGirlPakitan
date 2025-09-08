# cogs/rivenmod.py
import discord
from discord import app_commands
from discord.ext import commands
import random
from utils.data import get_user, DATA, save_data
from utils.rivens import add_riven, get_user_rivens, load_rivens

COST_ROLL = 3000
MAX_RIVENS = 10

DISPO_RANGES = {
    5: (1.31, 1.55),
    4: (1.11, 1.30),
    3: (0.90, 1.10),
    2: (0.70, 0.89),
    1: (0.50, 0.69),
}

ICON = {
    "primary": "🔫", "secondary": "🎯", "melee": "⚔️",
    "companion": "🐾", "archgun": "🚀",
}

AFFIX_POOL = {
    "melee": [
        "Additional Combo Count Chance", "Chance to not gain Combo Count",
        "Damage vs Corpus", "Damage vs Grineer", "Damage vs Infested",
        "Cold", "Combo Duration", "Critical Chance", "Critical Chance on Slide Attack",
        "Critical Damage", "Melee Damage", "Electricity", "Heat", "Finisher Damage",
        "Attack Speed", "Initial Combo", "Impact", "Heavy Attack Efficiency",
        "Toxin", "Puncture", "Range", "Slash", "Status Chance", "Status Duration"
    ],
    "primary": [
        "Ammo Maximum", "Damage vs Corpus", "Damage vs Grineer", "Damage vs Infested",
        "Cold", "Critical Chance", "Critical Damage", "Damage", "Electricity", "Heat",
        "Fire Rate", "Impact", "Toxin", "Puncture", "Slash", "Status Chance",
        "Status Duration", "Multishot", "Punch Through", "Reload Speed",
        "Weapon Recoil", "Zoom"
    ],
    "secondary": [
        "Ammo Maximum", "Damage vs Corpus", "Damage vs Grineer", "Damage vs Infested",
        "Cold", "Critical Chance", "Critical Damage", "Damage", "Electricity", "Heat",
        "Fire Rate", "Impact", "Toxin", "Puncture", "Slash", "Status Chance",
        "Status Duration", "Multishot", "Punch Through", "Reload Speed",
        "Weapon Recoil", "Zoom"
    ],
    "companion": [
        "Ammo Maximum", "Damage vs Corpus", "Damage vs Grineer", "Damage vs Infested",
        "Cold", "Critical Chance", "Critical Damage", "Damage", "Electricity", "Heat",
        "Fire Rate", "Impact", "Toxin", "Puncture", "Slash", "Status Chance",
        "Status Duration", "Multishot", "Reload Speed"
    ],
    "archgun": [
        "Ammo Maximum", "Damage vs Corpus", "Damage vs Grineer", "Damage vs Infested",
        "Cold", "Critical Chance", "Critical Damage", "Damage", "Electricity", "Heat",
        "Fire Rate", "Impact", "Toxin", "Puncture", "Slash", "Status Chance",
        "Status Duration", "Multishot", "Punch Through", "Reload Speed",
        "Weapon Recoil", "Zoom"
    ],
}

def pick_disposition_value(dot:int) -> float:
    lo, hi = DISPO_RANGES.get(dot, (0.9,1.1))
    return random.uniform(lo, hi)

def generate_id(existing_ids):
    while True:
        rid = random.randint(1000, 9999)
        if rid not in existing_ids:
            return rid

def generate_riven(slot: str, disposition: int, name: str, mr=None, cap=None, rerolls=0, rid=None):
    dispo_val = pick_disposition_value(disposition)
    pool = AFFIX_POOL.get(slot, [])
    k = random.randint(2, 4)
    chosen = random.sample(pool, k=k)
    affixes = []
    for i, stat in enumerate(chosen):
        value = random.uniform(5, 50) * dispo_val
        negative = (k == 4 and i == 3)
        affixes.append({
            "label": stat, "value": round(value, 2),
            "percent": True, "negative": negative
        })
    existing_ids = [r["id"] for r in get_user_rivens]
    return {
        "id": rid or generate_id(existing_ids),
        "name": name or "(không tên)",
        "slot": slot,
        "disposition": disposition,
        "dispo_val": round(dispo_val, 3),
        "mr": mr if mr is not None else random.randint(8, 16),
        "capacity": cap if cap is not None else random.randint(8, 18),
        "affixes": affixes,
        "rerolls": rerolls
    }

def nice_val(v: float, percent: bool, negative: bool) -> str:
    s = f"{v:.1f}" if abs(v - round(v)) > 0.01 else str(int(round(v)))
    prefix = "-" if negative else "+"
    return f"{prefix}{s}{'%' if percent else ''}"

def build_embed(riven: dict, user_money: int) -> discord.Embed:
    icon = ICON.get(riven["slot"], "💎")
    stats_lines = []
    for a in riven["affixes"]:
        stats_lines.append(f"{nice_val(a['value'], a['percent'], a['negative'])} {a['label']}")
    stats_text = "\n".join(stats_lines)
    desc = (
        f"**ID:** {riven['id']}\n"
        f"**Tên:** `{riven['name']}`\n"
        f"**Loại:** {riven['slot'].capitalize()}    **Disposition:** {riven['disposition']} (×{riven['dispo_val']})\n"
        f"**MR:** {riven['mr']}    **Cap:** {riven['capacity']}\n"
        f"**Rerolls:** {riven['rerolls']}\n\n"
        f"── Stats ──\n{stats_text}"
    )
    emb = discord.Embed(title=f"{icon} Riven Mod", description=desc, color=discord.Color.purple())
    emb.set_footer(text=f"💰 Số dư hiện tại: {user_money:,} xu")
    return emb

class RivenModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_rivens()

    @app_commands.command(name="rivenmod", description="Tạo Riven Mod (3000 xu / lần)")
    async def rivenmod(self, interaction: discord.Interaction, name: str, slot: str, disposition: int):
        if disposition < 1 or disposition > 5:
            return await interaction.response.send_message("⚠️ Disposition phải là số 1 → 5.", ephemeral=True)
        user_data = get_user(DATA, interaction.user.id)
        if user_data.get("money", 0) < COST_ROLL:
            return await interaction.response.send_message(f"💸 Bạn cần {COST_ROLL:,} xu.", ephemeral=True)
        if len(get_user_rivens(interaction.user.id)) >= MAX_RIVENS:
            return await interaction.response.send_message("📦 Kho đã đầy (10). Hãy dùng `/xoariven <id>` để xoá.", ephemeral=True)
        user_data["money"] -= COST_ROLL; save_data()
        riven = generate_riven(slot, disposition, name)
        add_riven(interaction.user.id, riven); save_data()
        embed = build_embed(riven, user_data["money"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="inventory", description="Xem kho Riven (tối đa 10)")
    async def inventory(self, interaction: discord.Interaction):
        inv = get_user_rivens(interaction.user.id)
        if not inv:
            return await interaction.response.send_message("📭 Kho Riven trống!", ephemeral=True)
        emb = discord.Embed(title=f"📦 Kho Riven của {interaction.user.display_name}", color=discord.Color.gold())
        for rv in inv:
            icon = ICON.get(rv["slot"], "💎")
            stats = "\n".join(f"{nice_val(a['value'], a['percent'], a['negative'])} {a['label']}" for a in rv["affixes"])
            emb.add_field(
                name=f"[{rv['id']}] {icon} {rv['name']} | Rerolls: {rv['rerolls']}",
                value=stats, inline=False
            )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="xoariven", description="Xóa Riven bằng ID")
    async def xoariven(self, interaction: discord.Interaction, rid: int):
        inv = get_user_rivens(interaction.user.id)
        target = next((rv for rv in inv if rv["id"] == rid), None)
        if not target:
            return await interaction.response.send_message("❌ Không tìm thấy Riven ID này.", ephemeral=True)
        inv.remove(target); save_data()
        await interaction.response.send_message(f"🗑️ Đã xóa Riven ID {rid}.", ephemeral=True)

    @app_commands.command(name="reroll", description="Reroll Riven trong kho theo ID")
    async def reroll_cmd(self, interaction: discord.Interaction, rid: int):
        user_data = get_user(DATA, interaction.user.id)
        if user_data.get("money", 0) < COST_ROLL:
            return await interaction.response.send_message("💸 Không đủ xu để reroll.", ephemeral=True)
        inv = get_user_rivens(interaction.user.id)
        target = next((rv for rv in inv if rv["id"] == rid), None)
        if not target:
            return await interaction.response.send_message("❌ Không tìm thấy Riven ID này.", ephemeral=True)
        user_data["money"] -= COST_ROLL; save_data()
        inv.remove(target)
        new_riven = generate_riven(
            target["slot"], target["disposition"], target["name"],
            mr=target["mr"], cap=target["capacity"],
            rerolls=target["rerolls"]+1, rid=target["id"]
        )
        inv.append(new_riven); save_data()
        emb = build_embed(new_riven, user_data["money"])
        await interaction.response.send_message(embed=emb, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RivenModCog(bot))

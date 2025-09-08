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
    "primary": "🔫",
    "secondary": "🎯",
    "melee": "⚔️",
    "companion": "🐾",
    "archgun": "🚀",
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
    ]
}

def pick_disposition_value(dot:int) -> float:
    lo, hi = DISPO_RANGES.get(dot, (0.9,1.1))
    return round(random.uniform(lo, hi), 3)

def generate_id(existing_ids):
    while True:
        rid = random.randint(1000, 9999)
        if rid not in existing_ids:
            return rid

def generate_riven(slot, weapon_name, name, dot, mr=None, cap=None, rerolls=0, rid=None):
    dispo_val = pick_disposition_value(dot)
    pool = AFFIX_POOL.get(slot, [])
    if not pool:
        raise ValueError(f"Không có affix cho slot '{slot}'")

    k = random.randint(2, 4)
    if k > len(pool):
        k = len(pool)
    chosen = random.sample(pool, k=k)

    affixes = []
    for i, stat in enumerate(chosen):
        value = round(random.uniform(5, 50) * dispo_val, 2)
        negative = (k == 4 and i == 3)
        affixes.append({"label": stat, "value": value, "percent": True, "negative": negative})

    inv = get_user_rivens
    rid = rid or generate_id([r["id"] for r in inv])
    return {
        "id": rid,
        "weapon": weapon_name,
        "name": name or "(không tên)",
        "slot": slot,
        "disposition": dispo_val,
        "mr": mr if mr is not None else random.randint(8,16),
        "capacity": cap if cap is not None else random.randint(8,18),
        "affixes": affixes,
        "rerolls": rerolls
    }

def nice_val(v, percent, negative):
    prefix = "-" if negative else "+"
    s = f"{v:.1f}" if abs(v - round(v)) > 0.01 else str(int(round(v)))
    return f"{prefix}{s}{'%' if percent else ''}"

def build_embed(riven, user_money):
    icon = ICON.get(riven["slot"], "💎")
    stats = "\n".join(nice_val(a["value"], a["percent"], a["negative"]) + " " + a["label"] for a in riven["affixes"])
    desc = (
        f"**ID:** {riven['id']}\n"
        f"**Weapon:** {riven['weapon']}\n"
        f"**Tên:** `{riven['name']}`\n"
        f"**Loại / Dispo:** {riven['slot'].capitalize()} / ×{riven['disposition']}\n"
        f"**MR:** {riven['mr']}    **Cap:** {riven['capacity']}\n"
        f"**Rerolls:** {riven['rerolls']}\n\n── Stats ──\n{stats}"
    )
    emb = discord.Embed(title=f"{icon} Riven Mod", description=desc, color=discord.Color.purple())
    emb.set_footer(text=f"💰 Số dư: {user_money:,} xu")
    return emb

class RivenModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_rivens()

    @app_commands.command(name="rivenmod", description="Tạo Riven Mod (3000 xu)")
    @app_commands.describe(
        weapon="Tên vũ khí",
        name="Tên Riven",
        slot="Loại vũ khí",
        dot="Disposition (1–5)"
    )
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

        if len(get_user_rivens(interaction.user.id)) >= MAX_RIVENS:
            return await interaction.response.send_message("📦 Kho đã đầy (10). Xoá riven bằng `/xoariven <id>`.", ephemeral=True)

        user_data["money"] -= COST_ROLL
        save_data()

        riven = generate_riven(slot.value, weapon, name, dot.value)
        add_riven(interaction.user.id, riven)
        save_data()

        emb = build_embed(riven, user_data["money"])
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="inventory", description="Xem kho Riven (max 10)")
    async def inventory(self, interaction: discord.Interaction):
        inv = get_user_rivens(interaction.user.id)
        if not inv:
            return await interaction.response.send_message("📭 Kho trống!", ephemeral=True)
        emb = discord.Embed(title=f"📦 Kho Riven của {interaction.user.display_name}", color=discord.Color.gold())
        for rv in inv:
            icon = ICON.get(rv["slot"], "💎")
            stats = "\n".join(nice_val(a["value"], a["percent"], a["negative"]) + " " + a["label"] for a in rv["affixes"])
            emb.add_field(name=f"[{rv['id']}] {icon} {rv['weapon']} – {rv['name']} | Rerolls: {rv['rerolls']}", value=stats, inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="xoariven", description="Xoá Riven theo ID")
    async def xoariven(self, interaction: discord.Interaction, rid: int):
        inv = get_user_rivens(interaction.user.id)
        for rv in inv:
            if rv["id"] == rid:
                inv.remove(rv)
                save_data()
                return await interaction.response.send_message(f"🗑 Riven [{rid}] đã được xoá.", ephemeral=True)
        await interaction.response.send_message("❌ Không tìm thấy Riven ID đó.", ephemeral=True)

    @app_commands.command(name="reroll", description="Reroll trong kho theo ID (3000 xu)")
    async def reroll(self, interaction: discord.Interaction, rid: int):
        user_data = get_user(DATA, interaction.user.id)
        if user_data.get("money", 0) < COST_ROLL:
            return await interaction.response.send_message("💸 Không đủ xu.", ephemeral=True)

        inv = get_user_rivens(interaction.user.id)
        target = next((rv for rv in inv if rv["id"] == rid), None)
        if not target:
            return await interaction.response.send_message("❌ ID không hợp lệ.", ephemeral=True)

        user_data["money"] -= COST_ROLL
        save_data()

        inv.remove(target)
        new = generate_riven(
            target["slot"], target["weapon"], target["name"],
            dot=1,  # dùng lại dispo random range theo dot=1 nếu không có gốc
            mr=target["mr"], cap=target["capacity"],
            rerolls=target["rerolls"]+1, rid=rid
        )
        inv.append(new)
        save_data()

        emb = build_embed(new, user_data["money"])
        await interaction.response.send_message(embed=emb, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RivenModCog(bot))

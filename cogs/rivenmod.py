# cogs/rivenmod.py
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import time

from utils.data import get_user, DATA, save_data
from utils.rivens import add_riven, get_user_rivens

COST_ROLL = 3000

# disposition ranges (wiki: 5 mức)
DISPO_RANGES = {
    5: (1.31, 1.55),
    4: (1.11, 1.30),
    3: (0.90, 1.10),
    2: (0.70, 0.89),
    1: (0.50, 0.69),
}

# bonus/malus multipliers from wiki
BM_MULT = {
    (2, 0): 0.99,
    (2, 1): 1.2375,
    (3, 0): 0.75,
    (3, 1): 0.9375,
}

# A compact but wide attribute base table (numbers taken/approximated from wiki base-value table).
# Keys are internal names; each entry: { "label": str, "percent": bool, "primary": base, "secondary": base, "melee": base }
BASE_VALUES = {
    "crit_chance": {"label":"Critical Chance", "percent":True, "primary":149.99, "secondary":149.99, "melee":180.0},
    "crit_damage": {"label":"Critical Damage", "percent":True, "primary":120.0, "secondary":120.0, "melee":90.0},
    "multishot": {"label":"Multishot", "percent":True, "primary":90.0, "secondary":119.7, "melee":0.0},
    "status_chance": {"label":"Status Chance", "percent":True, "primary":90.0, "secondary":90.0, "melee":60.3},
    "fire_rate": {"label":"Fire Rate / Attack Speed", "percent":True, "primary":60.03, "secondary":89.1, "melee":54.9},
    "base_damage": {"label":"Base Damage", "percent":True, "primary":165.0, "secondary":164.7, "melee":164.7},
    "puncture": {"label":"Puncture", "percent":True, "primary":119.97, "secondary":119.97, "melee":119.7},
    "impact": {"label":"Impact", "percent":True, "primary":119.97, "secondary":119.97, "melee":119.7},
    "slash": {"label":"Slash", "percent":True, "primary":119.97, "secondary":119.97, "melee":119.7},
    "magazine": {"label":"Magazine", "percent":True, "primary":50.0, "secondary":50.0, "melee":0.0},
    "reload": {"label":"Reload Speed", "percent":True, "primary":50.0, "secondary":49.45, "melee":0.0},
    "range": {"label":"Range", "percent":False, "primary":0.0, "secondary":0.0, "melee":1.94},
    "punch_through": {"label":"Punch Through (m)", "percent":False, "primary":2.7, "secondary":2.7, "melee":0.0},
    "ammo": {"label":"Ammo Max", "percent":True, "primary":49.95, "secondary":90.0, "melee":0.0},
    # add more if you like (wiki contains ~31 attrs)
}

SLOTS = {"primary":"primary", "secondary":"secondary", "melee":"melee"}

def pick_disposition_value(dot:int) -> float:
    lo, hi = DISPO_RANGES.get(dot, (0.9, 1.0))
    return random.uniform(lo, hi)

def generate_riven(slot: str, disposition_dot: int):
    # choose number of bonuses (2 or 3)
    num_bonus = random.choices([2,3], weights=[60,40])[0]
    # chance to have a negative (malus): we'll use 30% approx
    has_malus = random.random() < 0.30

    # available attributes for this slot
    pool = [k for k,v in BASE_VALUES.items() if v.get(slot,0)]
    if len(pool) < num_bonus + (1 if has_malus else 0):
        pool = list(BASE_VALUES.keys())

    chosen = random.sample(pool, num_bonus)
    malus = None
    if has_malus:
        remaining = [p for p in pool if p not in chosen]
        if remaining:
            malus = random.choice(remaining)

    dispo_val = pick_disposition_value(disposition_dot)
    bm = BM_MULT.get((num_bonus, 1 if malus else 0), 1.0)

    affixes = []
    for stat in chosen:
        base = BASE_VALUES[stat][slot]
        # random roll 0.9..1.1
        r = random.uniform(0.9, 1.1)
        raw = base * r * dispo_val * bm
        affixes.append({
            "key": stat,
            "label": BASE_VALUES[stat]["label"],
            "value": raw,
            "percent": BASE_VALUES[stat]["percent"],
            "base": base
        })

    if malus:
        base = BASE_VALUES[malus][slot]
        r = random.uniform(0.9, 1.1)
        # malus value is negative - use same bm adjustment (wiki uses negative scaling)
        raw = -abs(base * r * dispo_val * bm)
        affixes.append({
            "key": malus,
            "label": BASE_VALUES[malus]["label"],
            "value": raw,
            "percent": BASE_VALUES[malus]["percent"],
            "base": base
        })

    # sort affixes (bonus first)
    affixes = sorted(affixes, key=lambda x: (x["value"]<0, -abs(x["value"])))
    return {
        "slot": slot,
        "disposition_dot": disposition_dot,
        "disposition_value": round(dispo_val, 4),
        "num_bonus": num_bonus,
        "has_malus": bool(malus),
        "affixes": affixes
    }

class RivenView(discord.ui.View):
    def __init__(self, cog, user_id, riven_obj, bet_cost):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id
        self.riven = riven_obj
        self.bet_cost = bet_cost  # cost per roll (3000)
        self.message = None

    async def save_and_confirm(self, interaction: discord.Interaction):
        # save to rivens
        add_riven(self.user_id, self.riven)
        inv = get_user_rivens(self.user_id)
        await interaction.response.edit_message(content=None, embed=build_embed(self.riven, saved=True, inv_count=len(inv)), view=None)

    @discord.ui.button(label="Giữ (Lưu)", style=discord.ButtonStyle.success)
    async def hold(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Chỉ chủ request mới thao tác được.", ephemeral=True)
        await self.save_and_confirm(interaction)

    @discord.ui.button(label="Roll lại (-3000 xu)", style=discord.ButtonStyle.secondary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Chỉ chủ request mới thao tác được.", ephemeral=True)

        user_data = get_user(DATA, self.user_id)
        if user_data["money"] < self.bet_cost:
            return await interaction.response.send_message("❌ Bạn không đủ tiền để roll lại.", ephemeral=True)

        # trừ tiền và tạo riven mới
        user_data["money"] -= self.bet_cost
        save_data()
        new_riven = generate_riven(self.riven["slot"], self.riven["disposition_dot"])
        self.riven = new_riven
        # update message with new embed (still same view)
        await interaction.response.edit_message(embed=build_embed(self.riven, saved=False, inv_count=len(get_user_rivens(self.user_id))), view=self)
        # update stored message ref
        # no deletion here; message will be auto-deleted by the original caller after 30s

def pretty_val(v: float, percent: bool):
    if percent:
        return f"{v:.2f}%"
    else:
        # for meters/absolute numbers, show 2 decimals if not integer
        if abs(v - int(v)) < 0.001:
            return f"{int(v)}"
        return f"{v:.2f}"

def build_embed(riven_obj, saved=False, inv_count=0):
    title = f"🧾 Riven Mod — {riven_obj.get('slot').capitalize()}"
    embed = discord.Embed(title=title, color=discord.Color.blurple())
    embed.add_field(name="Tên", value=f"**{riven_obj.get('name','(không tên)')}**", inline=False)
    embed.add_field(name="Loại", value=riven_obj.get("slot").capitalize(), inline=True)
    embed.add_field(name="Disposition", value=f"{riven_obj.get('disposition_dot')} dots (×{riven_obj.get('disposition_value')})", inline=True)
    embed.add_field(name="Số bonus", value=str(riven_obj.get("num_bonus")), inline=True)
    if riven_obj.get("has_malus"):
        embed.add_field(name="Có Malus", value="Có", inline=True)
    embed.add_field(name="—— Affixes ——", value="\u200b", inline=False)
    for a in riven_obj.get("affixes", []):
        sign = "" if a["value"]>=0 else "−"
        embed.add_field(
            name=a["label"],
            value=f"{sign}{pretty_val(abs(a['value']), a['percent'])}",
            inline=True
        )
    if saved:
        embed.set_footer(text=f"✅ Đã lưu vào inventory ({inv_count} rivens). Tin nhắn sẽ tự xóa sau 30s.")
    else:
        embed.set_footer(text=f"🪙 Roll tốn {COST_ROLL:,} xu. Tin nhắn sẽ tự xóa sau 30s.")
    return embed

class RivenModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rivenmod", description="Tạo Riven Mod (3000 xu / lần roll)")
    @app_commands.describe(name="Tên Riven", slot="Primary / Secondary / Melee", disposition="Disposition (1..5)")
    @app_commands.choices(slot=[
        app_commands.Choice(name="Primary", value="primary"),
        app_commands.Choice(name="Secondary", value="secondary"),
        app_commands.Choice(name="Melee", value="melee"),
    ])
    async def rivenmod(self, interaction: discord.Interaction, name: str, slot: app_commands.Choice[str], disposition: int):
        if disposition < 1 or disposition > 5:
            return await interaction.response.send_message("⚠️ Disposition phải từ 1 đến 5.", ephemeral=True)

        user_id = interaction.user.id
        user_data = get_user(DATA, user_id)
        if user_data["money"] < COST_ROLL:
            return await interaction.response.send_message("💸 Bạn không đủ tiền để roll Riven (3000 xu).", ephemeral=True)

        # trừ tiền ban đầu
        user_data["money"] -= COST_ROLL
        save_data()

        # generate riven
        riven = generate_riven(slot.value, disposition)
        riven["name"] = name
        # build embed + view
        embed = build_embed(riven, saved=False, inv_count=len(get_user_rivens(user_id)))
        view = RivenView(self, user_id, riven, COST_ROLL)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()

        # auto-delete after 30s (embed + view)
        await asyncio.sleep(30)
        try:
            await msg.delete()
        except Exception:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(RivenModCog(bot))

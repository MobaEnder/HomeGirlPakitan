# cogs/rivenmod.py
import discord
from discord import app_commands
from discord.ext import commands
import random, os

from utils.data import get_user, DATA, save_data
from utils.rivens import add_riven, get_user_rivens, load_rivens

COST_ROLL = 3000

# disposition ranges
DISPO_RANGES = {
    5: (1.31, 1.55),
    4: (1.11, 1.30),
    3: (0.90, 1.10),
    2: (0.70, 0.89),
    1: (0.50, 0.69),
}

# icons per slot
ICON = {
    "primary": "🔫",
    "secondary": "🎯",
    "melee": "⚔️"
}

# base values (small/representative set). You can expand this map from wiki.
BASE_VALUES = {
    "crit_chance":      {"label":"Critical Chance",        "percent":True, "primary":149.99, "secondary":149.99, "melee":180.0},
    "crit_damage":      {"label":"Critical Damage",        "percent":True, "primary":120.0,  "secondary":120.0,  "melee":90.0},
    "multishot":        {"label":"Multishot",              "percent":True, "primary":90.0,   "secondary":119.7, "melee":0.0},
    "status_chance":    {"label":"Status Chance",          "percent":True, "primary":90.0,   "secondary":90.0,  "melee":60.3},
    "status_duration":  {"label":"Status Duration",        "percent":True, "primary":40.0,   "secondary":40.0,  "melee":40.0},
    "fire_rate":        {"label":"Fire Rate / Attack Speed","percent":True,"primary":60.03,  "secondary":89.1,  "melee":54.9},
    "base_damage":      {"label":"Base Damage",            "percent":True, "primary":165.0,  "secondary":164.7, "melee":164.7},
    "puncture":         {"label":"Puncture",                "percent":True, "primary":119.97, "secondary":119.97,"melee":119.7},
    "impact":           {"label":"Impact",                  "percent":True, "primary":119.97, "secondary":119.97,"melee":119.7},
    "slash":            {"label":"Slash",                   "percent":True, "primary":119.97, "secondary":119.97,"melee":119.7},
    "magazine":         {"label":"Magazine Size",           "percent":True, "primary":50.0,   "secondary":50.0,  "melee":0.0},
    "reload_speed":     {"label":"Reload Speed",           "percent":True, "primary":50.0,   "secondary":49.45, "melee":0.0},
    "max_ammo":         {"label":"Ammo Max",                "percent":True, "primary":49.95,  "secondary":90.0,  "melee":0.0},
    "shot_type":        {"label":"Shot Type (Pellet Count)", "percent":False, "primary":0.0, "secondary":0.0,  "melee":0.0},
    "status_delay":     {"label":"Status Delay",            "percent":False,"primary":0.0,    "secondary":0.0,   "melee":0.0},
    "crit_mult":        {"label":"Critical Multiplier",     "percent":True, "primary":0.0,    "secondary":0.0,   "melee":0.0},
    "angle":            {"label":"Spread Angle",            "percent":False,"primary":0.0,    "secondary":0.0,   "melee":0.0},
    "zoom":             {"label":"Zoom",                    "percent":True, "primary":-50.0,  "secondary":-50.0, "melee":0.0},
    "jump_range":       {"label":"Jump Attack Range",       "percent":False,"primary":0.0,    "secondary":0.0,   "melee":0.0},
    "lethal_force":     {"label":"Lethal Force",            "percent":True, "primary":0.0,    "secondary":0.0,   "melee":0.0},
    "stagger":          {"label":"Stagger",                 "percent":True, "primary":0.0,    "secondary":0.0,   "melee":0.0},
    "wall_damage":      {"label":"Wall Damage",             "percent":True, "primary":0.0,    "secondary":0.0,   "melee":0.0},
    "melee_range":      {"label":"Melee Range",             "percent":False,"primary":0.0,    "secondary":0.0,   "melee":1.94},
    "block_efficiency": {"label":"Block Efficiency",        "percent":True, "primary":0.0,    "secondary":0.0,   "melee":600.0},
    "kill_distance":    {"label":"Kill Distance",           "percent":False,"primary":0.0,    "secondary":0.0,   "melee":0.0},
    "slide_attack":     {"label":"Slide Attack Damage",     "percent":True, "primary":0.0,    "secondary":0.0,   "melee":0.0},
    "jump_attack":      {"label":"Jump Attack Damage",      "percent":True, "primary":0.0,    "secondary":0.0,   "melee":0.0},
    # Các thuộc tính này có base-value không có sẵn trên wiki; giữ 0.0 để tránh chọn ngẫu nhiên
}

SLOTS = ["primary", "secondary", "melee"]

def pick_disposition_value(dot:int) -> float:
    lo, hi = DISPO_RANGES.get(dot, (0.9,1.1))
    return random.uniform(lo, hi)

def generate_riven(slot: str, disposition: int, name: str):
    """
    Generate a riven with exactly 2 bonus stats (no malus per request).
    Keep name as provided.
    """
    dispo_val = pick_disposition_value(disposition)
    # build pool of stats that are applicable to the slot (base > 0)
    pool = [k for k,v in BASE_VALUES.items() if v.get(slot, 0)]
    # if pool smaller than 2 fallback to all keys
    if len(pool) < 2:
        pool = list(BASE_VALUES.keys())
    chosen = random.sample(pool, k=2)
    affixes = []
    for stat in chosen:
        base = BASE_VALUES[stat][slot]
        r = random.uniform(0.9, 1.1)
        raw = base * r * dispo_val
        affixes.append({
            "label": BASE_VALUES[stat]["label"],
            "value": raw,
            "percent": BASE_VALUES[stat]["percent"]
        })
    # MR and capacity approximations
    return {
        "name": name or "(không tên)",
        "slot": slot,
        "disposition": disposition,
        "dispo_val": round(dispo_val, 3),
        "mr": random.randint(8, 16),
        "capacity": random.randint(8, 18),
        "affixes": affixes
    }

def nice_val(v: float, percent: bool) -> str:
    # format: if percent show with %; if integer show int
    if percent:
        s = f"{v:.2f}" if abs(v - round(v)) > 0.001 else f"{int(round(v))}"
        return f"+{s}%"
    else:
        s = f"{v:.2f}" if abs(v - round(v)) > 0.001 else f"{int(round(v))}"
        return f"{s}"

def build_embed(riven: dict, user_money: int) -> discord.Embed:
    """Build a compact, single-block stats embed with cute icons and balance footer"""
    icon = ICON.get(riven["slot"], "💎")
    title = f"{icon} Riven Mod — {riven['slot'].capitalize()}"
    # stats block: name + line per stat, but we will keep them compact (one block)
    stats_lines = []
    for a in riven["affixes"]:
        stats_lines.append(f"{nice_val(a['value'], a['percent'])} {a['label']}")
    stats_text = "\n".join(stats_lines)
    desc = (
        f"**Tên:** `{riven['name']}`\n"
        f"**Loại:** {riven['slot'].capitalize()}    **Disposition:** {riven['disposition']} (×{riven['dispo_val']})\n"
        f"**MR:** {riven['mr']}    **Cap:** {riven['capacity']}\n\n"
        f"── Stats ──\n{stats_text}"
    )
    emb = discord.Embed(title=title, description=desc, color=discord.Color.purple())
    emb.set_footer(text=f"💰 Số dư hiện tại: {user_money:,} xu")
    return emb

# ----- View -----
class RivenView(discord.ui.View):
    def __init__(self, cog, user_id: int, riven: dict):
        super().__init__(timeout=None)  # no auto-timeout needed
        self.cog = cog
        self.user_id = user_id
        self.riven = riven
        self.message: discord.Message | None = None

    @discord.ui.button(label="💾 Giữ (Lưu)", style=discord.ButtonStyle.success)
    async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Chỉ chủ request mới thao tác được.", ephemeral=True)
        # save riven
        add_riven(self.user_id, self.riven)
        inv_count = len(get_user_rivens(self.user_id))
        # reply ephemeral & delete the bot message
        await interaction.response.send_message(f"✅ Đã lưu Riven! Bạn hiện có **{inv_count}** Riven.", ephemeral=True)
        # delete the original embed message to tidy channel
        if self.message:
            try:
                await self.message.delete()
            except Exception:
                pass

    @discord.ui.button(label=f"🎲 Roll lại (-{COST_ROLL:,} xu)", style=discord.ButtonStyle.primary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Chỉ chủ request mới thao tác được.", ephemeral=True)
        user_data = get_user(DATA, self.user_id)
        if user_data.get("money", 0) < COST_ROLL:
            return await interaction.response.send_message("💸 Bạn không đủ xu để roll lại.", ephemeral=True)
        # deduct cost and generate new riven (keep name)
        user_data["money"] -= COST_ROLL
        save_data()
        self.riven = generate_riven(self.riven["slot"], self.riven["disposition"], self.riven["name"])
        emb = build_embed(self.riven, user_data["money"])
        # edit original message
        if self.message:
            try:
                await self.message.edit(embed=emb, view=self)
            except Exception:
                # fallback: send new message
                await interaction.followup.send(embed=emb, view=self)
        await interaction.response.send_message(f"🎲 Roll lại xong — Số dư hiện tại: **{user_data['money']:,} xu**", ephemeral=True)

# ----- Cog -----
class RivenModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # ensure rivens loaded
        load_rivens()

    @app_commands.command(name="rivenmod", description="Tạo Riven Mod (3000 xu / lần)")
    @app_commands.choices(slot=[
        app_commands.Choice(name="Primary", value="primary"),
        app_commands.Choice(name="Secondary", value="secondary"),
        app_commands.Choice(name="Melee", value="melee"),
    ])
    @app_commands.describe(name="Tên Riven (chuỗi)", slot="Loại (Primary/Secondary/Melee)", disposition="Disposition 1-5")
    async def rivenmod(self, interaction: discord.Interaction, name: str, slot: app_commands.Choice[str], disposition: int):
        # validate
        if disposition < 1 or disposition > 5:
            return await interaction.response.send_message("⚠️ Disposition phải là số nguyên 1 → 5.", ephemeral=True)
        user_data = get_user(DATA, interaction.user.id)
        if user_data.get("money", 0) < COST_ROLL:
            return await interaction.response.send_message(f"💸 Bạn cần ít nhất {COST_ROLL:,} xu để roll Riven.", ephemeral=True)

        # deduct cost; generate riven; show embed (do NOT auto-delete)
        user_data["money"] -= COST_ROLL
        save_data()

        riven = generate_riven(slot.value, disposition, name)
        embed = build_embed(riven, user_data["money"])
        view = RivenView(self, interaction.user.id, riven)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        view.message = msg  # keep reference so view can edit/delete

    @app_commands.command(name="inventory", description="Xem kho Riven của bạn")
    async def inventory(self, interaction: discord.Interaction):
        inv = get_user_rivens(interaction.user.id)
        if not inv:
            return await interaction.response.send_message("📭 Kho Riven trống!", ephemeral=True)
        emb = discord.Embed(title=f"📦 Kho Riven của {interaction.user.display_name}", color=discord.Color.gold())
        for idx, rv in enumerate(inv, start=1):
            icon = ICON.get(rv["slot"], "💎")
            stats = " • ".join(f"{nice_val(a['value'], a['percent'])} {a['label']}" for a in rv["affixes"])
            emb.add_field(name=f"{idx}. {icon} {rv['name']}", value=stats, inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RivenModCog(bot))

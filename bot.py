import discord
from discord.ext import commands, tasks
import asyncio
import random
import datetime
import pytz
import requests
import json
import os

# ==============================
# الإعدادات العامة
# ==============================
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or "ضع_توكن_البوت_هنا"
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"
OWNER_ID = 949947235574095892
POLICE_ROLE_ID = 1342832610878951444
GANG_PING_ROLE_ID = 1342832658908057681
DAILY_CHANNEL_ID = 1432630812137754715

# ==============================
# إعداد البوت
# ==============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# ألوان وشعارات العصابات
# ==============================
gang_styles = {
    "بلود": {"emoji": "💉", "color": 0x8B0000},
    "مافيا": {"emoji": "🕶️", "color": 0x000000},
    "طوفان": {"emoji": "🌊", "color": 0x1E90FF},
    "سكراب": {"emoji": "🪵", "color": 0x8B4513},
}

# ==============================
# دوال Firebase
# ==============================
def get_gangs():
    url = f"{FIREBASE_URL}/gangs/list.json"
    r = requests.get(url)
    if r.status_code == 200 and r.text != "null":
        return r.json()
    return {}

def update_gang(gang_name, data):
    url = f"{FIREBASE_URL}/gangs/list/{gang_name}.json"
    requests.patch(url, json=data)

def log_action(gang, points, reason):
    url = f"{FIREBASE_URL}/gangs/logs.json"
    entry = {
        "gang": gang,
        "points": points,
        "reason": reason,
        "time": str(datetime.datetime.now(pytz.timezone('Asia/Riyadh')))
    }
    requests.post(url, json=entry)

# ==============================
# عرض النقاط
# ==============================
@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs()
    if not gangs:
        await ctx.send("❌ لا توجد بيانات عصابات حالياً.")
        return

    sorted_gangs = sorted(gangs.items(), key=lambda x: x[1].get("points", 0), reverse=True)
    desc = ""
    for name, data in sorted_gangs:
        style = gang_styles.get(name, {"emoji": "🏴", "color": 0x808080})
        desc += f"{style['emoji']} **{name}** — {data.get('points', 0)} نقطة\n"

    embed = discord.Embed(title="📊 ترتيب العصابات الحالي", description=desc, color=0xFFD700)
    await ctx.send(embed=embed)

# ==============================
# أمر الإضافة
# ==============================
@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return

    gangs = get_gangs()
    if gang_name not in gangs:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current_points = gangs[gang_name].get("points", 0)
    update_gang(gang_name, {"points": current_points + amount})
    log_action(gang_name, +amount, reason)

    style = gang_styles.get(gang_name, {"emoji": "🏴", "color": 0xFFFFFF})
    embed = discord.Embed(
        title=f"{style['emoji']} تمت إضافة النقاط",
        description=f"✅ تمت إضافة **{amount}** نقطة لعصابة **{gang_name}**.\n📜 السبب: {reason}",
        color=style["color"]
    )
    await ctx.send(embed=embed)

# ==============================
# أمر الخصم
# ==============================
@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return

    gangs = get_gangs()
    if gang_name not in gangs:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current_points = gangs[gang_name].get("points", 0)
    update_gang(gang_name, {"points": current_points - amount})
    log_action(gang_name, -amount, reason)

    style = gang_styles.get(gang_name, {"emoji": "🏴", "color": 0xFFFFFF})
    embed = discord.Embed(
        title=f"{style['emoji']} تم خصم النقاط",
        description=f"❌ تم خصم **{amount}** نقطة من عصابة **{gang_name}**.\n📜 السبب: {reason}",
        color=style["color"]
    )
    await ctx.send(embed=embed)

# ==============================
# نظام المهمة اليومية
# ==============================
mission_active = False
current_target = None

async def start_daily_mission(test_mode=False):
    global mission_active, current_target

    for guild in bot.guilds:
        police_role = guild.get_role(POLICE_ROLE_ID)
        channel = guild.get_channel(DAILY_CHANNEL_ID)
        if not police_role or not channel:
            continue

        members = [m for m in guild.members if police_role in m.roles]
        if not members:
            continue

        current_target = random.choice(members)
        mission_active = True

        embed = discord.Embed(
            title="🚨 مهمة القبض اليومية!",
            description=(
                f"المطلوب: {current_target.mention}\n\n"
                f"العصابة التي ستقبض عليه خلال ساعة ستحصل على 🏆 **30 نقطة**!\n"
                f"<@&{GANG_PING_ROLE_ID}>"
            ),
            color=0xFF0000
        )
        if test_mode:
            embed.title = "🧪 تجربة المهمة اليومية"
        await channel.send(embed=embed)

        await asyncio.sleep(3600)
        if mission_active:
            await channel.send("⏰ **فشلت المهمة اليومية!** لم يتم القبض على المطلوب في الوقت المحدد.")
            mission_active = False

# ==============================
# أمر تجربة
# ==============================
@bot.command(name="تجربة")
async def test_mission(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return
    await start_daily_mission(test_mode=True)
    await ctx.send("✅ تمت تجربة المهمة اليومية بنجاح.")

# ==============================
# أمر القبض
# ==============================
@bot.command(name="قبض")
async def complete_mission(ctx, *, gang_name: str):
    global mission_active
    if not mission_active:
        await ctx.send("⚠️ لا توجد مهمة نشطة.")
        return

    gangs = get_gangs()
    if gang_name not in gangs:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current_points = gangs[gang_name].get("points", 0)
    update_gang(gang_name, {"points": current_points + 30})
    log_action(gang_name, +30, "إكمال مهمة القبض اليومية")

    style = gang_styles.get(gang_name, {"emoji": "🏆", "color": 0xFFD700})
    embed = discord.Embed(
        title=f"{style['emoji']} المهمة اكتملت!",
        description=f"✅ العصابة **{gang_name}** حصلت على **30 نقطة** لإكمال المهمة اليومية!",
        color=style["color"]
    )
    await ctx.send(embed=embed)
    mission_active = False

# ==============================
# المهمة التلقائية (بين 11 صباحًا و5 عصرًا)
# ==============================
@tasks.loop(minutes=20)
async def daily_task_loop():
    now = datetime.datetime.now(pytz.timezone("Asia/Riyadh"))
    if 11 <= now.hour < 17 and not mission_active:
        if random.randint(1, 6) == 3:
            await start_daily_mission()

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم {bot.user}")
    if not daily_task_loop.is_running():
        daily_task_loop.start()

# ==============================
# تشغيل البوت
# ==============================
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("⚠️ لم يتم العثور على التوكن.")
    else:
        bot.run(BOT_TOKEN)

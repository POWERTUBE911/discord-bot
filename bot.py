import discord
from discord.ext import commands, tasks
import asyncio
import os
import requests
import random
import datetime
import pytz

# ---------------- الإعدادات ----------------
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FIREBASE_URL = os.getenv("FIREBASE_URL")

OWNER_ID = int(os.getenv("OWNER_ID", "949047235574091589"))
POLICE_ROLE_ID = int(os.getenv("POLICE_ROLE_ID", "1342382610878951444"))
GANG_ROLE_ID = int(os.getenv("GANG_ROLE_ID", "1342825369080506781"))
DAILY_CHANNEL_ID = int(os.getenv("DAILY_CHANNEL_ID", "1342852921072574755"))

DAILY_REWARD_POINTS = 30
TZ = os.getenv("TZ", "Asia/Riyadh")

if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على DISCORD_BOT_TOKEN")
if not FIREBASE_URL:
    raise ValueError("❌ لم يتم العثور على FIREBASE_URL")

FIREBASE_URL = FIREBASE_URL.rstrip('/')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

mission_active = False
mission_target = None
mission_ends_at = None


# ---------------- Firebase REST ----------------
def get_gangs_data():
    try:
        url = f"{FIREBASE_URL}/gangs/list.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json() or {}
        return {}
    except Exception as e:
        print("خطأ بجلب العصابات:", e)
        return {}


def save_gang_points(gang_id, points):
    try:
        url = f"{FIREBASE_URL}/gangs/list/{gang_id}/points.json"
        resp = requests.put(url, json=points, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print("خطأ بحفظ النقاط:", e)
        return False


def find_gang_by_name(name):
    data = get_gangs_data()
    for gid, g in data.items():
        if g.get("name", "").strip().lower() == name.strip().lower():
            return gid, g
    return None, None


# ---------------- الأوامر ----------------

@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم أجد بيانات العصابات.")
        return

    embed = discord.Embed(title="📊 نقاط العصابات", color=discord.Color.gold())
    for gid, g in gangs.items():
        embed.add_field(
            name=f"🏴‍☠️ {g.get('name', gid)}",
            value=f"**{g.get('points', 0)}** نقطة",
            inline=False
        )
    await ctx.send(embed=embed)


@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ هذا الأمر مخصص لمالك البوت فقط.")
        return

    gid, gdata = find_gang_by_name(gang_name)
    if not gid:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current = gdata.get("points", 0)
    new = current + amount
    ok = save_gang_points(gid, new)

    if ok:
        embed = discord.Embed(
            title="💰 عملية إضافة نقاط",
            description=f"✅ تم إضافة **{amount}** نقطة إلى **{gdata.get('name')}**",
            color=discord.Color.green()
        )
        embed.add_field(name="📋 السبب", value=reason, inline=False)
        embed.add_field(name="🏆 المجموع الجديد", value=f"{new} نقطة", inline=False)
        embed.set_footer(text="نظام العصابات 🔥")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ حدث خطأ أثناء تحديث النقاط.")


@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ هذا الأمر مخصص لمالك البوت فقط.")
        return

    gid, gdata = find_gang_by_name(gang_name)
    if not gid:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current = gdata.get("points", 0)
    new = max(0, current - amount)
    ok = save_gang_points(gid, new)

    if ok:
        embed = discord.Embed(
            title="⚠️ عملية خصم نقاط",
            description=f"🔻 تم خصم **{amount}** نقطة من **{gdata.get('name')}**",
            color=discord.Color.red()
        )
        embed.add_field(name="📋 السبب", value=reason, inline=False)
        embed.add_field(name="🏆 المجموع الجديد", value=f"{new} نقطة", inline=False)
        embed.set_footer(text="نظام العصابات 🔥")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ حدث خطأ أثناء حفظ التغييرات.")


@bot.command(name="تجربة")
async def trial_task(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ هذا الأمر مخصص لمالك البوت فقط.")
        return

    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    if not police_role:
        await ctx.send("❌ لم أجد رتبة الشرطة.")
        return

    members = [m for m in police_role.members if not m.bot]
    if not members:
        await ctx.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    selected = random.choice(members)
    await ctx.send(
        f"🧪 تجربة — تم اختيار {selected.mention} كشرطي اليوم (تجريبي فقط، لا يؤثر على المهمة اليومية)."
    )


@bot.command(name="قبض")
async def capture(ctx, gang_name: str):
    global mission_active, mission_ends_at

    if not mission_active:
        await ctx.send("❌ لا توجد مهمة نشطة حالياً.")
        return

    now = datetime.datetime.now(pytz.timezone(TZ))
    if mission_ends_at and now > mission_ends_at:
        mission_active = False
        mission_ends_at = None
        await ctx.send("⚠️ انتهى وقت المهمة.")
        return

    gid, gdata = find_gang_by_name(gang_name)
    if not gid:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current = gdata.get("points", 0)
    new = current + DAILY_REWARD_POINTS
    ok = save_gang_points(gid, new)

    if ok:
        embed = discord.Embed(
            title="🎯 المهمة اليومية أُنجزت!",
            description=f"🚔 الشرطة قبضت على المجرمين!\n"
                        f"العصابة **{gdata.get('name')}** كسبت **{DAILY_REWARD_POINTS}** نقطة 🎉",
            color=discord.Color.blue()
        )
        embed.add_field(name="🏆 المجموع الجديد", value=f"{new} نقطة", inline=False)
        await ctx.send(embed=embed)
        mission_active = False
    else:
        await ctx.send("❌ فشل تحديث النقاط.")


# ---------------- المهمة اليومية ----------------

@tasks.loop(hours=24)
async def daily_task_loop():
    global mission_active, mission_target, mission_ends_at
    await bot.wait_until_ready()

    guild = bot.guilds[0] if bot.guilds else None
    if not guild:
        print("❌ لا يوجد سيرفر.")
        return

    police_role = guild.get_role(POLICE_ROLE_ID)
    if not police_role:
        print("❌ لم أجد رتبة الشرطة.")
        return

    members = [m for m in police_role.members if not m.bot]
    if not members:
        print("⚠️ لا يوجد أعضاء في رتبة الشرطة.")
        return

    selected = random.choice(members)
    channel = guild.get_channel(DAILY_CHANNEL_ID)
    if not channel:
        print("❌ لم أجد قناة المهمة اليومية.")
        return

    mission_active = True
    mission_target = selected
    now = datetime.datetime.now(pytz.timezone(TZ))
    mission_ends_at = now + datetime.timedelta(hours=1)

    embed = discord.Embed(
        title="🚨 المهمة اليومية بدأت!",
        description=f"الشرطي {selected.mention} بدأ المهمة!\n"
                    f"باقي **ساعة واحدة** فقط!\n"
                    f"استخدموا `!قبض <اسم_العصابة>` لإتمام المهمة وكسب {DAILY_REWARD_POINTS} نقطة 💪",
        color=discord.Color.blurple()
    )
    await channel.send(embed=embed)
    print(f"تم اختيار {selected} للمهمة اليومية.")


@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت: {bot.user}")
    if not daily_task_loop.is_running():
        daily_task_loop.start()


# ---------------- تشغيل البوت ----------------
bot.run(DISCORD_BOT_TOKEN)

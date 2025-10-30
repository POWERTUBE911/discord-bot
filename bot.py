import discord
from discord.ext import commands, tasks
import asyncio
import json
import random
import os
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, db
from config import BOT_TOKEN

# ================= إعداد Firebase =================
cred = credentials.Certificate("test.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"
})

# ================= إعداد Discord Bot =================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 949947235574095892  # اكتب هنا ID مالك البوت
POLICE_ROLE_ID = 1342832610878951444
GANG_ROLE_ID = 1342832658908057681
DAILY_CHANNEL_ID = 1432630812137754715

# ================= جلب بيانات العصابات =================
def get_gangs_data():
    ref = db.reference("gangs/list")
    data = ref.get()
    return data if data else {}

# ================= أوامر النقاط =================
@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(
        title="🏆 ترتيب العصابات الحالي",
        color=discord.Color.red()
    )

    for gang_id, gang_data in gangs.items():
        name = gang_data.get("name", f"عصابة {gang_id}")
        points = gang_data.get("points", 0)
        embed.add_field(name=name, value=f"النقاط: **{points}**", inline=False)

    await ctx.send(embed=embed)

# ================= إضافة نقاط =================
@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    target_gang = None

    for gang_id, gang_data in gangs.items():
        if gang_data.get("name", "").lower() == gang_name.lower():
            target_gang = db.reference(f"gangs/list/{gang_id}")
            break

    if not target_gang:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    points = target_gang.child("points").get() or 0
    new_points = points + amount
    target_gang.update({"points": new_points})

    await ctx.send(f"✅ تم إضافة {amount} نقطة لعصابة **{gang_name}** بسبب: {reason}")

# ================= خصم نقاط =================
@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    target_gang = None

    for gang_id, gang_data in gangs.items():
        if gang_data.get("name", "").lower() == gang_name.lower():
            target_gang = db.reference(f"gangs/list/{gang_id}")
            break

    if not target_gang:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    points = target_gang.child("points").get() or 0
    new_points = max(points - amount, 0)
    target_gang.update({"points": new_points})

    await ctx.send(f"⚠️ تم خصم {amount} نقطة من عصابة **{gang_name}** بسبب: {reason}")

# ================= المهام اليومية (مهمة القبض) =================
mission_active = False
current_target = None

@tasks.loop(minutes=30)
async def daily_task_loop():
    global mission_active, current_target
    now = datetime.datetime.now(pytz.timezone("Asia/Riyadh"))
    if 11 <= now.hour < 17 and not mission_active:
        guild = bot.guilds[0]
        police_role = guild.get_role(POLICE_ROLE_ID)
        if not police_role:
            return

        members = [m for m in police_role.members]
        if not members:
            return

        target = random.choice(members)
        channel = guild.get_channel(DAILY_CHANNEL_ID)
        current_target = target
        mission_active = True

        msg = (
            f"🚨 **مهمة القبض اليومية** 🚨\n\n"
            f"العصابة التي ستقبض على {target.mention} خلال ساعة ستحصل على **30 نقطة**!\n"
            f"👮‍♂️ بالتوفيق للجميع!\n\n"
            f"<@&{GANG_ROLE_ID}>"
        )
        await channel.send(msg)

        await asyncio.sleep(3600)
        if mission_active:
            await channel.send("❌ انتهى الوقت! فشلت المهمة اليومية.")
            mission_active = False
            current_target = None

@bot.command(name="قبض")
async def complete_mission(ctx, gang_name: str):
    global mission_active, current_target
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 ليس لديك صلاحية استخدام هذا الأمر.")
        return

    if not mission_active:
        await ctx.send("⚠️ لا توجد مهمة نشطة حالياً.")
        return

    gangs = get_gangs_data()
    target_gang = None
    for gang_id, gang_data in gangs.items():
        if gang_data.get("name", "").lower() == gang_name.lower():
            target_gang = db.reference(f"gangs/list/{gang_id}")
            break

    if not target_gang:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    points = target_gang.child("points").get() or 0
    new_points = points + 30
    target_gang.update({"points": new_points})

    channel = bot.get_channel(DAILY_CHANNEL_ID)
    await channel.send(f"✅ عصابة **{gang_name}** أكملت المهمة اليومية وحصلت على 30 نقطة!")

    mission_active = False
    current_target = None

@bot.command(name="تجربة")
async def test_mission(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 ليس لديك صلاحية استخدام هذا الأمر.")
        return

    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    members = [m for m in police_role.members]
    if not members:
        await ctx.send("❌ لا يوجد أعضاء برتبة الشرطة.")
        return

    target = random.choice(members)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    msg = (
        f"🧪 **تجربة مهمة القبض** 🧪\n\n"
        f"العصابة التي ستقبض على {target.mention} خلال ساعة ستحصل على **30 نقطة (تجربة)**\n\n"
        f"<@&{GANG_ROLE_ID}>"
    )
    await channel.send(msg)

# ================= تشغيل البوت =================
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم {bot.user}")
    daily_task_loop.start()

bot.run(BOT_TOKEN)

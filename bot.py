import discord
from discord.ext import commands, tasks
import asyncio
import random
import os
import json
import pytz
from datetime import datetime
from firebase import FirebaseApplication
from config import BOT_TOKEN, FIREBASE_URL

# إعداد النوايا
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
firebase_app = FirebaseApplication(FIREBASE_URL, None)

OWNER_ID = 949947235574095892  # رقمك
DAILY_CHANNEL_ID = 1432630812137754715
POLICE_ROLE_ID = 1342832610878951444
GANG_PING_ROLE_ID = 1342832658908057681

# 🧠 دالة جلب بيانات العصابات من الفايربيس
def get_live_gang_data():
    try:
        gangs_data = firebase_app.get("/gangs/list", None)
        if not gangs_data:
            print("⚠️ لا توجد بيانات عصابات.")
            return {}
        return gangs_data
    except Exception as e:
        print(f"❌ خطأ أثناء الاتصال بـ Firebase: {e}")
        return {}

# 🎯 حساب المستوى بناءً على النقاط
def calculate_level(points):
    if points < 100:
        return 1
    elif points < 250:
        return 2
    elif points < 500:
        return 3
    elif points < 1000:
        return 4
    else:
        return 5

# ✅ عند تشغيل البوت
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم {bot.user}")
    daily_task_loop.start()

# 🧾 عرض النقاط
@bot.command(name="نقاط")
async def show_points(ctx):
    gangs_data = get_live_gang_data()
    if not gangs_data:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="🏴‍☠️ قائمة العصابات", color=discord.Color.red())
    for gang_id, data in gangs_data.items():
        name = data.get("name", "غير معروف")
        points = data.get("points", 0)
        level = calculate_level(points)
        embed.add_field(
            name=f"🔹 {name}",
            value=f"النقاط: {points}\nالمستوى: {level}",
            inline=False
        )

    await ctx.send(embed=embed)

# ➕ إضافة نقاط
@bot.command(name="اضف")
async def add_points(ctx, points: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 لا تملك صلاحية استخدام هذا الأمر.")
        return

    gangs_data = get_live_gang_data()
    if not gangs_data:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    # البحث عن العصابة بالاسم
    gang_id = None
    for key, data in gangs_data.items():
        if data.get("name") == gang_name:
            gang_id = key
            break

    if not gang_id:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    # تحديث النقاط
    current_points = gangs_data[gang_id].get("points", 0)
    new_points = current_points + points
    firebase_app.put(f"/gangs/list/{gang_id}", "points", new_points)

    await ctx.send(f"✅ تم إضافة {points} نقطة لعصابة **{gang_name}** بسبب: {reason}")

# ➖ خصم نقاط
@bot.command(name="خصم")
async def remove_points(ctx, points: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 لا تملك صلاحية استخدام هذا الأمر.")
        return

    gangs_data = get_live_gang_data()
    if not gangs_data:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    gang_id = None
    for key, data in gangs_data.items():
        if data.get("name") == gang_name:
            gang_id = key
            break

    if not gang_id:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current_points = gangs_data[gang_id].get("points", 0)
    new_points = max(0, current_points - points)
    firebase_app.put(f"/gangs/list/{gang_id}", "points", new_points)

    await ctx.send(f"⚠️ تم خصم {points} نقطة من عصابة **{gang_name}** بسبب: {reason}")

# 🚔 مهمة القبض اليومية
current_target = None
mission_active = False

@tasks.loop(minutes=30)
async def daily_task_loop():
    now = datetime.now(pytz.timezone("Asia/Riyadh"))
    if 11 <= now.hour < 17 and not mission_active:
        await start_daily_mission()

async def start_daily_mission():
    global current_target, mission_active
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_ping_role = guild.get_role(GANG_PING_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not channel:
        print("⚠️ لم يتم العثور على الرتب أو القناة المحددة.")
        return

    members = [m for m in guild.members if police_role in m.roles]
    if not members:
        print("⚠️ لا يوجد أعضاء بشرطة السيرفر.")
        return

    target = random.choice(members)
    current_target = target
    mission_active = True

    await channel.send(
        f"🚨 **مهمة القبض اليومية!** 🚨\n"
        f"العصابة التي ستقبض على {target.mention} خلال ساعة ستحصل على **30 نقطة!**\n"
        f"{gang_ping_role.mention}"
    )

    await asyncio.sleep(3600)  # مدة المهمة ساعة
    if mission_active:
        await channel.send("⏰ انتهى الوقت! فشلت المهمة اليومية.")
        mission_active = False
        current_target = None

# ✅ أمر تجربة المهمة
@bot.command(name="تجربة")
async def test_daily(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 لا تملك صلاحية التجربة.")
        return
    await start_daily_mission()
    await ctx.send("✅ تم تنفيذ تجربة المهمة اليومية بنجاح!")

# ✅ تنفيذ القبض
@bot.command(name="قبض")
async def complete_mission(ctx, gang_name: str):
    global mission_active, current_target

    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 لا تملك صلاحية استخدام هذا الأمر.")
        return

    if not mission_active:
        await ctx.send("❌ لا توجد مهمة نشطة حالياً.")
        return

    gangs_data = get_live_gang_data()
    if not gangs_data:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    gang_id = None
    for key, data in gangs_data.items():
        if data.get("name") == gang_name:
            gang_id = key
            break

    if not gang_id:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    current_points = gangs_data[gang_id].get("points", 0)
    new_points = current_points + 30
    firebase_app.put(f"/gangs/list/{gang_id}", "points", new_points)

    await ctx.send(f"🏆 تمت إضافة **30 نقطة** لعصابة **{gang_name}** بسبب إكمال المهمة اليومية!")
    mission_active = False
    current_target = None

# 🚀 تشغيل البوت
bot.run(BOT_TOKEN)

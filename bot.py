import discord
from discord.ext import commands, tasks
import asyncio
import json
import requests
import random
import pytz
from datetime import datetime
import os

# ========== إعداد البوت ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 949004327547091589  # اكتب هنا ايديك
POLICE_ROLE_ID = 1243660718079514444  # رتبة الشرطة
GANG_ROLE_ID = 1324608938056078781   # رتبة العصابات (للتنبيه في المهمة)
DAILY_CHANNEL_ID = 1342852921072457575  # روم المهمة اليومية
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# ========== دوال Firebase ==========

def get_gangs_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/gangs/list.json")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            return []
        print(f"⚠️ خطأ أثناء الاتصال بـ Firebase: {response.status_code}")
    except Exception as e:
        print(f"❌ فشل جلب البيانات من Firebase: {e}")
    return []

def update_gang_points(gang_name, new_points):
    try:
        gangs = get_gangs_data()
        for i, gang in enumerate(gangs):
            if gang.get("name") == gang_name:
                gangs[i]["points"] = new_points
                break
        response = requests.put(f"{FIREBASE_URL}/gangs/list.json", json=gangs)
        if response.status_code == 200:
            print(f"✅ تم تحديث نقاط العصابة {gang_name}")
        else:
            print(f"⚠️ فشل تحديث النقاط: {response.status_code}")
    except Exception as e:
        print(f"❌ خطأ أثناء تحديث النقاط: {e}")

def add_log(gang_name, action, reason):
    log_entry = {
        "gang": gang_name,
        "action": action,
        "reason": reason,
        "timestamp": datetime.now(pytz.timezone("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        requests.post(f"{FIREBASE_URL}/infoLog.json", json=log_entry)
    except:
        pass

# ========== الأوامر ==========

@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات")
        return

    embed = discord.Embed(title="📊 عرض نقاط العصابات", color=discord.Color.red())
    for gang in gangs:
        name = gang.get("name", "غير معروف")
        points = gang.get("points", 0)
        embed.add_field(name=name, value=f"{points} نقطة", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    for gang in gangs:
        if gang.get("name") == gang_name:
            new_points = gang.get("points", 0) + amount
            update_gang_points(gang_name, new_points)
            add_log(gang_name, f"+{amount}", reason)
            await ctx.send(f"✅ تمت إضافة **{amount}** لـ **{gang_name}** (السبب: {reason})")
            return
    await ctx.send("❌ العصابة غير موجودة.")

@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    for gang in gangs:
        if gang.get("name") == gang_name:
            new_points = max(gang.get("points", 0) - amount, 0)
            update_gang_points(gang_name, new_points)
            add_log(gang_name, f"-{amount}", reason)
            await ctx.send(f"✅ تم خصم **{amount}** من **{gang_name}** (السبب: {reason})")
            return
    await ctx.send("❌ العصابة غير موجودة.")

# ========== المهمة اليومية ==========

@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(5)
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_role = guild.get_role(GANG_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not gang_role or not channel:
        print("⚠️ لم يتم العثور على الأدوار أو الروم المحدد.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await channel.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await channel.send(
        f"🚨 **بدأت المهمة اليومية!**\n"
        f"👮‍♂️ الشرطي: {chosen.mention}\n"
        f"🔥 العصابات: {gang_role.mention}\n"
        f"⏳ أمامكم ساعة واحدة لتنفيذ المهمة!"
    )

    await asyncio.sleep(3600)
    await channel.send("⏰ **انتهى وقت المهمة اليومية!**")

# ========== أمر تجربة المهمة اليومية ==========
@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_role = guild.get_role(GANG_ROLE_ID)

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await ctx.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await ctx.send(
        f"🧪 **تجربة المهمة اليومية فقط!**\n"
        f"👮‍♂️ الشرطي: {chosen.mention}\n"
        f"🔥 العصابات: {gang_role.mention}"
    )

# ========== إنهاء المهمة اليومية ==========
@bot.command(name="قبض")
async def catch_gang(ctx, gang_name: str):
    gangs = get_gangs_data()
    for gang in gangs:
        if gang.get("name") == gang_name:
            points = gang.get("points", 0) + 30
            update_gang_points(gang_name, points)
            add_log(gang_name, "+30", "إتمام المهمة اليومية")
            await ctx.send(f"🔥 العصابة **{gang_name}** أنجزت المهمة اليومية وحصلت على 30 نقطة! 🎉")
            return
    await ctx.send("❌ العصابة غير موجودة.")

# ========== عند تشغيل البوت ==========
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# ========== تشغيل البوت ==========
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على التوكن في الأسرار (Secrets)")
bot.run(DISCORD_BOT_TOKEN)

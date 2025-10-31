import discord
from discord.ext import commands, tasks
import asyncio
import json
import requests
import random
import os
from datetime import datetime, timedelta
import pytz

# =============== إعداد البوت ===============
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =============== الإعدادات ===============
OWNER_ID = 949947235574095892
POLICE_ROLE_ID = 1243660128709514444
GANG_ROLE_ID = 1324860938056067871
DAILY_CHANNEL_ID = 134285290127054755
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# =============== جلب بيانات العصابات ===============
def get_gangs_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/gangs/list.json")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "list" in data:
                return data["list"]
            elif isinstance(data, list):
                return data
        print(f"⚠️ خطأ أثناء الاتصال بـ Firebase: {response.status_code}")
        return []
    except Exception as e:
        print(f"⚠️ فشل في جلب البيانات من Firebase: {e}")
        return []

# =============== تحديث نقاط العصابة ===============
def update_gang_points(gang_name, new_points):
    try:
        requests.patch(f"{FIREBASE_URL}/gangs/list.json", json=[{"name": gang_name, "points": new_points}])
        return True
    except Exception as e:
        print(f"⚠️ فشل التحديث: {e}")
        return False

# =============== سجل العمليات ===============
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

# =============== الأوامر ===============
@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="📊 عرض نقاط العصابات", color=discord.Color.blue())
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
            await ctx.send(f"✅ تمت إضافة {amount} نقطة إلى **{gang_name}** (السبب: {reason})")
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
            await ctx.send(f"✅ تم خصم {amount} من **{gang_name}** (السبب: {reason})")
            return

    await ctx.send("❌ العصابة غير موجودة.")

# =============== المهمة اليومية ===============
@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(3)
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role:
        print("❌ لم يتم العثور على رتبة الشرطة.")
        return
    if not channel:
        print("❌ لم يتم العثور على الروم المحدد.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await channel.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await channel.send(f"🚓 المهمة اليومية بدأت! تم اختيار {chosen.mention} كمكلف بالمهمة. أمامه ساعة واحدة للتنفيذ ⏳")
    await asyncio.sleep(3600)
    await channel.send("⌛ انتهى وقت المهمة اليومية!")

# =============== التجربة ===============
@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = ctx.channel

    if not police_role:
        await ctx.send("❌ لم يتم العثور على رتبة الشرطة. تأكد من ID الرتبة.")
        print(f"⚠️ POLICE_ROLE_ID = {POLICE_ROLE_ID}")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await ctx.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await ctx.send(f"🎯 (تجربة فقط) تم اختيار {chosen.mention} كمكلف بالمهمة اليومية!")

# =============== إنهاء المهمة اليومية ===============
@bot.command(name="قبض")
async def catch_gang(ctx, gang_name: str):
    gangs = get_gangs_data()
    for gang in gangs:
        if gang.get("name") == gang_name:
            points = gang.get("points", 0) + 30
            update_gang_points(gang_name, points)
            add_log(gang_name, "+30", "إتمام المهمة اليومية")
            await ctx.send(f"🎉 أحسنت! العصابة **{gang_name}** كسبت 30 نقطة لإتمام المهمة اليومية.")
            return
    await ctx.send("❌ العصابة غير موجودة.")

# =============== عند تشغيل البوت ===============
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# ============ تشغيل البوت ============

import os

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على التوكن في الأسرار (DISCORD_BOT_TOKEN)")

bot.run(DISCORD_BOT_TOKEN)

import discord
from discord.ext import commands, tasks
import asyncio
import json
import requests
import random
import os
import pytz
from datetime import datetime, timedelta

# ===========================
# إعداد البوت
# ===========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 940904232574091589  # ضع هنا رقم الـ ID الخاص بك
POLICE_ROLE_ID = 1243660718079514444
DAILY_CHANNEL_ID = 1342852921072547575

# ===========================
# إعداد Firebase
# ===========================
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# ===========================
# دوال Firebase
# ===========================

def get_gangs_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/gangs/list.json")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                return data
            else:
                print("⚠️ البيانات في Firebase ليست بشكل صحيح.")
                return {}
        else:
            print(f"⚠️ خطأ أثناء الاتصال بـ Firebase: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ فشل جلب البيانات من Firebase: {e}")
        return {}

def update_gang_points(gang_name, points):
    try:
        response = requests.patch(
            f"{FIREBASE_URL}/gangs/list.json",
            json={gang_name: {"points": points}}
        )
        if response.status_code == 200:
            print(f"✅ تم تحديث نقاط العصابة {gang_name} إلى {points}")
        else:
            print(f"⚠️ فشل تحديث النقاط في Firebase: {response.status_code}")
    except Exception as e:
        print(f"❌ خطأ أثناء التحديث في Firebase: {e}")

def add_log(gang_name, action, reason):
    log_entry = {
        "gang": gang_name,
        "action": action,
        "reason": reason,
        "timestamp": datetime.now(pytz.timezone("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        requests.post(f"{FIREBASE_URL}/infoLog.json", json=log_entry)
    except Exception as e:
        print(f"⚠️ فشل إرسال السجل: {e}")

# ===========================
# أوامر البوت
# ===========================

@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(
        title="📊 عرض نقاط العصابات",
        color=discord.Color.red()
    )
    for name, data in gangs.items():
        points = data.get("points", 0)
        embed.add_field(name=name, value=f"{points} نقطة", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    new_points = gangs[gang_name].get("points", 0) + amount
    update_gang_points(gang_name, new_points)
    add_log(gang_name, f"إضافة {amount}", reason)
    await ctx.send(f"✅ تمت إضافة {amount} نقطة إلى **{gang_name}** (السبب: {reason})")

@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    new_points = max(gangs[gang_name].get("points", 0) - amount, 0)
    update_gang_points(gang_name, new_points)
    add_log(gang_name, f"خصم {amount}", reason)
    await ctx.send(f"✅ تم خصم {amount} من **{gang_name}** (السبب: {reason})")

# ===========================
# المهمة اليومية
# ===========================

@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(3)
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not channel:
        print("❌ لم يتم العثور على رتبة الشرطة أو الروم المحدد.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await channel.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await channel.send(f"🚨 المهمة اليومية بدأت! تم اختيار {chosen.mention} لتنفيذ المهمة أمامه ساعة واحدة ⏰")
    await asyncio.sleep(3600)
    await channel.send("⏳ انتهى وقت المهمة اليومية!")

@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = ctx.channel

    if not police_role:
        await ctx.send("❌ لم يتم العثور على رتبة الشرطة.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await ctx.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await ctx.send(f"🎯 تم اختيار {chosen.mention} (تجربة فقط).")

@bot.command(name="قبض")
async def catch_gang(ctx, gang_name: str):
    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    new_points = gangs[gang_name].get("points", 0) + 30
    update_gang_points(gang_name, new_points)
    add_log(gang_name, "إتمام المهمة اليومية", "إضافة 30 نقطة للمهمة اليومية")
    await ctx.send(f"✅ تمت إضافة 30 نقطة إلى **{gang_name}** لإتمام المهمة اليومية!")

# ===========================
# عند تشغيل البوت
# ===========================

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# ===========================
# تشغيل البوت
# ===========================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على التوكن في الأسرار (DISCORD_BOT_TOKEN)")

bot.run(DISCORD_BOT_TOKEN)

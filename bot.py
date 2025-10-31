import discord
from discord.ext import commands, tasks
import asyncio
import json
import requests
import random
import pytz
import os
from datetime import datetime

# ================= إعداد Discord Bot =================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= إعداد ثابتات =================
OWNER_ID = 940090234570191589  # آيدي المالك
POLICE_ROLE_ID = 1243660218798514444  # رتبة الشرطة
GANG_ROLE_ID = 123480639805670871  # رتبة العصابات
DAILY_CHANNEL_ID = 134282590127547555  # روم المهمات اليومية
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"  # رابط Firebase

# ================= دوال Firebase =================
def get_gangs_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/gangs.json")
        if response.status_code == 200:
            return response.json() or {}
        else:
            print(f"⚠️ خطأ أثناء الاتصال بـ Firebase: {response.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ خطأ في جلب بيانات Firebase: {e}")
        return {}

def update_gang_points(gang_name, points):
    try:
        response = requests.patch(f"{FIREBASE_URL}/gangs/{gang_name}.json", json={"points": points})
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ خطأ أثناء تحديث النقاط: {e}")
        return False

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
        print(f"⚠️ خطأ أثناء تسجيل الحدث: {e}")

# ================= أوامر البوت =================
@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="📊 عرض نقاط العصابات", color=discord.Color.red())
    for gang, data in gangs.items():
        points = data.get("points", 0)
        embed.add_field(name=gang, value=f"**{points} نقطة**", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    new_points = gangs[gang_name].get("points", 0) + amount
    update_gang_points(gang_name, new_points)
    add_log(gang_name, f"إضافة {amount} نقطة", reason)
    await ctx.send(f"✅ تم إضافة {amount} نقطة إلى عصابة **{gang_name}** 🎯 السبب: {reason}")

@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    new_points = max(gangs[gang_name].get("points", 0) - amount, 0)
    update_gang_points(gang_name, new_points)
    add_log(gang_name, f"خصم {amount} نقطة", reason)
    await ctx.send(f"⚠️ تم خصم {amount} نقطة من عصابة **{gang_name}** ⛔ السبب: {reason}")

# ================= المهمة اليومية =================
@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(3)
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not channel:
        print("❌ لم يتم العثور على رتبة الشرطة أو القناة اليومية.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await channel.send("🚫 لا يوجد أفراد شرطة حالياً.")
        return

    chosen = random.choice(police_members)
    await channel.send(f"🚨 بدأت المهمة اليومية! الشرطي المختار اليوم هو: {chosen.mention}")
    await asyncio.sleep(3600)
    await channel.send("⌛ انتهى وقت المهمة اليومية! لم يتم تنفيذ القبض بعد 😢")

@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    police_members = [m for m in police_role.members if not m.bot]

    if not police_members:
        await ctx.send("🚫 لا يوجد أفراد شرطة حالياً.")
        return

    chosen = random.choice(police_members)
    await ctx.send(f"🎯 (تجربة فقط) الشرطي المختار هو: {chosen.mention}")

@bot.command(name="قبض")
async def catch_gang(ctx, gang_name: str):
    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    points = gangs[gang_name].get("points", 0) + 30
    update_gang_points(gang_name, points)
    add_log(gang_name, "إنهاء المهمة اليومية", "إتمام القبض")
    await ctx.send(f"🎉 العصابة **{gang_name}** أنجزت المهمة اليومية بنجاح وتمت مكافأتها بـ 30 نقطة! 🔥")

# ================= تشغيل البوت =================
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# 🔹 توكن البوت من الأسرار فقط 🔹
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على توكن البوت في الأسرار!")

bot.run(DISCORD_BOT_TOKEN)

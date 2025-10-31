import discord
from discord.ext import commands, tasks
import asyncio
import json
import requests
import random
import os
import pytz
from datetime import datetime, timedelta

# ================= إعداد البوت =================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 94009423574091589
POLICE_ROLE_ID = 1243662018708514444
GANG_ROLE_ID = 1324860938056067871
DAILY_CHANNEL_ID = 1342852921072547575

# ================= إعداد Firebase =================
FIREBASE_URL = os.getenv("FIREBASE_URL")

if not FIREBASE_URL:
    raise ValueError("❌ لم يتم العثور على FIREBASE_URL في إعدادات الأسرار")

def get_gangs_data():
    """جلب بيانات العصابات"""
    try:
        response = requests.get(f"{FIREBASE_URL}/gangs/list.json")
        if response.status_code == 200:
            data = response.json()
            # معالجة إذا كانت قائمة داخل dict
            if isinstance(data, dict) and "list" in data:
                return data["list"]
            return data or {}
        else:
            print(f"⚠️ خطأ في الاتصال بـ Firebase: {response.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ فشل في جلب بيانات Firebase: {e}")
        return {}

def update_gang_points(gang_name, points):
    """تحديث نقاط العصابة"""
    try:
        response = requests.patch(f"{FIREBASE_URL}/gangs/list.json", json={gang_name: {"points": points}})
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ خطأ في تحديث البيانات: {e}")
        return False

def add_log(gang_name, action, reason):
    """إضافة سجل جديد"""
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

# ================= أوامر البوت =================

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
        embed.add_field(name=name, value=f"**{points} نقطة**", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    for gang in gangs:
        if gang.get("name") == gang_name:
            new_points = gang.get("points", 0) + amount
            gang["points"] = new_points
            update_gang_points(gang_name, new_points)
            add_log(gang_name, f"إضافة {amount} نقطة", reason)
            await ctx.send(f"✅ تمت إضافة **{amount}** نقطة إلى **{gang_name}** (السبب: {reason})")
            return

    await ctx.send("❌ العصابة غير موجودة.")

@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    for gang in gangs:
        if gang.get("name") == gang_name:
            new_points = max(gang.get("points", 0) - amount, 0)
            gang["points"] = new_points
            update_gang_points(gang_name, new_points)
            add_log(gang_name, f"خصم {amount} نقطة", reason)
            await ctx.send(f"✅ تم خصم **{amount}** نقطة من **{gang_name}** (السبب: {reason})")
            return

    await ctx.send("❌ العصابة غير موجودة.")

# ================= المهام اليومية =================

@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(3)
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not channel:
        print("⚠️ لم يتم العثور على الرتبة أو القناة اليومية.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await channel.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await channel.send(f"🚨 **بدأت المهمة اليومية!**\nتم اختيار {chosen.mention} لتنفيذها خلال ساعة واحدة!")
    await asyncio.sleep(3600)
    await channel.send("⌛ انتهى وقت المهمة اليومية!")

@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = ctx.channel

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await ctx.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    await ctx.send(f"🎯 (تجربة فقط) تم اختيار {chosen.mention} كمكلف بالمهمة اليومية!")

@bot.command(name="قبض")
async def catch_gang(ctx, gang_name: str):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    for gang in gangs:
        if gang.get("name") == gang_name:
            points = gang.get("points", 0) + 30
            gang["points"] = points
            update_gang_points(gang_name, points)
            add_log(gang_name, "إتمام مهمة يومية", "تمت المهمة اليومية بنجاح")
            await ctx.send(f"🎉 العصابة **{gang_name}** أكملت المهمة اليومية وربحت **30 نقطة**!")
            return

    await ctx.send("❌ العصابة غير موجودة.")

# ================= عند تشغيل البوت =================

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# ================= تشغيل البوت =================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على DISCORD_BOT_TOKEN في الأسرار")

bot.run(DISCORD_BOT_TOKEN)

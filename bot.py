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

# ================= إعداد القيم =================
OWNER_ID = 940090423574091589   # 🧑‍💼 مالك البوت
POLICE_ROLE_ID = 1243662018789514444  # 🚓 رتبة الشرطة
GANG_ROLE_ID = 132480693805667871  # 🕵️‍♂️ رتبة العصابات
DAILY_CHANNEL_ID = 134285920125747555  # 💬 روم المهام اليومية

# ================= إعداد Firebase =================
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# ================= دوال المساعدة =================
def get_gangs_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/gangs.json")
        if response.status_code == 200:
            data = response.json() or {}
            # تحويل القائمة إلى قاموس لو كانت البيانات list
            if isinstance(data, list):
                data = {f"gang_{i+1}": g for i, g in enumerate(data) if isinstance(g, dict)}
            return data
        else:
            print(f"⚠️ خطأ أثناء الاتصال بـ Firebase: {response.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ خطأ في جلب بيانات Firebase: {e}")
        return {}

def update_gang_points(gang_name, points):
    try:
        requests.patch(f"{FIREBASE_URL}/gangs/{gang_name}.json", json={"points": points})
        return True
    except Exception as e:
        print(f"⚠️ خطأ في تحديث نقاط العصابة: {e}")
        return False

def add_log(gang_name, action, reason):
    log_entry = {
        "gang": gang_name,
        "action": action,
        "reason": reason,
        "time": datetime.now(pytz.timezone("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        requests.post(f"{FIREBASE_URL}/infoLog.json", json=log_entry)
    except:
        pass

# ================= الأوامر =================
@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="📊 نقاط العصابات", color=discord.Color.blue())
    for gang, data in gangs.items():
        points = data.get("points", 0)
        embed.add_field(name=gang, value=f"🔹 {points} نقطة", inline=False)

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
    add_log(gang_name, f"+{amount}", reason)
    await ctx.send(f"✅ تمت إضافة **{amount}** نقطة إلى **{gang_name}** بسبب: {reason}")

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
    add_log(gang_name, f"-{amount}", reason)
    await ctx.send(f"✅ تم خصم **{amount}** نقطة من **{gang_name}** بسبب: {reason}")

# ================= المهام اليومية =================
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
    await channel.send(f"🚨 **بدأت المهمة اليومية!**\nالضابط المختار اليوم هو: {chosen.mention}.\nلديكم ساعة واحدة فقط لتنفيذ المهام!")

    await asyncio.sleep(3600)
    await channel.send("⌛ انتهى وقت المهمة اليومية.")

@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = ctx.channel

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await ctx.send("❌ لا يوجد أفراد شرطة.")
        return

    chosen = random.choice(police_members)
    await ctx.send(f"🧪 تجربة المهمة اليومية: تم اختيار {chosen.mention} (اختبار فقط).")

@bot.command(name="قبض")
async def catch_gang(ctx, gang_name: str):
    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    points = gangs[gang_name].get("points", 0) + 30
    update_gang_points(gang_name, points)
    add_log(gang_name, "+30", "إتمام المهمة اليومية")
    await ctx.send(f"🎯 العصابة **{gang_name}** أكملت المهمة اليومية بنجاح! حصلت على **30** نقطة 💰")

# ================= تشغيل البوت =================
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول بنجاح باسم: {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# التوكن من أسرار GitHub
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على متغير DISCORD_BOT_TOKEN في الأسرار.")

bot.run(DISCORD_BOT_TOKEN)

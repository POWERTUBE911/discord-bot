import discord
from discord.ext import commands, tasks
import asyncio
import json
import requests
import random
import pytz
from datetime import datetime, timedelta

# ============ إعداد Discord Bot ============
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 94009423574091589  # مالك البوت
POLICE_ROLE_ID = 1243662018789514444  # رتبة الشرطة
GANG_ROLE_ID = 132486093865067871  # رتبة العصابة (للمنشن)
DAILY_CHANNEL_ID = 13428529012754755  # الروم الخاص بالمهمة اليومية

# ============ إعداد Firebase ============
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# ============ دوال Firebase ============
def get_gangs_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/gangs.json")
        if response.status_code == 200:
            return response.json() or {}
        else:
            print(f"⚠️ خطأ في الاتصال بـ Firebase: {response.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ خطأ في جلب البيانات من Firebase: {e}")
        return {}

def update_gang_points(gang_name, points):
    try:
        response = requests.patch(f"{FIREBASE_URL}/gangs/{gang_name}.json", json={"points": points})
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ خطأ في تحديث النقاط: {e}")
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
    except:
        pass

# ============ أوامر البوت ============
@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="📊 عرض نقاط العصابات", color=discord.Color.gold())
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
    await ctx.send(f"✅ تمت إضافة **{amount}** نقطة إلى **{gang_name}**.\n🎯 السبب: {reason}")

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
    await ctx.send(f"⚠️ تم خصم **{amount}** نقطة من **{gang_name}**.\n🎯 السبب: {reason}")

# ============ المهام اليومية ============
@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(3)
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not channel:
        print("❌ لم يتم العثور على رتبة الشرطة أو الروم اليومي.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await channel.send("🚨 لا يوجد أي شرطي حاليًا.")
        return

    chosen = random.choice(police_members)
    await channel.send(f"🚨 تم اختيار {chosen.mention} لتنفيذ المهمة اليومية! أمامكم ساعة للقبض عليه 🔥")

    await asyncio.sleep(3600)
    await channel.send("⌛ انتهى وقت المهمة اليومية! من لم يقبض عليه فقد خسر!")

@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    channel = ctx.channel
    police_members = [m for m in police_role.members if not m.bot]

    if not police_members:
        await ctx.send("🚨 لا يوجد شرطة للتجربة.")
        return

    chosen = random.choice(police_members)
    await ctx.send(f"🚨 تجربة: تم اختيار {chosen.mention} كمطلوب اليومي (تجريبي فقط).")

@bot.command(name="قبض")
async def catch_gang(ctx, gang_name: str):
    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    points = gangs[gang_name].get("points", 0) + 30
    update_gang_points(gang_name, points)
    add_log(gang_name, "مهمة يومية ناجحة", "إتمام القبض بنجاح")
    await ctx.send(f"🎉 تهانينا! العصابة **{gang_name}** أكملت المهمة اليومية بنجاح وكسبت **30 نقطة**!")

# ============ عند تشغيل البوت ============
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت: {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# ============ تشغيل البوت ============
DISCORD_BOT_TOKEN = "ضع_توكن_البوت_هنا"
bot.run(DISCORD_BOT_TOKEN)

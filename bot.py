import discord
from discord.ext import commands, tasks
import asyncio
import random
import json
import os
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, db
from config import BOT_TOKEN

# ================= إعداد Firebase من الأسرار =================
# قراءة بيانات الخدمة من السر FIREBASE_KEY في GitHub
firebase_key_json = os.getenv("FIREBASE_KEY")
if not firebase_key_json:
    raise ValueError("❌ لم يتم العثور على السر FIREBASE_KEY في إعدادات GitHub!")

cred_dict = json.loads(firebase_key_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app'
})

# ================= إعداد بوت Discord =================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= إعدادات أساسية =================
OWNER_ID = 949947325574091892
POLICE_ROLE_ID = 1342828601878951444
GANG_ROLE_ID = 1342828659008056781
DAILY_CHANNEL_ID = 1423660121377344715

mission_active = False
current_target = None

# ================= دالة لجلب بيانات العصابات =================
def get_gangs_data():
    ref = db.reference("gangs/list")
    data = ref.get()
    return data if data else {}

# ================= أوامر العصابات =================

@bot.command(name="عرض")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="🩸 نقاط العصابات", color=discord.Color.red())
    for gang_id, gang_data in gangs.items():
        name = gang_data.get("name", f"عصابة {gang_id}")
        points = gang_data.get("points", 0)
        embed.add_field(name=name, value=f"النقاط: **{points}**", inline=False)

    await ctx.send(embed=embed)


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

    await ctx.send(f"✅ تمت إضافة **{amount}** نقطة لعصابة **{gang_name}** بسبب: {reason}")


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

    await ctx.send(f"⚠️ تم خصم **{amount}** نقطة من عصابة **{gang_name}** بسبب: {reason}")

# ================= المهام اليومية =================

@tasks.loop(minutes=30)
async def daily_task_loop():
    global mission_active, current_target
    now = datetime.datetime.now(pytz.timezone("Asia/Riyadh"))
    if now.hour != 17 or mission_active:
        return

    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    if not police_role:
        return

    members = [m for m in police_role.members]
    if not members:
        return

    target = random.choice(members)
    channel = guild.get_channel(DAILY_CHANNEL_ID)
    mission_active = True
    current_target = target

    msg = (
        "🚨 **مهمة اليوم** 🚨\n\n"
        f"🎯 الهدف: {target.mention}\n"
        "**المدة:** ساعة واحدة للحصول على **30** نقطة\n\n"
        f"@&{GANG_ROLE_ID}"
    )
    await channel.send(msg)

    await asyncio.sleep(3600)
    if mission_active:
        await channel.send("❌ انتهى الوقت! فشلت المهمة اليومية.")
        mission_active = False
        current_target = None


@bot.command(name="انهاء")
async def complete_mission(ctx, gang_name: str):
    global mission_active, current_target
    if ctx.author.id != OWNER_ID:
        await ctx.send("🚫 ليس لديك صلاحية استخدام هذا الأمر.")
        return

    if not mission_active:
        await ctx.send("⚠️ لا توجد مهمة نشطة حاليًا.")
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
    await channel.send(f"✅ أنهت عصابة **{gang_name}** المهمة اليومية وحصلت على **30** نقطة!")

    mission_active = False
    current_target = None

# ================= تشغيل البوت =================
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت {bot.user}")
    daily_task_loop.start()

bot.run(BOT_TOKEN)

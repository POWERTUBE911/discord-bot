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
firebase_key_json = os.getenv("FIREBASE_KEY")  # قراءة المفتاح من أسرار GitHub

if not firebase_key_json:
    raise ValueError("❌ لم يتم العثور على السر FIREBASE_KEY في إعدادات GitHub!")

try:
    cred_dict = json.loads(firebase_key_json)
except json.JSONDecodeError as e:
    raise ValueError(f"❌ خطأ في تنسيق FIREBASE_KEY: {e}")

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app'
})

# ================= إعداد Discord Bot =================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= متغيرات عامة =================
OWNER_ID = 940947325574091589
POLICE_ROLE_ID = 1342823681087895144
GANG_ROLE_ID = 1342825860908056781
DAILY_CHANNEL_ID = 1423668012301275475

mission_active = False
current_target = None


# ================= دالة جلب بيانات العصابات =================
def get_gangs_data():
    ref = db.reference("gangs/list")
    data = ref.get()
    return data if data else {}


# ================= أوامر البوت =================

@bot.command(name="العصابات")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="📊 نقاط العصابات", color=discord.Color.red())
    for gang_id, gang_data in gangs.items():
        name = gang_data.get("name", f"عصابة {gang_id}")
        points = gang_data.get("points", 0)
        embed.add_field(name=name, value=f"**{points}** نقطة", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
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
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
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

    await ctx.send(f"✅ تم خصم **{amount}** نقطة من عصابة **{gang_name}** بسبب: {reason}")


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
        f"🚨 **مهمة اليوم** 🚨\n\n"
        f"الهدف: **{target.mention}**\n"
        f"المهلة: ساعة واحدة للحصول على **30 نقطة** 🎯\n\n"
        f"<@&{GANG_ROLE_ID}>"
    )
    await channel.send(msg)

    await asyncio.sleep(3600)
    if mission_active:
        await channel.send("⏰ انتهى الوقت! لم تُكمل أي عصابة المهمة.")
        mission_active = False
        current_target = None


@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول بنجاح باسم {bot.user}")
    daily_task_loop.start()


bot.run(BOT_TOKEN)

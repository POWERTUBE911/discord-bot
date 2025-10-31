import discord
from discord.ext import commands, tasks
import asyncio
import json
import random
import os
import pytz
import firebase_admin
from firebase_admin import credentials, db

# ============================
# 🔐 تحميل مفاتيح Secrets
# ============================
firebase_key_json = os.getenv("FIREBASE_KEY")
if not firebase_key_json:
    raise ValueError("❌ لم يتم العثور على FIREBASE_KEY في إعدادات Secrets")

try:
    cred_dict = json.loads(firebase_key_json)
except json.JSONDecodeError as e:
    raise ValueError(f"❌ خطأ في JSON الخاص بـ FIREBASE_KEY: {e}")

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://gang-war-2-default-rtdb.firebaseio.com/'
})

# ============================
# ⚙️ إعدادات البوت
# ============================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 940049325734091589
POLICE_ROLE_ID = 1243268120897851144
GANG_ROLE_ID = 1348293088056806781
DAILY_CHANNEL_ID = 1348300631201752745

mission_active = False
current_target = None

# ============================
# 📦 Firebase Utility
# ============================
def get_gangs_data():
    ref = db.reference("gangs/list")
    data = ref.get()
    return data if data else {}

# ============================
# 💬 الأوامر
# ============================

@bot.command(name="نقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات")
        return

    embed = discord.Embed(title="🏴‍☠️ نقاط العصابات", color=discord.Color.red())
    for gang_id, gang_data in gangs.items():
        name = gang_data.get("name", "بدون اسم")
        points = gang_data.get("points", 0)
        embed.add_field(name=name, value=f"**النقاط:** {points}", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    target_ref = None

    for gid, data in gangs.items():
        if data.get("name") == gang_name:
            target_ref = db.reference(f"gangs/list/{gid}")
            break

    if not target_ref:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    current_points = target_ref.child("points").get() or 0
    target_ref.update({"points": current_points + amount})

    embed = discord.Embed(title="✅ تم إضافة نقاط", color=discord.Color.green())
    embed.add_field(name="العصابة", value=gang_name, inline=True)
    embed.add_field(name="النقاط المضافة", value=str(amount), inline=True)
    embed.add_field(name="السبب", value=reason, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    target_ref = None

    for gid, data in gangs.items():
        if data.get("name") == gang_name:
            target_ref = db.reference(f"gangs/list/{gid}")
            break

    if not target_ref:
        await ctx.send("❌ العصابة غير موجودة.")
        return

    current_points = target_ref.child("points").get() or 0
    target_ref.update({"points": max(0, current_points - amount)})

    embed = discord.Embed(title="📉 تم خصم نقاط", color=discord.Color.orange())
    embed.add_field(name="العصابة", value=gang_name, inline=True)
    embed.add_field(name="النقاط المخصومة", value=str(amount), inline=True)
    embed.add_field(name="السبب", value=reason, inline=False)
    await ctx.send(embed=embed)

# ============================
# 💣 أمر القبض
# ============================
@bot.command(name="قبض")
async def arrest(ctx):
    await ctx.send("🚓 تمت عملية القبض بنجاح!")

# ============================
# 🧪 أمر تجربة
# ============================
@bot.command(name="تجربة")
async def test(ctx):
    await ctx.send("✅ البوت شغال تمام!")

# ============================
# 🎯 تشغيل البوت
# ============================
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم: {bot.user}")
    print("⚡ البوت جاهز للعمل.")

# ============================
# 🚀 التشغيل
# ============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على BOT_TOKEN في Secrets")

bot.run(BOT_TOKEN)

import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import requests
import random
import pytz

# ============ إعداد Discord Bot ============
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 940094235374091589
POLICE_ROLE_ID = 1243268210878951444
GANG_ROLE_ID = 1342868930865067871
DAILY_CHANNEL_ID = 1342852920172574755

# ============ إعداد Firebase (بدون مفتاح) ============
firebase_url = os.getenv("FIREBASE_URL")
if not firebase_url:
    raise ValueError("❌ لم يتم العثور على FIREBASE_URL في إعدادات GitHub!")

def get_gangs_data():
    try:
        response = requests.get(f"{firebase_url}/gangs/list.json")
        if response.status_code == 200:
            data = response.json()
            return data if data else {}
        else:
            print(f"⚠️ خطأ في الاتصال بـ Firebase: {response.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ فشل في جلب البيانات من Firebase: {e}")
        return {}

def update_gang_points(gang_name, points):
    try:
        response = requests.patch(f"{firebase_url}/gangs/list/{gang_name}.json", json={"points": points})
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ خطأ في تحديث النقاط: {e}")
        return False

# ============ أوامر البوت ============
@bot.command(name="النقاط")
async def show_points(ctx):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    embed = discord.Embed(title="📊 عرض نقاط العصابات", color=discord.Color.red())
    for gang_name, gang_data in gangs.items():
        points = gang_data.get("points", 0)
        embed.add_field(name=gang_name, value=f"نقاط: **{points}**", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="اضافة")
async def add_points(ctx, gang_name: str, amount: int):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ لم يتم العثور على العصابة المحددة.")
        return

    new_points = gangs[gang_name].get("points", 0) + amount
    update_gang_points(gang_name, new_points)
    await ctx.send(f"✅ تم إضافة {amount} نقطة إلى العصابة {gang_name}. المجموع الآن: {new_points}")

@bot.command(name="خصم")
async def remove_points(ctx, gang_name: str, amount: int):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if gang_name not in gangs:
        await ctx.send("❌ لم يتم العثور على العصابة المحددة.")
        return

    new_points = max(0, gangs[gang_name].get("points", 0) - amount)
    update_gang_points(gang_name, new_points)
    await ctx.send(f"✅ تم خصم {amount} نقطة من العصابة {gang_name}. المجموع الآن: {new_points}")

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت: {bot.user}")

# ============ تشغيل البوت ============
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ لم يتم العثور على DISCORD_BOT_TOKEN في إعدادات GitHub!")

bot.run(DISCORD_BOT_TOKEN)

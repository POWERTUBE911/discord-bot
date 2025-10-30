import discord
from discord.ext import commands, tasks
import random
import asyncio
import requests
from datetime import datetime, timedelta
import pytz
from config import BOT_TOKEN, FIREBASE_URL

# إعداد intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# إعداد المنطقة الزمنية (الرياض)
riyadh_tz = pytz.timezone("Asia/Riyadh")

# تعريف المتغيرات العامة
OWNER_ID = 949947235574095892  # ايدي المالك
POLICE_ROLE_ID = 1342832610878951444  # رول الشرطة
GANG_PING_ROLE_ID = 1342832658908057681  # رول العصابات
MISSION_CHANNEL_ID = 1432630812137754715  # روم المهمات اليومية
FIREBASE_PATH = f"{FIREBASE_URL}/gangs.json"

# === الدوال المساعدة ===

def get_gangs_data():
    """جلب بيانات العصابات من Firebase"""
    try:
        res = requests.get(FIREBASE_PATH)
        if res.status_code == 200 and res.text.strip() != "null":
            return res.json()
        return {}
    except Exception as e:
        print(f"Firebase Error: {e}")
        return {}

def update_gang_points(gang_name, points, reason):
    """تحديث نقاط العصابة"""
    data = get_gangs_data()
    if gang_name in data:
        gang_data = data[gang_name]
        gang_data["points"] = gang_data.get("points", 0) + points
        gang_data["last_reason"] = reason
        requests.patch(FIREBASE_PATH, json={gang_name: gang_data})
        return True
    return False

# === أوامر البوت ===

@bot.event
async def on_ready():
    print(f"✅ تم تشغيل البوت بنجاح باسم {bot.user}")
    daily_mission.start()

@bot.command()
async def تجربة(ctx):
    """اختبار المهمة اليومية بدون تأثير فعلي"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ ما عندك صلاحية لاستخدام هذا الأمر.")
    await send_mission(test_mode=True)
    await ctx.send("✅ تمت تجربة المهمة بنجاح (بدون تأثير على البيانات).")

@bot.command()
async def قبض(ctx, *, gang_name: str = None):
    """إكمال مهمة القبض"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ ما عندك صلاحية لاستخدام هذا الأمر.")
    if not gang_name:
        return await ctx.send("❗ استخدم الأمر بهذا الشكل: `!قبض اسم_العصابة`")
    
    updated = update_gang_points(gang_name, 30, "إكمال مهمة يومية")
    if updated:
        await ctx.send(f"✅ تمت إضافة 30 نقطة لعصابة **{gang_name}** بسبب إكمال المهمة اليومية!")
    else:
        await ctx.send("❌ العصابة غير موجودة في قاعدة البيانات!")

# === نظام المهام اليومية ===

@tasks.loop(minutes=60)
async def daily_mission():
    """تفعيل مهمة القبض اليومية في وقت عشوائي"""
    now = datetime.now(riyadh_tz)
    if 11 <= now.hour < 17:  # بين 11 صباحاً و5 العصر
        # تأكد من أنها أول مرة فقط
        if random.randint(1, 3) == 1:  # احتمال 1/3 لتفعيل المهمة
            await send_mission()

async def send_mission(test_mode=False):
    """نشر مهمة القبض اليومية"""
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_role = guild.get_role(GANG_PING_ROLE_ID)
    channel = guild.get_channel(MISSION_CHANNEL_ID)

    if not (police_role and gang_role and channel):
        print("⚠️ تأكد من صحة الآي ديهات الخاصة بالرولات والروم.")
        return

    # اختيار شرطي عشوائي
    police_members = [m for m in guild.members if police_role in m.roles]
    if not police_members:
        print("⚠️ لا يوجد أعضاء برتبة الشرطة.")
        return

    target = random.choice(police_members)
    msg = await channel.send(
        f"🚨 **مهمة القبض اليومية!** 🚨\n"
        f"لدينا مهمة قبض اليوم!\n"
        f"العصابة التي ستقبض على {target.mention} خلال ساعة من الآن 🔥 "
        f"ستحصل على **30 نقطة**!\n\n"
        f"{gang_role.mention}"
    )

    if not test_mode:
        # الانتظار لمدة ساعة
        await asyncio.sleep(3600)
        await channel.send("⌛ انتهى الوقت ولم يتم تنفيذ المهمة! المهمة **فشلت** ❌")

# تشغيل البوت
bot.run(BOT_TOKEN)

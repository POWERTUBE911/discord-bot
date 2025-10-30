import discord
from discord.ext import commands, tasks
import asyncio
import random
import json
import os
from firebase import firebase
from config import BOT_TOKEN, FIREBASE_URL, OWNER_ID, DAILY_CHANNEL_ID, POLICE_ROLE_ID, MENTION_ROLE_ID

# إعداد النوايا (intents)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)

# 🧩 دالة لحساب مستوى العصابة
def calculate_level(points, rewards_levels):
    level = 0
    sorted_rewards = sorted(rewards_levels, key=lambda r: r.get("points", 0))
    for reward in sorted_rewards:
        if points >= reward.get("points", 0):
            level = reward.get("level", 0)
        else:
            break
    return level


# 🧠 جلب بيانات العصابات من Firebase
def get_live_gang_data():
    try:
        gangs_data = firebase_app.get("/gangs/list", None)
        if not gangs_data:
            print("⚠️ لا توجد بيانات عصابات.")
            return {}, []
        rewards_data = firebase_app.get("/rewards/levels", None)
        rewards_levels = rewards_data if rewards_data else []
        return gangs_data, rewards_levels
    except Exception as e:
        print(f"⚠️ خطأ في Firebase: {e}")
        return {}, []


# ✅ عند تشغيل البوت
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم {bot.user}")
    daily_task_loop.start()


# 🏆 أمر عرض النقاط
@bot.command(name="نقاط")
async def show_points(ctx):
    await ctx.send("📊 جاري جلب بيانات العصابات...")
    gangs_data, rewards_levels = get_live_gang_data()
    if not gangs_data:
        await ctx.send("❌ لم أجد بيانات العصابات في Firebase.")
        return

    embed = discord.Embed(
        title="🏆 ترتيب العصابات الحالي",
        color=discord.Color.red()
    )
    for name, data in sorted(gangs_data.items(), key=lambda x: x[1].get("points", 0), reverse=True):
        embed.add_field(
            name=f"{name}",
            value=f"**النقاط:** {data.get('points', 0)}\n**المستوى:** {calculate_level(data.get('points', 0), rewards_levels)}",
            inline=True
        )
    await ctx.send(embed=embed)


# 🔺 أمر إضافة نقاط (للمالك فقط)
@bot.command(name="اضف")
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return

    try:
        gangs_data = firebase_app.get("/gangs/list", None)
        if gang_name not in gangs_data:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        gangs_data[gang_name]["points"] += amount
        gangs_data[gang_name].setdefault("recent_actions", []).insert(0, f"+{amount} {reason}")
        firebase_app.put("/gangs/list", gang_name, gangs_data[gang_name])

        await ctx.send(f"✅ تمت إضافة {amount} نقطة لعصابة **{gang_name}** بسبب: **{reason}**")
    except Exception as e:
        await ctx.send(f"⚠️ خطأ أثناء الإضافة: {e}")


# 🔻 أمر خصم النقاط (للمالك فقط)
@bot.command(name="خصم")
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return

    try:
        gangs_data = firebase_app.get("/gangs/list", None)
        if gang_name not in gangs_data:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        gangs_data[gang_name]["points"] -= amount
        gangs_data[gang_name].setdefault("recent_actions", []).insert(0, f"-{amount} {reason}")
        firebase_app.put("/gangs/list", gang_name, gangs_data[gang_name])

        await ctx.send(f"✅ تم خصم {amount} نقطة من عصابة **{gang_name}** بسبب: **{reason}**")
    except Exception as e:
        await ctx.send(f"⚠️ خطأ أثناء الخصم: {e}")


# 🎯 متغيرات المهمة اليومية
current_target = None
mission_active = False


# 🎮 أمر تجربة المهمة (للمالك فقط)
@bot.command(name="تجربة")
async def test_daily(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ما عندك صلاحية.")
        return
    await start_daily_mission(ctx.guild, test_mode=True)


# ⚡ أمر القبض
@bot.command(name="قبض")
async def complete_mission(ctx, gang_name: str):
    global mission_active, current_target
    if not mission_active or not current_target:
        await ctx.send("❌ لا توجد مهمة نشطة حالياً.")
        return

    gangs_data = firebase_app.get("/gangs/list", None)
    if gang_name not in gangs_data:
        await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
        return

    gangs_data[gang_name]["points"] += 30
    gangs_data[gang_name].setdefault("recent_actions", []).insert(0, f"+30 اكمال مهمة القبض اليومية")
    firebase_app.put("/gangs/list", gang_name, gangs_data[gang_name])

    mission_active = False
    await ctx.send(f"🏅 العصابة **{gang_name}** أكملت مهمة اليوم بنجاح! (+30 نقطة)")
    current_target = None


# 🕐 مهمة القبض اليومية
@tasks.loop(minutes=5)
async def daily_task_loop():
    now = discord.utils.utcnow().time()
    if 8 <= now.hour <= 15:  # 11am to 5pm بتوقيت السعودية
        if random.randint(1, 12) == 3:  # احتمال عشوائي
            guilds = bot.guilds
            for guild in guilds:
                await start_daily_mission(guild)
            await asyncio.sleep(3600)


# ⚙️ إنشاء المهمة اليومية
async def start_daily_mission(guild, test_mode=False):
    global mission_active, current_target
    if mission_active:
        return

    police_role = guild.get_role(POLICE_ROLE_ID)
    if not police_role or not police_role.members:
        return

    current_target = random.choice(police_role.members)
    mission_active = True

    channel = guild.get_channel(DAILY_CHANNEL_ID)
    if not channel:
        print("❌ لم يتم العثور على القناة.")
        return

    msg = await channel.send(
        f"🚨 لدينا مهمة قبض {'(تجريبية)' if test_mode else 'جديدة'}!\n"
        f"المطلوب: {current_target.mention}\n"
        f"العصابة التي ستقبض عليه خلال ساعة ستحصل على **30 نقطة!**\n"
        f"{guild.get_role(MENTION_ROLE_ID).mention}"
    )

    # بعد ساعة، فشل المهمة إن لم يتم إنهاؤها
    await asyncio.sleep(3600)
    if mission_active:
        mission_active = False
        await channel.send("⏰ انتهى الوقت! فشلت مهمة اليوم.")
        current_target = None


# 🚀 تشغيل البوت
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("⚠️ لم يتم العثور على توكن البوت. تأكد من وضعه في Secrets باسم DISCORD_BOT_TOKEN.")
    else:
        bot.run(BOT_TOKEN)

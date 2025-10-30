# bot.by مجنون 🇲🇦 — نظام العصابات + المهمات اليومية

import discord
from discord.ext import commands, tasks
import random
import asyncio
import json
import os
from datetime import datetime, timedelta
import pytz
from firebase import firebase
from config import BOT_TOKEN, FIREBASE_URL

# ====== إعداد النوايا ======
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ====== إعداد Firebase ======
firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)

# ====== بيانات ثابتة ======
OWNER_ID = 949947235574095892
POLICE_ROLE_ID = 1342832610878951444
GANGS_ROLE_ID = 1342832658908057681
MISSION_CHANNEL_ID = 1432630812137754715
POINTS_REWARD = 30

# ====== حساب المستوى ======
def calculate_level(points, rewards_levels):
    level = 0
    sorted_rewards = sorted(rewards_levels, key=lambda r: r.get('points', 0))
    for reward in sorted_rewards:
        if points >= reward.get('points', 0):
            level = reward.get('level', 0)
        else:
            break
    return level

# ====== جلب بيانات العصابات ======
def get_live_gang_data():
    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if not gangs_data:
            return [], []

        rewards_data = firebase_app.get('/rewards/levels', None)
        if not rewards_data:
            DATA_FILE = os.path.join(os.path.dirname(__file__), 'gang_data.json')
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                default_data = json.load(f)
            rewards_levels = default_data.get('rewards_levels', [])
        else:
            rewards_levels = rewards_data

        processed_gangs = []
        for gang_name, gang in gangs_data.items():
            gang_info = {
                'name': gang_name,
                'points': gang.get('points', 0)
            }
            gang_info['level'] = calculate_level(gang_info['points'], rewards_levels)
            processed_gangs.append(gang_info)

        sorted_gangs = sorted(processed_gangs, key=lambda g: g['points'], reverse=True)
        return sorted_gangs, rewards_levels

    except Exception as e:
        print(f"⚠️ خطأ أثناء جلب البيانات: {e}")
        return [], []

# ====== تشغيل البوت ======
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم: {bot.user}")
    daily_mission.start()

# ====== أمر عرض النقاط ======
@bot.command(name='نقاط')
async def show_gang_points(ctx):
    gangs_data, _ = get_live_gang_data()
    if not gangs_data:
        await ctx.send("❌ لم أتمكن من جلب البيانات.")
        return

    embed = discord.Embed(title="🏆 ترتيب العصابات (بيانات مباشرة)", color=discord.Color.red())
    for index, gang in enumerate(gangs_data, 1):
        embed.add_field(
            name=f"{index}. {gang['name']}",
            value=f"**النقاط:** {gang['points']}\n**المستوى:** {gang['level']}",
            inline=True
        )
    await ctx.send(embed=embed)

# ====== أوامر النقاط ======
@bot.command(name='اضف')
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return
    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if gang_name not in gangs_data:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return
        gangs_data[gang_name]['points'] += amount
        if 'recent_actions' not in gangs_data[gang_name]:
            gangs_data[gang_name]['recent_actions'] = []
        gangs_data[gang_name]['recent_actions'].insert(0, f"+{amount} {reason}")
        firebase_app.put('/gangs/list', gang_name, gangs_data[gang_name])
        await ctx.send(f"✅ تمت إضافة {amount} نقطة لعصابة {gang_name} بسبب: {reason}")
    except Exception as e:
        await ctx.send(f"⚠️ خطأ: {e}")

@bot.command(name='خصم')
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return
    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if gang_name not in gangs_data:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return
        gangs_data[gang_name]['points'] -= amount
        if 'recent_actions' not in gangs_data[gang_name]:
            gangs_data[gang_name]['recent_actions'] = []
        gangs_data[gang_name]['recent_actions'].insert(0, f"-{amount} {reason}")
        firebase_app.put('/gangs/list', gang_name, gangs_data[gang_name])
        await ctx.send(f"✅ تم خصم {amount} نقطة من عصابة {gang_name} بسبب: {reason}")
    except Exception as e:
        await ctx.send(f"⚠️ خطأ: {e}")

# ====== المهمة اليومية ======
@tasks.loop(minutes=5)
async def daily_mission():
    now = datetime.now(pytz.timezone("Asia/Riyadh"))
    hour = now.hour
    if 11 <= hour < 17:
        if random.randint(1, 12) == 5:  # احتمال 1/12 كل 5 دقائق
            channel = bot.get_channel(MISSION_CHANNEL_ID)
            guild = channel.guild
            police_role = guild.get_role(POLICE_ROLE_ID)
            if not police_role or not police_role.members:
                return
            target = random.choice(police_role.members)
            firebase_app.put('/', 'daily_mission', {
                'target_id': target.id,
                'status': 'active',
                'start_time': str(datetime.now())
            })
            mention = f"<@{target.id}>"
            ping = f"<@&{GANGS_ROLE_ID}>"
            msg = (
                f"🚨 لدينا مهمة قبض لليوم!\n\n"
                f"العصابة التي سوف تقبض على {mention} في غضون ساعة من فتح الرول "
                f"سوف تحصل على {POINTS_REWARD} نقطة 🏆\n\n"
                f"{ping}"
            )
            await channel.send(msg)
            await asyncio.sleep(3600)  # انتظر ساعة
            mission = firebase_app.get('/daily_mission', None)
            if mission and mission.get('status') == 'active':
                firebase_app.put('/', 'daily_mission', {'status': 'failed'})
                await channel.send("⏰ انتهى الوقت، المهمة فشلت! لم يتم القبض على الهدف 😢")

# ====== أمر القبض ======
@bot.command(name='قبض')
async def arrest(ctx, gang_name: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return
    mission = firebase_app.get('/daily_mission', None)
    if not mission or mission.get('status') != 'active':
        await ctx.send("❌ لا توجد مهمة حالياً.")
        return
    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if gang_name not in gangs_data:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return
        gangs_data[gang_name]['points'] += POINTS_REWARD
        if 'recent_actions' not in gangs_data[gang_name]:
            gangs_data[gang_name]['recent_actions'] = []
        gangs_data[gang_name]['recent_actions'].insert(0, f"+{POINTS_REWARD} اكمال مهمة يومية")
        firebase_app.put('/gangs/list', gang_name, gangs_data[gang_name])
        firebase_app.put('/', 'daily_mission', {'status': 'completed'})
        await ctx.send(f"✅ تمت المهمة بنجاح! العصابة **{gang_name}** حصلت على +{POINTS_REWARD} نقاط 🏆")
    except Exception as e:
        await ctx.send(f"⚠️ خطأ: {e}")

# ====== أمر تجربة ======
@bot.command(name='تجربة')
async def test_mission(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ ليس لديك صلاحية.")
        return
    channel = bot.get_channel(MISSION_CHANNEL_ID)
    guild = channel.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    if not police_role or not police_role.members:
        await ctx.send("❌ لا يوجد أعضاء برتبة الشرطة.")
        return
    target = random.choice(police_role.members)
    mention = f"<@{target.id}>"
    ping = f"<@&{GANGS_ROLE_ID}>"
    msg = (
        f"🧪 تجربة مهمة قبض!\n\n"
        f"العصابة التي سوف تقبض على {mention} في غضون ساعة من فتح الرول "
        f"سوف تحصل على {POINTS_REWARD} نقطة 🏆\n\n"
        f"{ping}"
    )
    await channel.send(msg)
    await ctx.send("✅ تم إرسال تجربة المهمة بنجاح (لا تؤثر على البيانات).")

# ====== تشغيل البوت ======
if __name__ == "__main__":
    bot.run(BOT_TOKEN)

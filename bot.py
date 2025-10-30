import discord
from discord.ext import commands
import json
import os
from firebase import firebase
from config import BOT_TOKEN, FIREBASE_URL  # استيراد بيانات Firebase من config.py

# إعداد النوايا (Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# تعريف البوت
bot = commands.Bot(command_prefix='!', intents=intents)

# تهيئة اتصال Firebase
firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)

# دالة لحساب المستوى
def calculate_level(points, rewards_levels):
    """تحسب مستوى العصابة بناءً على النقاط."""
    level = 0
    sorted_rewards = sorted(rewards_levels, key=lambda r: r.get('points', 0))
    for reward in sorted_rewards:
        if points >= reward.get('points', 0):
            level = reward.get('level', 0)
        else:
            break
    return level


# دالة لجلب بيانات العصابات من Firebase
def get_live_gang_data():
    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if not gangs_data:
            print("⚠️ لا توجد بيانات عصابات في Firebase.")
            return [], []

        rewards_data = firebase_app.get('/rewards/levels', None)
        if not rewards_data:
            print("⚠️ لا توجد بيانات مستويات في Firebase، سيتم استخدام الافتراضية.")
            DATA_FILE = os.path.join(os.path.dirname(__file__), 'gang_data.json')
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                default_data = json.load(f)
            rewards_levels = default_data.get('rewards_levels', [])
        else:
            rewards_levels = rewards_data

        processed_gangs = []
        for gang in gangs_data:
            if isinstance(gang, dict):
                gang_info = {
                    'name': gang.get('name', 'عصابة غير معروفة'),
                    'points': gang.get('points', 0)
                }
                gang_info['level'] = calculate_level(gang_info['points'], rewards_levels)
                processed_gangs.append(gang_info)

        sorted_gangs = sorted(processed_gangs, key=lambda g: g.get('points', 0), reverse=True)
        return sorted_gangs, rewards_levels

    except Exception as e:
        print(f"⚠️ خطأ أثناء جلب البيانات: {e}")
        return [], []


# عند تشغيل البوت
@bot.event
async def on_ready():
    print(f"✅ البوت جاهز وتم تسجيل الدخول باسم: {bot.user}")
    print("--------------------------------------------------")


# أمر عرض النقاط
@bot.command(name='نقاط')
async def show_gang_points(ctx):
    await ctx.send("📊 جاري جلب بيانات العصابات من Firebase...")
    gangs_data, _ = get_live_gang_data()

    if not gangs_data:
        await ctx.send("❌ لم أتمكن من جلب البيانات. تأكد من إعداد Firebase بشكل صحيح.")
        return

    embed = discord.Embed(
        title="🏆 ترتيب العصابات (بيانات مباشرة)",
        description="قائمة العصابات مع النقاط والمستويات الحالية:",
        color=discord.Color.gold()
    )

    for index, gang in enumerate(gangs_data, 1):
        embed.add_field(
            name=f"{index}. {gang['name']}",
            value=f"**النقاط:** {gang['points']}\n**المستوى:** {gang['level']}",
            inline=True
        )

    embed.set_footer(text=f"آخر تحديث: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    await ctx.send(embed=embed)


# أمر إضافة نقاط
@bot.command(name='اضف')
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != 949947235574095892:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    try:
        firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)
        gangs_data = firebase_app.get('/gangs/list', None)

        if gang_name not in gangs_data:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        gangs_data[gang_name]['points'] += amount

        if 'recent_actions' not in gangs_data[gang_name]:
            gangs_data[gang_name]['recent_actions'] = []
        gangs_data[gang_name]['recent_actions'].insert(0, f"+{amount} {reason}")

        firebase_app.put('/gangs/list', gang_name, gangs_data[gang_name])

        await ctx.send(f"✅ تمت إضافة **{amount}** نقطة لعصابة **{gang_name}** بسبب: **{reason}**")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الإضافة: {e}")


# أمر خصم النقاط
@bot.command(name='خصم')
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != 949947235574095892:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    try:
        firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)
        gangs_data = firebase_app.get('/gangs/list', None)

        if gang_name not in gangs_data:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        gangs_data[gang_name]['points'] -= amount

        if 'recent_actions' not in gangs_data[gang_name]:
            gangs_data[gang_name]['recent_actions'] = []
        gangs_data[gang_name]['recent_actions'].insert(0, f"-{amount} {reason}")

        firebase_app.put('/gangs/list', gang_name, gangs_data[gang_name])

        await ctx.send(f"✅ تم خصم **{amount}** نقطة من عصابة **{gang_name}** بسبب: **{reason}**")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الخصم: {e}")


# تشغيل البوت
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ خطأ: يرجى تعديل ملف config.py ووضع رمز البوت الخاص بك.")
    else:
        bot.run(BOT_TOKEN)

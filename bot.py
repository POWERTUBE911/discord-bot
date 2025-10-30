import discord
from discord.ext import commands
import json
import os
from firebase import firebase
from config import BOT_TOKEN, FIREBASE_URL  # بيانات Firebase من config.py

# إعداد intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# تعريف البوت
bot = commands.Bot(command_prefix='!', intents=intents)

# الاتصال بفايربيس
firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)


# دالة حساب المستوى
def calculate_level(points, rewards_levels):
    level = 0
    sorted_rewards = sorted(rewards_levels, key=lambda r: r.get('points', 0))
    for reward in sorted_rewards:
        if points >= reward.get('points', 0):
            level = reward.get('level', 0)
        else:
            break
    return level


# جلب بيانات العصابات من فايربيس
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


# أمر إضافة النقاط
@bot.command(name='اضف')
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != 949947235574095892:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if not gangs_data:
            await ctx.send("⚠️ لا توجد بيانات عصابات في Firebase.")
            return

        # البحث عن العصابة بالاسم
        gang_found = None
        for gang in gangs_data:
            if gang.get("name") == gang_name:
                gang_found = gang
                break

        if not gang_found:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        # تحديث النقاط
        gang_found['points'] = gang_found.get('points', 0) + amount

        # تسجيل السبب داخل pointsSources
        if 'pointsSources' not in gang_found:
            gang_found['pointsSources'] = []
        gang_found['pointsSources'].insert(0, f"+{amount} - {reason}")

        # حفظ التغيير في Firebase
        index = gangs_data.index(gang_found)
        firebase_app.put('/gangs/list', index, gang_found)

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
        gangs_data = firebase_app.get('/gangs/list', None)
        if not gangs_data:
            await ctx.send("⚠️ لا توجد بيانات عصابات في Firebase.")
            return

        # البحث عن العصابة بالاسم
        gang_found = None
        for gang in gangs_data:
            if gang.get("name") == gang_name:
                gang_found = gang
                break

        if not gang_found:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        # تحديث النقاط
        gang_found['points'] = max(0, gang_found.get('points', 0) - amount)

        # تسجيل السبب داخل pointsSources
        if 'pointsSources' not in gang_found:
            gang_found['pointsSources'] = []
        gang_found['pointsSources'].insert(0, f"-{amount} - {reason}")

        # حفظ التغيير في Firebase
        index = gangs_data.index(gang_found)
        firebase_app.put('/gangs/list', index, gang_found)

        await ctx.send(f"✅ تم خصم **{amount}** نقطة من عصابة **{gang_name}** بسبب: **{reason}**")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الخصم: {e}")


# تشغيل البوت
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ خطأ: يرجى تعديل ملف config.py ووضع رمز البوت الخاص بك.")
    else:
        bot.run(BOT_TOKEN)

import discord
from discord.ext import commands
import json
import os
from firebase import firebase
from config import BOT_TOKEN, FIREBASE_URL  # استيراد بيانات Firebase من config.py

# إعداد النوايا
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# تهيئة Firebase
firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)

def calculate_level(points, rewards_levels):
    level = 0
    sorted_rewards = sorted(rewards_levels, key=lambda r: r.get('points', 0))
    for reward in sorted_rewards:
        if points >= reward.get('points', 0):
            level = reward.get('level', 0)
        else:
            break
    return level

def get_live_gang_data():
    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if not gangs_data:
            print("⚠️ لا توجد بيانات عصابات في Firebase.")
            return [], []

        rewards_data = firebase_app.get('/rewards/levels', None)
        if not rewards_data:
            print("⚠️ لا توجد بيانات مستويات، سيتم استخدام الافتراضية.")
            DATA_FILE = os.path.join(os.path.dirname(__file__), 'gang_data.json')
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                default_data = json.load(f)
            rewards_levels = default_data.get('rewards_levels', [])
        else:
            rewards_levels = rewards_data

        processed = []
        for gang in gangs_data:
            if isinstance(gang, dict):
                gang_info = {
                    'name': gang.get('name', 'غير معروفة'),
                    'points': gang.get('points', 0)
                }
                gang_info['level'] = calculate_level(gang_info['points'], rewards_levels)
                processed.append(gang_info)

        sorted_gangs = sorted(processed, key=lambda g: g.get('points', 0), reverse=True)
        return sorted_gangs, rewards_levels

    except Exception as e:
        print(f"⚠️ خطأ أثناء جلب البيانات: {e}")
        return [], []


@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول باسم: {bot.user}")


@bot.command(name='نقاط')
async def show_gang_points(ctx):
    await ctx.send("📊 جاري جلب بيانات العصابات...")
    gangs, _ = get_live_gang_data()

    if not gangs:
        await ctx.send("❌ لم أتمكن من جلب البيانات.")
        return

    embed = discord.Embed(title="🏆 ترتيب العصابات (مباشر)", color=discord.Color.gold())
    for i, gang in enumerate(gangs, 1):
        embed.add_field(
            name=f"{i}. {gang['name']}",
            value=f"**النقاط:** {gang['points']}\n**المستوى:** {gang['level']}",
            inline=True
        )
    await ctx.send(embed=embed)


@bot.command(name='اضف')
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != 949947235574095892:
        await ctx.send("❌ لا تملك صلاحية استخدام هذا الأمر.")
        return

    try:
        gangs_data = firebase_app.get('/gangs/list', None)

        found = False
        for index, gang in enumerate(gangs_data):
            if gang.get('name') == gang_name:
                gangs_data[index]['points'] += amount

                if 'recent_actions' not in gangs_data[index]:
                    gangs_data[index]['recent_actions'] = []
                gangs_data[index]['recent_actions'].insert(0, f"+{amount} {reason}")

                firebase_app.put('/gangs', 'list', gangs_data)
                found = True
                break

        if found:
            await ctx.send(f"✅ تمت إضافة **{amount}** نقطة لعصابة **{gang_name}** بسبب: **{reason}**")
        else:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الإضافة: {e}")


@bot.command(name='خصم')
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    if ctx.author.id != 949947235574095892:
        await ctx.send("❌ لا تملك صلاحية استخدام هذا الأمر.")
        return

    try:
        gangs_data = firebase_app.get('/gangs/list', None)

        found = False
        for index, gang in enumerate(gangs_data):
            if gang.get('name') == gang_name:
                gangs_data[index]['points'] -= amount

                if 'recent_actions' not in gangs_data[index]:
                    gangs_data[index]['recent_actions'] = []
                gangs_data[index]['recent_actions'].insert(0, f"-{amount} {reason}")

                firebase_app.put('/gangs', 'list', gangs_data)
                found = True
                break

        if found:
            await ctx.send(f"✅ تم خصم **{amount}** نقطة من عصابة **{gang_name}** بسبب: **{reason}**")
        else:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الخصم: {e}")


if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ عدّل config.py وضع رمز البوت الصحيح.")
    else:
        bot.run(BOT_TOKEN)

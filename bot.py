# bot.py
import discord
from discord.ext import commands
import json
import os
from firebase import firebase
from config import BOT_TOKEN, FIREBASE_URL  # تأكد من وجود هذا الملف وقيمه

# إعداد النوايا (Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# تعريف البوت
bot = commands.Bot(command_prefix='!', intents=intents)

# تهيئة اتصال Firebase
firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)

# مساعدة: العثور على عصابة حسب الاسم (يدعم list أو dict)
def find_gang_by_name(gangs_data, name):
    """
    يعيد (gang, key, index) حيث:
    - gang: الكائن نفسه (dict)
    - key: المفتاح الذي يجب استخدامه في firebase_app.put (قد يكون index كـ str أو المفتاح الأصلي)
    - index: موقعه في القائمة إذا كان قائمة (int) أو None
    يرجع (None, None, None) لو لم يُعثر.
    """
    if gangs_data is None:
        return None, None, None

    # لو كانت القائمة عبارة عن dict مفاتيح نصية (مثال: { "0": {...}, "1": {...} })
    if isinstance(gangs_data, dict):
        # جرب البحث بحسب قيمة name داخل كل عنصر
        for k, v in gangs_data.items():
            if isinstance(v, dict) and v.get('name') == name:
                return v, k, None
        # بعض مشاريع Firebase ترجع قائمة كـ dict بالأرقام كسلاسل
        # حاول أيضاً البحث بالمفتاح المطابق للاسم مباشرة (نادر)
        if name in gangs_data:
            return gangs_data[name], name, None
        return None, None, None

    # لو كانت قائمة (list)
    if isinstance(gangs_data, list):
        for idx, item in enumerate(gangs_data):
            if isinstance(item, dict) and item.get('name') == name:
                # في هذه الحالة المفتاح في Firebase هو رقم العنصر كسلسلة
                return item, str(idx), idx
        return None, None, None

    # حالات أخرى
    return None, None, None

# دالة لحساب المستوى من rewards_levels
def calculate_level(points, rewards_levels):
    level = 0
    try:
        sorted_rewards = sorted(rewards_levels, key=lambda r: r.get('points', 0))
    except Exception:
        sorted_rewards = []
    for reward in sorted_rewards:
        if points >= reward.get('points', 0):
            level = reward.get('level', 0)
        else:
            break
    return level

# جلب ومعالجة بيانات العصابات الحية
def get_live_gang_data():
    try:
        gangs_data = firebase_app.get('/gangs/list', None)
        if not gangs_data:
            print("⚠️ لا توجد بيانات عصابات في Firebase.")
            return [], []

        rewards_data = firebase_app.get('/rewards/levels', None)
        if not rewards_data:
            print("⚠️ لا توجد بيانات مستويات في Firebase، سيتم استخدام الملف المحلي (إن وُجد).")
            DATA_FILE = os.path.join(os.path.dirname(__file__), 'gang_data.json')
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    default_data = json.load(f)
                rewards_levels = default_data.get('rewards_levels', [])
            except Exception:
                rewards_levels = []
        else:
            rewards_levels = rewards_data

        processed_gangs = []

        # قد تكون gangs_data قائمة أو dict
        if isinstance(gangs_data, dict):
            # تحويل dict => list من القيم إذا لزم
            for k, gang in gangs_data.items():
                if isinstance(gang, dict):
                    info = {
                        'key': k,
                        'name': gang.get('name', 'عصابة غير معروفة'),
                        'points': gang.get('points', 0)
                    }
                    info['level'] = calculate_level(info['points'], rewards_levels)
                    processed_gangs.append(info)
        elif isinstance(gangs_data, list):
            for idx, gang in enumerate(gangs_data):
                if isinstance(gang, dict):
                    info = {
                        'key': str(idx),
                        'name': gang.get('name', 'عصابة غير معروفة'),
                        'points': gang.get('points', 0)
                    }
                    info['level'] = calculate_level(info['points'], rewards_levels)
                    processed_gangs.append(info)
        else:
            # نوع غير متوقع
            print("⚠️ نوع بيانات العصابات غير متوقع:", type(gangs_data))
            return [], rewards_levels

        # ترتيب تنازلي حسب النقاط
        sorted_gangs = sorted(processed_gangs, key=lambda g: g.get('points', 0), reverse=True)
        return sorted_gangs, rewards_levels

    except Exception as e:
        print(f"⚠️ خطأ أثناء جلب البيانات من Firebase: {e}")
        return [], []

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
        await ctx.send("❌ لم أتمكن من جلب بيانات العصابات. تحقق من FIREBASE_URL و صلاحيات القراءة في Firebase.")
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
            inline=False
        )

    embed.set_footer(text=f"آخر تحديث: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    await ctx.send(embed=embed)

# أمر إضافة نقاط
@bot.command(name='اضف')
async def add_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    # تحقق أن الأمر من المرسل المصرّح له (استخدم ID اللي أعطيته)
    AUTHORIZED_ID = 949947235574095892
    if ctx.author.id != AUTHORIZED_ID:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    try:
        gangs_data_raw = firebase_app.get('/gangs/list', None)
        gang_found, gang_key, gang_index = find_gang_by_name(gangs_data_raw, gang_name)

        if not gang_found:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        # تأكد من وجود حقل points وتهيئته
        if 'points' not in gang_found or not isinstance(gang_found.get('points'), (int, float)):
            gang_found['points'] = 0

        # تحديث النقاط
        gang_found['points'] = int(gang_found['points']) + int(amount)

        # سجّل السبب في recent_actions (نص) و pointsSources (كائن)
        if 'recent_actions' not in gang_found or not isinstance(gang_found['recent_actions'], list):
            gang_found['recent_actions'] = []
        gang_found['recent_actions'].insert(0, f"+{amount} {reason}")

        # pointsSources يجب أن يكون قائمة من كائنات {points, reason}
        if 'pointsSources' not in gang_found or not isinstance(gang_found['pointsSources'], list):
            gang_found['pointsSources'] = []
        gang_found['pointsSources'].insert(0, {
            'points': int(amount),
            'reason': reason
        })

        # اكتب التعديل في Firebase
        # المسار: /gangs/list/{key}
        firebase_app.put('/gangs/list', gang_key, gang_found)

        await ctx.send(f"✅ تمت إضافة **{amount}** نقطة لعصابة **{gang_name}** بسبب: **{reason}**")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الإضافة: {e}")

# أمر خصم النقاط
@bot.command(name='خصم')
async def remove_points(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    AUTHORIZED_ID = 949947235574095892
    if ctx.author.id != AUTHORIZED_ID:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    try:
        gangs_data_raw = firebase_app.get('/gangs/list', None)
        gang_found, gang_key, gang_index = find_gang_by_name(gangs_data_raw, gang_name)

        if not gang_found:
            await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")
            return

        if 'points' not in gang_found or not isinstance(gang_found.get('points'), (int, float)):
            gang_found['points'] = 0

        # خصم النقاط
        gang_found['points'] = int(gang_found['points']) - int(amount)

        # سجّل السبب
        if 'recent_actions' not in gang_found or not isinstance(gang_found['recent_actions'], list):
            gang_found['recent_actions'] = []
        gang_found['recent_actions'].insert(0, f"-{amount} {reason}")

        if 'pointsSources' not in gang_found or not isinstance(gang_found['pointsSources'], list):
            gang_found['pointsSources'] = []
        gang_found['pointsSources'].insert(0, {
            'points': -int(amount),
            'reason': reason
        })

        # اكتب التعديل في Firebase
        firebase_app.put('/gangs/list', gang_key, gang_found)

        await ctx.send(f"✅ تم خصم **{amount}** نقطة من عصابة **{gang_name}** بسبب: **{reason}**")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الخصم: {e}")

# تشغيل البوت
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ خطأ: يرجى تعديل ملف config.py ووضع رمز البوت الخاص بك.")
    else:
        bot.run(BOT_TOKEN)

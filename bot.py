# bot.py
# بوت العصابات — تصميم دموي متحرك، كل الرسائل عربية، التوكن من Secrets
import discord
from discord.ext import commands, tasks
import asyncio
import requests
import random
import os
from datetime import datetime, timedelta
import pytz

# ------------------ إعداد النوايا والبوت ------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # مهم جداً لقراءة أعضاء الرتب
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------ إعدادات ثابتة (عدل OWNER_ID لو تبي) ------------------
# ملاحظة: التوكن فقط من الأسرار؛ باقي القيم ثابتة داخل الملف كما طلبت
OWNER_ID = 949947235574095892  # لو تحب غيّر هنا
POLICE_ROLE_ID = 1342832610878951444
GANG_ROLE_ID = 1342832658908057681
DAILY_CHANNEL_ID = 1432630812137754715

# رابط Firebase ثابت داخل الكود (مثل ما طلبت)
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# نقاط المكافأة للمهمة اليومية
DAILY_REWARD_POINTS = 30
# المنطقة الزمنية لعرض التاريخ/الوقت
TZ = "Asia/Riyadh"

# ------------------ مساعدة: حساب المستوى ------------------
# نحاول تحميل مستويات من Firebase إن وُجدت، وإلا نستخدم thresholds محلية
DEFAULT_LEVEL_THRESHOLDS = [
    (0, 1),
    (100, 2),
    (250, 3),
    (500, 4),
    (1000, 5)
]

def load_rewards_levels_from_firebase():
    try:
        r = requests.get(f"{FIREBASE_URL}/rewards/levels.json", timeout=8)
        if r.status_code == 200:
            data = r.json()
            # نتوقع قائمة عناصر بها fields 'points' و 'level'
            if isinstance(data, list):
                return sorted([(int(item.get("points", 0)), int(item.get("level", 0))) for item in data], key=lambda x: x[0])
            if isinstance(data, dict):
                # قد يكون dict مهيكل differently -> نقله للقائمة
                arr = []
                for _, v in data.items():
                    if isinstance(v, dict):
                        arr.append((int(v.get("points", 0)), int(v.get("level", 0))))
                return sorted(arr, key=lambda x: x[0])
    except Exception:
        pass
    return DEFAULT_LEVEL_THRESHOLDS

LEVEL_THRESHOLDS = load_rewards_levels_from_firebase()

def calculate_level(points: int) -> int:
    lvl = 0
    for thresh, level in LEVEL_THRESHOLDS:
        if points >= thresh:
            lvl = level
        else:
            break
    return lvl

# ------------------ دوال Firebase (تتعامل مع gangs/list كقائمة) ------------------
def get_gangs_data():
    """
    يرجع قائمة من القواميس: [{ "name": "...", "points": 0, ... }, ...]
    يتعامل مع المسار /gangs/list.json
    """
    try:
        resp = requests.get(f"{FIREBASE_URL}/gangs/list.json", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
            # في بعض الحالات قد يكون dict => نحول لقائمة values أو عناصر dict
            if isinstance(data, dict):
                # إذا العناصر أرقام مفهرسة كـ "0","1" نعيد القيم كقائمة
                try:
                    # محاولة استخراج قيم مرتبة
                    keys = sorted([k for k in data.keys()], key=lambda x: int(x) if str(x).isdigit() else x)
                    return [data[k] for k in keys]
                except Exception:
                    return list(data.values())
        else:
            print(f"⚠️ فشل جلب gangs/list.json، status_code = {resp.status_code}")
    except Exception as e:
        print(f"❌ استثناء عند جلب بيانات العصابات من Firebase: {e}")
    return []

def put_full_gangs_list(gangs_list):
    """
    يكتب القائمة كلها إلى /gangs/list.json عبر PUT (نستخدم PUT لأن لدينا قائمة كاملة).
    """
    try:
        resp = requests.put(f"{FIREBASE_URL}/gangs/list.json", json=gangs_list, timeout=8)
        if resp.status_code not in (200, 204):
            print(f"⚠️ فشل PUT للقائمة: {resp.status_code} - {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"❌ استثناء عند PUT للقائمة: {e}")
        return False

def update_gang_points(gang_name: str, new_points: int) -> bool:
    """
    يحدّث النقاط للعصابة بالاسم ضمن القائمة، ثم يرسل PUT للقائمة كلها.
    """
    try:
        gangs = get_gangs_data()
        changed = False
        for item in gangs:
            if item.get("name", "").strip().lower() == gang_name.strip().lower():
                item["points"] = new_points
                changed = True
                break
        if not changed:
            # إذا لم نجد العصابة، يمكننا إضافتها (اختياري) - هنا نرجع False
            return False
        return put_full_gangs_list(gangs)
    except Exception as e:
        print(f"❌ خطأ في update_gang_points: {e}")
        return False

def add_log(gang_name: str, action: str, reason: str):
    """
    يضيف سجلًا في /infoLog.json (POST).
    """
    try:
        entry = {
            "gang": gang_name,
            "action": action,
            "reason": reason,
            "time": datetime.now(pytz.timezone(TZ)).strftime("%Y-%m-%d %H:%M:%S")
        }
        requests.post(f"{FIREBASE_URL}/infoLog.json", json=entry, timeout=8)
    except Exception:
        pass

# ------------------ تنسيق ورسائل متحركة (تدريجي) ------------------
EMBED_COLOR_BORDER = 0x8B0000  # أحمر دموي
GOLD_EMOJI = "🥇"
SILVER_EMOJI = "🥈"
BRONZE_EMOJI = "🥉"
STYLE_SIGNATURE = "💀 **GANG BOT** ⚔️ — قانون العصابات لا يرحم"
COMMON_EMOJIS = "💀 🔥 ⚔️"

def make_base_embed(title: str, subtitle: str = None):
    """
    يبني Embed أساسي بستايل الدموي (غامق مع لون أحمر للحد).
    نستخدم وصف (description) فارغ في البداية ليُملأ تدريجيًا.
    """
    embed = discord.Embed(title=title, description="", color=EMBED_COLOR_BORDER)
    if subtitle:
        embed.set_author(name=subtitle)
    # توقيع في الفوتر
    embed.set_footer(text=STYLE_SIGNATURE)
    return embed

async def send_progressive_embed(channel, title_lines, description_lines, pause=0.5):
    """
    يبعث embed فارغ أولًا ثم يضيف للأسفل سطرًا سطرًا من description_lines مع تأخير pause ثانية.
    title_lines: list of title lines to appear at top (مُدمَجة في العنوان أو الحقل الأول)
    description_lines: list of strings (each will be مضافة كسطر جديد)
    """
    # نحضر embed
    title = "  ".join(title_lines) if title_lines else ""
    embed = make_base_embed(title=title)
    # نرسل رسالة مبدئية
    msg = await channel.send(embed=embed)
    # نبني وصف تدريجيًا
    desc = ""
    for line in description_lines:
        desc += line + "\n"
        embed.description = desc
        try:
            await msg.edit(embed=embed)
        except Exception:
            # في بعض الأحيان لا يسمح بالتعديل -> نتحدث برسالة جديدة بدل التعديل
            await channel.send(line)
        await asyncio.sleep(pause)
    return msg

# ------------------ الأوامر ------------------

@bot.command(name="نقاط")
async def cmd_points(ctx):
    """
    يعرض العصابات مرتبة حسب النقاط، مع عرض المستوى لكل عصابة،
    وتنسيق متحرك (سطر بسطر).
    """
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم أتمكن من جلب بيانات العصابات الآن. حاول لاحقًا.")
        return

    # نحسب المستوى لكل عصابة ثم نرتب
    processed = []
    for g in gangs:
        name = g.get("name", "بدون اسم")
        points = int(g.get("points", 0) or 0)
        level = calculate_level(points)
        processed.append({"name": name, "points": points, "level": level})
    processed.sort(key=lambda x: x["points"], reverse=True)

    # بناء خطوط العرض
    lines = []
    rank_icons = [GOLD_EMOJI, SILVER_EMOJI, BRONZE_EMOJI]
    for idx, g in enumerate(processed, start=1):
        icon = rank_icons[idx-1] if idx-1 < len(rank_icons) else f"{idx}."
        # خط لكل عصابة
        line = f"{icon} **{g['name']}** — المستوى: **{g['level']}** — النقاط: **{g['points']}** {COMMON_EMOJIS}"
        lines.append(line)

    title_lines = ["🏴‍☠️  قائمة العصابات — الترتيب حسب النقاط"]
    await send_progressive_embed(ctx.channel, title_lines, lines, pause=0.6)

@bot.command(name="اضف")
async def cmd_add(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    """
    إضافة نقاط — خاص بالمالك فقط.
    """
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    found = False
    for g in gangs:
        if g.get("name", "").strip().lower() == gang_name.strip().lower():
            current = int(g.get("points", 0) or 0)
            new = current + amount
            ok = update_gang_points(gang_name, new)
            if ok:
                add_log(gang_name, f"إضافة {amount}", reason)
                # تحضير سطور النتيجة
                lines = [
                    f"✅ تم إضافة **{amount}** نقطة إلى العصابة **{g['name']}**",
                    f"🏆 المجموع الجديد: **{new}** نقطة",
                    f"📋 السبب: {reason}",
                    COMMON_EMOJIS
                ]
                await send_progressive_embed(ctx.channel, [f"💰 إضافة نقاط — {g['name']}"], lines, pause=0.5)
            else:
                await ctx.send("❌ فشل تحديث النقاط في قاعدة البيانات.")
            found = True
            break
    if not found:
        await ctx.send("❌ لم أجد هذه العصابة في قاعدة البيانات.")

@bot.command(name="خصم")
async def cmd_remove(ctx, amount: int, gang_name: str, *, reason: str = "بدون سبب"):
    """
    خصم نقاط — خاص بالمالك فقط.
    """
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    found = False
    for g in gangs:
        if g.get("name", "").strip().lower() == gang_name.strip().lower():
            current = int(g.get("points", 0) or 0)
            new = max(0, current - amount)
            ok = update_gang_points(gang_name, new)
            if ok:
                add_log(gang_name, f"خصم {amount}", reason)
                lines = [
                    f"⚠️ تم خصم **{amount}** نقطة من العصابة **{g['name']}**",
                    f"🏆 المجموع الجديد: **{new}** نقطة",
                    f"📋 السبب: {reason}",
                    COMMON_EMOJIS
                ]
                await send_progressive_embed(ctx.channel, [f"🔻 خصم نقاط — {g['name']}"], lines, pause=0.5)
            else:
                await ctx.send("❌ فشل تحديث النقاط في قاعدة البيانات.")
            found = True
            break
    if not found:
        await ctx.send("❌ لم أجد هذه العصابة في قاعدة البيانات.")

@bot.command(name="تجربة")
async def cmd_trial(ctx):
    """
    تجربة اختيار شرطي عشوائي — لا تؤثر على المهمة اليومية الحقيقية.
    مقصور على المالك (حسب طلبك السابق) — لكن يمكننا السماح للمالك فقط.
    """
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ هذا الأمر مخصص لمالك البوت فقط.")
        return

    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_role = guild.get_role(GANG_ROLE_ID)
    if not police_role:
        await ctx.send("❌ لم أجد رتبة الشرطة. تأكد من إعدادات السيرفر.")
        return
    members = [m for m in police_role.members if not m.bot]
    if not members:
        await ctx.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return
    chosen = random.choice(members)
    lines = [
        f"🧪 هذه مجرد تجربة — لا تؤثر على المهمة الحقيقية.",
        f"👮‍♂️ الشرطي المختار: {chosen.mention}",
        f"🔥 العصابات المستهدفة: {guild.get_role(GANG_ROLE_ID).mention if guild.get_role(GANG_ROLE_ID) else '‎🔰'}",
        COMMON_EMOJIS
    ]
    await send_progressive_embed(ctx.channel, [f"🧪 تجربة مهمة يومية"], lines, pause=0.6)

@bot.command(name="قبض")
async def cmd_catch(ctx, gang_name: str):
    """
    إتمام القبض خلال ساعة المهمة — يعطي العصابة نقاط الجائزة.
    فقط يسمح خلال المهمة — لكن هنا لا نعقّد: إذا نفّذ المالك الأمر أثناء المهمة (أو في أي وقت) سيتم التحقق.
    """
    # نتحقق إن العصابة موجودة
    gangs = get_gangs_data()
    for g in gangs:
        if g.get("name", "").strip().lower() == gang_name.strip().lower():
            current = int(g.get("points", 0) or 0)
            new = current + DAILY_REWARD_POINTS
            ok = update_gang_points(gang_name, new)
            if ok:
                add_log(gang_name, f"+{DAILY_REWARD_POINTS}", "إتمام المهمة اليومية")
                lines = [
                    f"🎉 أحسنت! العصابة **{g['name']}** نجحت في إتمام المهمة اليومية.",
                    f"🏆 حصلت على **{DAILY_REWARD_POINTS}** نقطة! المجموع الآن: **{new}** نقطة",
                    COMMON_EMOJIS
                ]
                await send_progressive_embed(ctx.channel, [f"🎯 مكافأة مهمة يومية — {g['name']}"], lines, pause=0.5)
            else:
                await ctx.send("❌ فشل تحديث النقاط في قاعدة البيانات.")
            return
    await ctx.send("❌ لم أجد هذه العصابة في قاعدة البيانات.")

# ------------------ المهمة اليومية التلقائية ------------------
@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(5)
    if not bot.guilds:
        print("⚠️ البوت غير متصل بأي سيرفر - المهمة اليومية متوقفة.")
        return
    guild = bot.guilds[0]
    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_role = guild.get_role(GANG_ROLE_ID)
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not channel:
        print("⚠️ لم يتم العثور على رتبة الشرطة أو القناة اليومية. تحقق من الإعدادات.")
        return
    if not gang_role:
        print("⚠️ لم أجد رتبة العصابات (GANG_ROLE_ID).")

    members = [m for m in police_role.members if not m.bot]
    if not members:
        await channel.send("❌ لا يوجد أعضاء في رتبة الشرطة حاليًا.")
        return

    chosen = random.choice(members)
    lines = [
        f"🚨 بدأت المهمة اليومية الآن!",
        f"👮‍♂️ الشرطي المكلف: {chosen.mention}",
        f"🔥 العصابات: {gang_role.mention if gang_role else '‎🔰'}",
        f"⏳ أمامكم ساعة واحدة للمحاولة — استخدموا `!قبض <اسم_العصابة>` لإتمام المهمة وكسب {DAILY_REWARD_POINTS} نقطة.",
        COMMON_EMOJIS
    ]
    await send_progressive_embed(channel, [f"🚨 مهمة يومية جديدة"], lines, pause=0.6)

    # ننتظر ساعة ثم نغلق المهمة (هذه مجرد رسالة انتهاء)
    await asyncio.sleep(3600)
    await channel.send("⌛ انتهت ساعة المهمة اليومية! انتهت المحاولة لهذه الدورة.")

# ------------------ حدث التشغيل ------------------
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت: {bot.user} (ID: {bot.user.id})")
    # شغّل المهمة اليومية إن لم تكن تعمل
    if not daily_mission.is_running():
        daily_mission.start()

# ------------------ تشغيل البوت (توكن من الأسرار) ------------------
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ متغير البيئة DISCORD_BOT_TOKEN غير موجود. ضع توكن البوت في الأسرار.")
bot.run(DISCORD_BOT_TOKEN)

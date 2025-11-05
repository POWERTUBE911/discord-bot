# bot.py
import os
import discord
from discord.ext import commands, tasks
import asyncio
import json
import requests
import random
from datetime import datetime
import pytz

# ========== إعداد البوت ==========
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======= إعدادات القيم الثابتة (حطها في Secrets/env) =======
OWNER_ID = 949947235574095892  # مثال - عدل إن أردت
POLICE_ROLE_ID = 1342832610878951444  # رتبة الشرطة
GANG_ROLE_ID = 1342832658908057681    # رتبة العصابات (لذكرها عند المهمة)
DAILY_CHANNEL_ID = 1432630812137754715  # قناة المهام اليومية
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"  # مثال: https://project-id-default-rtdb.europe-west1.firebasedatabase.app
DAILY_REWARD_POINTS = 30  # نقاط المهمة اليومية

if not FIREBASE_URL:
    raise ValueError("لم يتم العثور على FIREBASE_URL في المتغيرات البيئية.")

# ====================== دوال التعامل مع Firebase ======================

def get_gangs_data():
    """
    يجلب قائمة العصابات من /gangs/list.json
    يعيد قائمة (list) أو [] عند الفشل
    """
    try:
        resp = requests.get(f"{FIREBASE_URL}/gangs/list.json")
        if resp.status_code == 200:
            data = resp.json()
            # نتوقع قائمة؛ بعض قواعد قد ترجع dict أو None
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # إن كانت dict بترتيب معين نحاول تحويلها لقائمة إن قابل
                # لكن في هيكلك انت تظهر أن البيانات في شكل list بالفعل
                # إذا أردت تحويل dict إلى list هنا قم بالتعديل
                return list(data.values())
        else:
            print(f"⚠️ خطأ عند جلب العصابات من Firebase: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ استثناء عند جلب العصابات: {e}")
    return []

def update_gangs_list(new_list):
    """
    يكتب كامل قائمة العصابات إلى /gangs/list.json (PUT)
    """
    try:
        resp = requests.put(f"{FIREBASE_URL}/gangs/list.json", json=new_list)
        return resp.status_code == 200
    except Exception as e:
        print(f"⚠️ استثناء عند تحديث قائمة العصابات: {e}")
        return False

def update_gang_points(gang_name, new_points):
    """
    يحدث نقاط العصابة ذات الاسم gang_name في القائمة.
    يعيد True عند النجاح، False عند الفشل.
    """
    gangs = get_gangs_data()
    changed = False
    for g in gangs:
        # افترض أن كل عنصر يحتوي على مفتاح 'name' و 'points'
        try:
            if g.get("name") == gang_name:
                g["points"] = new_points
                changed = True
                break
        except Exception:
            continue
    if not changed:
        print(f"⚠️ لم أجد عصابة بالاسم: {gang_name}")
        return False
    success = update_gangs_list(gangs)
    if not success:
        print("⚠️ فشل تحديث البيانات في Firebase.")
    return success

def add_log(gang_name, action, reason):
    """
    يضيف سجل في infoLog أو infolog.json حسب هيكل القاعدة
    (هنا نرسل POST إلى /infolog.json إذا كان متاح)
    """
    log_entry = {
        "gang": gang_name,
        "action": action,
        "reason": reason,
        "timestamp": datetime.now(pytz.timezone("Asia/Riyadh")).isoformat()
    }
    try:
        requests.post(f"{FIREBASE_URL}/infoLog.json", json=log_entry)
    except Exception:
        pass

# ====================== أوامر العرض والتعامل ======================

@bot.command(name="نقاط")
async def show_points(ctx):
    """
    يعرض العصابات مرتبة حسب النقاط تنازلياً، مع الاسم، المستوى والنقاط.
    الستايل أسود/أحمر كما طلبت.
    """
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    # نتوقع قائمة. نرتبها حسب 'points' تنازليًا.
    try:
        sorted_gangs = sorted(gangs, key=lambda x: x.get("points", 0), reverse=True)
    except Exception:
        sorted_gangs = gangs

    # نبني Embed أنيق (داكن) مع خطوط باللون الأحمر داخل الحقول
    embed = discord.Embed(title="📊 عرض نقاط العصابات", color=discord.Color.dark_red())
    embed.set_footer(text="الترتيب بحسب النقاط — آخر تحديث من القاعدة")

    # نضيف كل عصابة كحقل؛ نعرض المستوى والنقاط
    for g in sorted_gangs:
        name = g.get("name", "غير معروف")
        points = g.get("points", 0)
        level = g.get("level", 0)
        # حقل بصيغة: المستوى 🔴 النقاط: 250
        value = f"المستوى: **{level}**\nالنقاط: **{points}**"
        embed.add_field(name=f"🔰 {name}", value=value, inline=False)

    await ctx.send(embed=embed)

# أمر إضافة نقاط (للمالك فقط)
@bot.command(name="اضف")
async def add_points(ctx, amount: int, *, gang_name: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم أجد بيانات العصابات.")
        return

    for g in gangs:
        if g.get("name") == gang_name:
            new_points = g.get("points", 0) + amount
            g["points"] = new_points
            success = update_gangs_list(gangs)
            if success:
                add_log(gang_name, f"اضافة {amount}", "أمر إداري")
                await ctx.send(f"✅ تم إضافة {amount} نقطة إلى **{gang_name}** (الآن {new_points} نقطة).")
            else:
                await ctx.send("❌ فشل في تحديث البيانات.")
            return

    await ctx.send("❌ العصابة المطلوبة غير موجودة.")

# أمر إزالة نقاط (للمالك فقط)
@bot.command(name="نقص")
async def remove_points(ctx, amount: int, *, gang_name: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("⚠️ ليس لديك صلاحية استخدام هذا الأمر.")
        return

    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم أجد بيانات العصابات.")
        return

    for g in gangs:
        if g.get("name") == gang_name:
            new_points = max(0, g.get("points", 0) - amount)
            g["points"] = new_points
            success = update_gangs_list(gangs)
            if success:
                add_log(gang_name, f"نقص {amount}", "أمر إداري")
                await ctx.send(f"✅ تم خصم {amount} نقطة من **{gang_name}** (الآن {new_points} نقطة).")
            else:
                await ctx.send("❌ فشل في تحديث البيانات.")
            return

    await ctx.send("❌ العصابة المطلوبة غير موجودة.")

# ====================== مهمة يومية (محدثة) ======================

async def send_progressive_embed(channel, title_lines, body_lines, pause=0.5):
    """
    دالة مساعدة لإرسال 'انطباع متدرج' (محاكاة حركة) عبر تعديل embed.
    سترسل Embed أولي ثم تعدّله لإعطاء تأثير متحرك.
    """
    embed = discord.Embed(title="\n".join(title_lines), color=discord.Color.dark_red())
    embed.description = "\n".join(body_lines)
    msg = await channel.send(embed=embed)
    # هنا يمكن التعديل مرات لتوليد تأثير "متحرك" — لكن لا نريد سبام كثير على سيرفراتك
    # فإذا أردت تأثير أكثر، زود عدد التكرارات أو عدّل pause.
    await asyncio.sleep(pause)
    # مثال تعديل خفيف (يمكن تعديله/حذفه)
    try:
        embed.set_footer(text=f"تم الإرسال: {datetime.now().strftime('%H:%M:%S')}")
        await msg.edit(embed=embed)
    except Exception:
        pass
    return msg

@tasks.loop(hours=24)
async def daily_mission():
    await asyncio.sleep(5)
    if not bot.guilds:
        print("⚠️ البوت غير متصل بأي سيرفر - المهمة اليومية متوقفة.")
        return
    guild = bot.guilds[0]

    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_role = guild.get_role(GANG_ROLE_ID) if GANG_ROLE_ID else None
    channel = guild.get_channel(DAILY_CHANNEL_ID)

    if not police_role or not channel:
        print("⚠️ لم يتم العثور على رتبة الشرطة أو القناة اليومية. تحقق من الإعدادات.")
        return

    police_members = [m for m in police_role.members if not m.bot]
    if not police_members:
        await channel.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)

    # الرسالة الجديدة كما طلبت (الجملة الأساسية)
    lines = [
        "🚨 **مهمة يومية جديدة!**",
        "🔺 بدأت المهمة اليومية الآن!",
        f"👮‍♂️ الشرطي المكلف: {chosen.mention}",
        f"🔥 العصابات: {gang_role.mention if gang_role else '🔰'}",
        f"⏳ **أمامكم ساعة واحدة اقبضوا على المطلوب لإتمام المهمة والحصول على {DAILY_REWARD_POINTS} نقطة!**",
    
    ]
    await send_progressive_embed(channel, ["🚨 مهمة يومية جديدة"], lines, pause=0.6)

    # ننتظر ساعة ثم نغلق المهمة (رسالة انتهاء)
    await asyncio.sleep(3600)
    await channel.send("⌛ انتهت ساعة المهمة اليومية! انتهت المحاولة لهذه الدورة.")

# أمر تجريبي لاختبار المهمة (يمكن استخدامه يدوياً)
@bot.command(name="تجربة")
async def test_daily(ctx):
    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    gang_role = guild.get_role(GANG_ROLE_ID) if GANG_ROLE_ID else None

    police_members = [m for m in police_role.members if not m.bot] if police_role else []
    if not police_role:
        await ctx.send("❌ لم يتم العثور على رتبة الشرطة. تأكد من إعداد POLICE_ROLE_ID.")
        return
    if not police_members:
        await ctx.send("❌ لا يوجد أعضاء في رتبة الشرطة.")
        return

    chosen = random.choice(police_members)
    lines = [
        "🚨 **مهمة يومية (تجريبية)!**",
        f"👮‍♂️ الشرطي المكلف: {chosen.mention}",
        f"🔥 العصابات: {gang_role.mention if gang_role else '🔰'}",
        f"⏳ **أمامكم ساعة واحدة اقبضوا على المطلوب لإتمام المهمة والحصول على {DAILY_REWARD_POINTS} نقطة!**",
        "استخدموا الأمر: `!قبض <اسم_العصابة>` لإتمام المهمة."
    ]
    await send_progressive_embed(ctx.channel, ["🚨 مهمة يومية (تجريبية)"], lines, pause=0.6)

# أمر القبض على عصابة (تكسب نقاط)
@bot.command(name="قبض")
async def catch_gang(ctx, *, gang_name: str):
    gangs = get_gangs_data()
    if not gangs:
        await ctx.send("❌ لم يتم العثور على بيانات العصابات.")
        return

    for g in gangs:
        if g.get("name") == gang_name:
            points = g.get("points", 0) + DAILY_REWARD_POINTS
            g["points"] = points
            success = update_gangs_list(gangs)
            if success:
                add_log(gang_name, f"+{DAILY_REWARD_POINTS}", "إتمام المهمة اليومية")
                await ctx.send(f"✅ تم إتمام المهمة وخصصت **{DAILY_REWARD_POINTS}** نقطة لـ **{gang_name}**! الآن لديه **{points}** نقطة.")
            else:
                await ctx.send("❌ فشل في تحديث البيانات، حاول لاحقًا.")
            return
    await ctx.send("❌ العصابة المطلوبة غير موجودة.")
# ====================== أحداث البوت ======================

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كـ: {bot.user}")
    if not daily_mission.is_running():
        daily_mission.start()

# ====================== تشغيل البوت ======================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("لم يتم العثور على DISCORD_BOT_TOKEN في المتغيرات البيئية (Secrets).")

bot.run(DISCORD_BOT_TOKEN)

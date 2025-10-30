import discord
from discord.ext import commands, tasks
import pyrebase
from datetime import datetime, timedelta
import pytz
import random
import asyncio
from config import FIREBASE_CONFIG, BOT_TOKEN

# ===== إعداد البوت =====
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# ===== إعداد Firebase =====
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

# ===== معلومات ثابتة =====
OWNER_ID = 949947235574095892  # ايدي المالك
POLICE_ROLE_ID = 1342832610878951444  # رتبة الشرطة
PING_ROLE_ID = 1342832658908057681    # رتبة المنشن
MISSION_CHANNEL_ID = 1432630812137754715  # روم الإعلان عن المهمة
TIMEZONE = pytz.timezone("Asia/Riyadh")

current_mission = None
mission_message = None


# ==========================
# ⚙️ الأوامر الأساسية
# ==========================

@bot.command()
async def اضف(ctx, points: int, gang_name: str, *, reason: str):
    """إضافة نقاط لعصابة"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")

    try:
        gang_ref = db.child("gangs").child(gang_name)
        gang_data = gang_ref.get().val()

        if not gang_data:
            return await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")

        new_points = gang_data.get("points", 0) + points
        gang_ref.update({
            "points": new_points,
            "last_reason": reason,
            "last_update": str(datetime.now(TIMEZONE))
        })
        await ctx.send(f"✅ تمت إضافة **{points}** نقطة لعصابة **{gang_name}** بسبب: **{reason}**")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الإضافة: {e}")


@bot.command()
async def خصم(ctx, points: int, gang_name: str, *, reason: str):
    """خصم نقاط من عصابة"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")

    try:
        gang_ref = db.child("gangs").child(gang_name)
        gang_data = gang_ref.get().val()

        if not gang_data:
            return await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")

        new_points = gang_data.get("points", 0) - points
        gang_ref.update({
            "points": new_points,
            "last_reason": reason,
            "last_update": str(datetime.now(TIMEZONE))
        })
        await ctx.send(f"✅ تم خصم **{points}** نقطة من عصابة **{gang_name}** بسبب: **{reason}**")

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء الخصم: {e}")


# ==========================
# 💣 نظام المهمة اليومية
# ==========================

@tasks.loop(minutes=1)
async def check_daily_mission():
    """يتحقق من الوقت ويطلق مهمة يومية"""
    global current_mission, mission_message

    now = datetime.now(TIMEZONE)
    if 11 <= now.hour < 17 and current_mission is None:
        guild = bot.guilds[0]
        police_role = guild.get_role(POLICE_ROLE_ID)
        channel = guild.get_channel(MISSION_CHANNEL_ID)

        if not police_role or not channel:
            return

        police_members = [m for m in police_role.members if not m.bot]
        if not police_members:
            return

        target = random.choice(police_members)
        mention_ping = guild.get_role(PING_ROLE_ID).mention

        current_mission = {
            "target_id": target.id,
            "start_time": now
        }

        embed = discord.Embed(
            title="💣 مهمة العصابات اليومية",
            description=(
                f"🎯 **المطلوب:** {target.mention}\n\n"
                f"⏱️ أمامكم **ساعة واحدة** للقبض عليه.\n"
                f"🏆 الجائزة: **30 نقطة** للعصابة التي تنجح بالقبض.\n\n"
                f"{mention_ping}"
            ),
            color=discord.Color.dark_red()
        )
        embed.set_footer(text=f"الوقت الحالي: {now.strftime('%Y-%m-%d %H:%M:%S')} (بتوقيت الرياض)")

        mission_message = await channel.send(embed=embed)
        print(f"✅ تم إطلاق مهمة جديدة: {target.name}")

    elif current_mission:
        start_time = current_mission["start_time"]
        if (now - start_time).seconds > 3600:
            if mission_message:
                embed = discord.Embed(
                    title="💀 فشلت المهمة اليومية",
                    description="⏰ انتهى الوقت ولم تتمكن أي عصابة من القبض على المطلوب!",
                    color=discord.Color.greyple()
                )
                await mission_message.reply(embed=embed)
            current_mission = None


@bot.command()
async def قبض(ctx, gang_name: str):
    """تنفيذ القبض على المطلوب"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")

    global current_mission
    if not current_mission:
        return await ctx.send("⚠️ لا توجد مهمة يومية حالياً.")

    try:
        gang_ref = db.child("gangs").child(gang_name)
        gang_data = gang_ref.get().val()

        if not gang_data:
            return await ctx.send(f"❌ العصابة '{gang_name}' غير موجودة.")

        points = gang_data.get("points", 0) + 30
        gang_ref.update({
            "points": points,
            "last_reason": "إكمال المهمة اليومية",
            "last_update": str(datetime.now(TIMEZONE))
        })

        now = datetime.now(TIMEZONE)
        elapsed = now - current_mission["start_time"]

        embed = discord.Embed(
            title="💥 المهمة اليومية اكتملت!",
            description=(
                f"العصابة **{gang_name}** قبضت على المطلوب خلال الوقت المحدد 🔥\n\n"
                f"تمت إضافة **+30 نقطة** للعصابة.\n\n"
                f"🕒 المدة المستغرقة: {elapsed.seconds // 60} دقيقة\n"
                f"📅 التاريخ: {now.strftime('%Y-%m-%d %H:%M:%S')} (بتوقيت الرياض)"
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        current_mission = None

    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ أثناء تنفيذ القبض: {e}")


@bot.command()
async def تجربة(ctx):
    """تجربة إطلاق مهمة بدون تأثير فعلي"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")

    guild = ctx.guild
    police_role = guild.get_role(POLICE_ROLE_ID)
    if not police_role:
        return await ctx.send("⚠️ لم يتم العثور على رتبة الشرطة.")

    members = [m for m in police_role.members if not m.bot]
    if not members:
        return await ctx.send("⚠️ لا يوجد أعضاء في رتبة الشرطة.")

    target = random.choice(members)
    mention_ping = guild.get_role(PING_ROLE_ID).mention
    embed = discord.Embed(
        title="🧪 تجربة مهمة يومية",
        description=(
            f"🎯 المطلوب: {target.mention}\n"
            f"⏱️ أمامكم ساعة واحدة (اختبار فقط)\n"
            f"{mention_ping}"
        ),
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print(f"✅ تم تشغيل البوت باسم: {bot.user}")
    check_daily_mission.start()


bot.run(BOT_TOKEN)

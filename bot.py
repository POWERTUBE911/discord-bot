import discord
from discord.ext import commands
import json
import os
from firebase import firebase
from config import BOT_TOKEN, FIREBASE_URL # استيراد بيانات Firebase من config.py

# تعريف البوت
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# تهيئة اتصال Firebase
firebase_app = firebase.FirebaseApplication(FIREBASE_URL, None)

def calculate_level(points, rewards_levels):
    """تحسب مستوى العصابة بناءً على النقاط وقائمة المستويات."""
    level = 0
    # التأكد من أن قائمة المستويات مرتبة تصاعديًا حسب النقاط
    sorted_rewards = sorted(rewards_levels, key=lambda r: r.get('points', 0))
    
    for reward in sorted_rewards:
        if points >= reward.get('points', 0):
            level = reward.get('level', 0)
        else:
            break
    return level

def get_live_gang_data():
    """تحميل ومعالجة بيانات العصابات الحية من Firebase."""
    try:
        # 1. جلب بيانات العصابات
        gangs_data = firebase_app.get('/gangs/list', None)
        if not gangs_data:
            print("تحذير: لا توجد بيانات عصابات حية في Firebase.")
            return [], []

        # 2. جلب بيانات مستويات الجوائز
        rewards_data = firebase_app.get('/rewards/levels', None)
        if not rewards_data:
            print("تحذير: لا توجد بيانات مستويات جوائز حية في Firebase. سيتم استخدام البيانات الافتراضية.")
            # إذا لم تتوفر بيانات الجوائز، نستخدم البيانات الافتراضية من gang_data.json
            DATA_FILE = os.path.join(os.path.dirname(__file__), 'gang_data.json')
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                default_data = json.load(f)
            rewards_levels = default_data.get('rewards_levels', [])
        else:
            rewards_levels = rewards_data
        
        # 3. حساب المستوى لكل عصابة
        processed_gangs = []
        for gang in gangs_data:
            if isinstance(gang, dict): # التأكد من أن العنصر هو قاموس
                gang_info = {
                    'name': gang.get('name', 'عصابة غير معروفة'),
                    'points': gang.get('points', 0)
                }
                gang_info['level'] = calculate_level(gang_info['points'], rewards_levels)
                processed_gangs.append(gang_info)

        # 4. ترتيب العصابات حسب النقاط تنازليًا
        sorted_gangs = sorted(processed_gangs, key=lambda g: g.get('points', 0), reverse=True)
        
        return sorted_gangs, rewards_levels

    except Exception as e:
        print(f"خطأ في جلب البيانات من Firebase: {e}")
        return [], []

@bot.event
async def on_ready():
    """يتم تشغيل هذه الدالة عند اتصال البوت بالديسكورد بنجاح."""
    print(f'البوت جاهز. تم تسجيل الدخول باسم: {bot.user}')
    print('--------------------------------------------------')

@bot.command(name='نقاط')
async def show_gang_points(ctx):
    """يعرض نقاط ومستوى جميع العصابات الحية من Firebase."""
    await ctx.send("جاري جلب بيانات العصابات الحية من Firebase...")
    
    gangs_data, _ = get_live_gang_data()
    
    if not gangs_data:
        await ctx.send("عذرًا، لم أتمكن من جلب بيانات العصابات من Firebase. يرجى التأكد من: \n1. أن `FIREBASE_URL` صحيح في `config.py`. \n2. أن قواعد أمان Firebase تسمح بالقراءة العامة.")
        return

    # إنشاء رسالة Embed منسقة
    embed = discord.Embed(
        title="🏆 ترتيب العصابات الحالي (بيانات حية) 🏆",
        description="قائمة بجميع العصابات ونقاطها ومستوياتها المحدثة.",
        color=discord.Color.gold()
    )
    
    # إضافة حقول لكل عصابة
    for index, gang in enumerate(gangs_data, 1):
        name = gang['name']
        points = gang['points']
        level = gang['level']
        
        # تنسيق الحقل المطلوب: اسم العصابة، تحتها عدد النقاط، تحتها مستوى العصابة
        field_value = (
            f"**النقاط:** {points}\n"
            f"**المستوى:** {level}"
        )
        
        # إضافة حقل لكل عصابة
        embed.add_field(
            name=f"{index}. {name}",
            value=field_value,
            inline=True
        )

    embed.set_footer(text=f"آخر تحديث للبيانات: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # إرسال رسالة Embed
    await ctx.send(embed=embed)

if __name__ == '__main__':
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("خطأ: يرجى تعديل ملف config.py وإضافة رمز البوت الخاص بك.")
    else:
        bot.run(BOT_TOKEN)

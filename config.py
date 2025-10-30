# config.py
import os

# يقرأ توكن البوت من Secrets في GitHub Actions أو من متغير البيئة المحلي
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# رابط قاعدة بيانات Firebase (حط رابطك هنا مباشرة)
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app/"

# الإعدادات العامة
OWNER_ID = 949947235574095892
DAILY_CHANNEL_ID = 1432630812137754715
POLICE_ROLE_ID = 1342832610878951444
MENTION_ROLE_ID = 1342832658908057681

import os

# 🧩 رمز البوت (خذه من GitHub Secrets أو اكتبه هنا مؤقتًا)
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or "ضع_توكن_البوت_هنا"

# 🔥 إعداد Firebase Realtime Database
# استبدل الرابط أدناه برابط قاعدة بياناتك في Firebase (Realtime وليس Firestore)
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# 🔐 مفتاح الوصول (اختياري إذا كانت القواعد مفتوحة للقراءة والكتابة)
FIREBASE_SECRET = None

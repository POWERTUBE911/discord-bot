import os

# 🧠 يتم جلب التوكن من GitHub Secrets تلقائياً
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 🔥 رابط قاعدة بيانات Firebase الخاصة بك
FIREBASE_URL = "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app"

# 🔒 إذا كانت قاعدة بياناتك مغلقة وتحتاج مفتاح سري (Firebase Secret)
# يمكنك وضعه هنا، لكن في الغالب ما تحتاجه لأن القاعدة مفتوحة للقراءة/الكتابة للبوت فقط
FIREBASE_SECRET = None

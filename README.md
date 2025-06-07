# MEXC Auto Trading Bot (Telethon + ccxt)

بوت تيليجرام يقرأ إشارات من قناة توصيات ويفتح صفقات تلقائية على MEXC باستخدام جلسة سلسلة (String Session).

## الملفات

- `config.ini` – إعدادات تيليجرام وMEXC (تُستخدم فقط لإنشاء الجلسة)
- `generate_string_session.py` – سكربت لإنشاء الجلسة
- `mexc_api.py` – كود تنفيذ الأوامر على MEXC
- `requirements.txt` – مكتبات المشروع
- `start.py` – يتحقق من وجود الجلسة ويشغل البوت المناسب
- `telegram_mexc_bot_string_session.py` – البوت الفعلي باستخدام Telethon

## متطلبات بيئة التشغيل

- TELEGRAM_STRING_SESSION
- TELEGRAM_API_ID
- TELEGRAM_API_HASH
- MEXC_API_KEY
- MEXC_API_SECRET
- MEXC_LEVERAGE
- MEXC_CAPITAL_PERCENTAGE

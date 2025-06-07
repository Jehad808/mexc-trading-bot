import os
import logging

logging.basicConfig(level=logging.INFO)
session = os.getenv("TELEGRAM_STRING_SESSION")

if session:
    logging.info("تشغيل البوت باستخدام جلسة السلسلة...")
    os.system("python telegram_mexc_bot_string_session.py")
else:
    logging.warning("لم يتم العثور على جلسة السلسلة... تشغيل مولد الجلسة")
    os.system("python generate_string_session.py")

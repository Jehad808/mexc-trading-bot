#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
هذا السكربت يستخدم لإنشاء جلسة سلسلة (String Session) لحساب تيليجرام.
يجب تشغيل هذا السكربت مرة واحدة فقط للحصول على السلسلة.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import configparser
import os

# قراءة الإعدادات من ملف التكوين
def load_config():
    try:
        config = configparser.ConfigParser()
        
        # إنشاء ملف التكوين إذا لم يكن موجوداً
        if not os.path.exists("config.ini"):
            config["TELEGRAM"] = {
                "api_id": "20535892",
                "api_hash": "25252574a23609d7bdeefe9378d97af2",
                "phone": "+966559336168"
            }
            
            config["MEXC"] = {
                "api_key": "mx0vglSFP0y6ypr7Dl",
                "api_secret": "55e276ea2ffc4bb2b2752b4a2906a849",
                "leverage": "100",
                "capital_percentage": "2"
            }
            
            with open("config.ini", "w") as configfile:
                config.write(configfile)
        else:
            config.read("config.ini")
            
        return config
    except Exception as e:
        print(f"خطأ في تحميل ملف التكوين: {e}")
        exit(1)

config = load_config()

api_id = int(config["TELEGRAM"]["api_id"])
api_hash = config["TELEGRAM"]["api_hash"]
phone = config["TELEGRAM"]["phone"]

print("--- إنشاء جلسة سلسلة تيليجرام ---")
print("سيطلب منك إدخال رقم الهاتف ورمز التحقق (وكلمة المرور إذا كانت مفعلة).")

# إنشاء جلسة سلسلة فارغة
string_session = StringSession()

# إنشاء عميل تيليجرام باستخدام الجلسة الفارغة
with TelegramClient(string_session, api_id, api_hash) as client:
    try:
        # محاولة تسجيل الدخول، سيطلب الرمز تلقائياً
        client.start(phone=phone)
        
        # طباعة جلسة السلسلة بعد تسجيل الدخول بنجاح
        session_string = client.session.save()
        print("\n--- تم إنشاء جلسة السلسلة بنجاح! ---")
        print("انسخ السلسلة التالية بالكامل واحتفظ بها في مكان آمن.")
        print("ستحتاج لإضافتها كمتغير بيئة باسم TELEGRAM_STRING_SESSION في Render:")
        print("\n" + session_string + "\n")
        print("---------------------------------------")
        
    except Exception as e:
        print(f"\nحدث خطأ أثناء إنشاء الجلسة: {e}")
        print("تأكد من إدخال المعلومات بشكل صحيح.")


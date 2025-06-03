#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف بدء التشغيل لبوت التداول الآلي على منصة MEXC
هذا الملف يقوم بتشغيل البوت المناسب بناءً على وجود متغير البيئة TELEGRAM_STRING_SESSION
"""

import os
import sys
import logging

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='startup.log'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # التحقق من وجود متغير البيئة TELEGRAM_STRING_SESSION
        string_session = os.environ.get('TELEGRAM_STRING_SESSION')
        
        if string_session:
            logger.info("تم العثور على متغير البيئة TELEGRAM_STRING_SESSION، تشغيل البوت باستخدام جلسة السلسلة...")
            # تشغيل البوت باستخدام جلسة السلسلة
            os.system('python telegram_mexc_bot_string_session.py')
        else:
            logger.info("لم يتم العثور على متغير البيئة TELEGRAM_STRING_SESSION، تشغيل سكربت إنشاء جلسة السلسلة...")
            # تشغيل سكربت إنشاء جلسة السلسلة
            os.system('python generate_string_session.py')
            
    except Exception as e:
        logger.error(f"خطأ في بدء التشغيل: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

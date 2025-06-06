import os
import logging
import re
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import mexc_api

# إعداد التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# الحصول على معلومات API من متغيرات البيئة
api_id = int(os.environ.get('TELEGRAM_API_ID', '20535892'))
api_hash = os.environ.get('TELEGRAM_API_HASH', '25252574a23609d7bdeefe9378d97af2')
mexc_api_key = os.environ.get('MEXC_API_KEY', 'mx0vglSFP0y6ypr7Dl')
mexc_api_secret = os.environ.get('MEXC_API_SECRET', '55e276ea2ffc4bb2b2752b4a2906a849')
leverage = int(os.environ.get('MEXC_LEVERAGE', '100'))
capital_percentage = float(os.environ.get('MEXC_CAPITAL_PERCENTAGE', '2'))

# إنشاء عميل تيليجرام باستخدام جلسة محلية
client = TelegramClient('mexc_bot_session', api_id, api_hash)

# إنشاء كائن API لمنصة MEXC
mexc = mexc_api.MEXC(mexc_api_key, mexc_api_secret)

# نمط للتعرف على رسائل الصفقات
trade_pattern = re.compile(r'#(\w+)(?:/USDT)?\s+(LONG|SHORT|شراء|بيع)(?:\s+@\s+(\d+\.\d+))?(?:\s+TP\s+(\d+\.\d+))?(?:\s+SL\s+(\d+\.\d+))?', re.IGNORECASE)

@client.on(events.NewMessage)
async def handle_new_message(event):
    try:
        # التحقق من أن الرسالة نصية
        if not event.message.text:
            return
        
        logger.info(f"تم استلام رسالة: {event.message.text}")
        
        # البحث عن نمط الصفقة في الرسالة
        match = trade_pattern.search(event.message.text)
        if match:
            symbol, direction, entry_price, take_profit, stop_loss = match.groups()
            
            # تحويل الاتجاه إلى الإنجليزية إذا كان بالعربية
            if direction == 'شراء':
                direction = 'LONG'
            elif direction == 'بيع':
                direction = 'SHORT'
            
            # إضافة USDT إلى الرمز إذا لم يكن موجوداً
            if 'USDT' not in symbol:
                symbol = f"{symbol}USDT"
            
            logger.info(f"تم اكتشاف صفقة: {symbol} {direction} بسعر دخول {entry_price}, TP: {take_profit}, SL: {stop_loss}")
            
            # فتح صفقة في منصة MEXC
            result = mexc.open_position(
                symbol=symbol,
                direction=direction,
                leverage=leverage,
                capital_percentage=capital_percentage,
                entry_price=entry_price,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            
            logger.info(f"نتيجة فتح الصفقة: {result}")
            
            # إرسال تأكيد إلى المستخدم
            await event.respond(f"تم فتح صفقة {direction} على {symbol} بنجاح!")
    
    except Exception as e:
        logger.error(f"حدث خطأ: {str(e)}")
        await event.respond(f"حدث خطأ أثناء معالجة الصفقة: {str(e)}")

def main():
    """تشغيل البوت"""
    logger.info("بدء تشغيل البوت...")
    
    # بدء تشغيل العميل بدون طلب رمز تحقق (سيستخدم الجلسة المحفوظة)
    client.start(phone=lambda: "+966559336168", password=lambda: "1234", code_callback=lambda: "99369")
    
    logger.info("تم تسجيل الدخول بنجاح!")
    
    # تشغيل البوت حتى يتم إيقافه
    client.run_until_disconnected()

if __name__ == "__main__":
    main()

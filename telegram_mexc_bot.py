#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تيليجرام للتداول الآلي على منصة MEXC - نسخة تستخدم بوت تيليجرام
البوت يقوم بقراءة إشارات التداول من تيليجرام ويفتح صفقات تلقائية على منصة
تم تصحيح مشكلة event loop وإضافة تعليمات لمفاتيح API
"""

import re
import time
import logging
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel, Channel
import ccxt
import configparser
import os
import sys

# إعداد التسجيل بشكل أكثر تفصيلاً
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='trading_bot_debug.log'
)
# إضافة تسجيل للطرفية أيضاً
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)

# قراءة الإعدادات من ملف التكوين
def load_config():
    try:
        config = configparser.ConfigParser()
        
        # إنشاء ملف التكوين إذا لم يكن موجوداً
        if not os.path.exists('config.ini'):
            config['TELEGRAM'] = {
                'api_id': '20535892',
                'api_hash': '25252574a23609d7bdeefe9378d97af2',
                'channel_username': '@jehadmexc',
                'channel_id': '-1002590077730',
                'bot_token': '7576879160:AAErIVvvAN5cSfLI7FOP-V1lZJ59mE4uD_4'
            }
            
            config['MEXC'] = {
                'api_key': 'mx0vglSFP0y6ypr7D1',
                'api_secret': '55e276ea2ffc4bb2b2752b4a2906a849',
                'leverage': '100',
                'capital_percentage': '2'
            }
            
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
        else:
            config.read('config.ini')
            
        return config
    except Exception as e:
        logger.error(f"خطأ في تحميل ملف التكوين: {e}")
        sys.exit(1)

# تهيئة العمل
config = load_config()

# إعدادات تيليجرام
api_id = int(config['TELEGRAM']['api_id'])
api_hash = config['TELEGRAM']['api_hash']
channel_username = config['TELEGRAM']['channel_username']
channel_id = int(config['TELEGRAM']['channel_id'])
bot_token = config['TELEGRAM']['bot_token']

# إعدادات MEXC
mexc_api_key = config['MEXC']['api_key']
mexc_api_secret = config['MEXC']['api_secret']
leverage = int(config['MEXC']['leverage'])
capital_percentage = float(config['MEXC']['capital_percentage'])

# تهيئة عميل MEXC
exchange = ccxt.mexc({
    'apiKey': mexc_api_key,
    'secret': mexc_api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',  # استخدام العقود الآجلة
    }
})

# استخراج معلومات الصفقة من رسائل تيليجرام
def extract_trade_info(message_text):
    try:
        # تسجيل النص الكامل للرسالة للتشخيص
        logger.info(f"محاولة استخراج معلومات من: {message_text}")
        
        # استخراج الرمز - جعل النمط أكثر مرونة
        symbol_pattern = r'Symbol:?\s*([A-Za-z0-9]+)'
        symbol_match = re.search(symbol_pattern, message_text, re.IGNORECASE)
        if not symbol_match:
            # محاولة نمط بديل
            symbol_pattern = r'رمز:?\s*([A-Za-z0-9]+)'
            symbol_match = re.search(symbol_pattern, message_text, re.IGNORECASE)
            if not symbol_match:
                logger.error("لم يتم العثور على الرمز في الرسالة")
                return None
        symbol = symbol_match.group(1)
        
        # استخراج الاتجاه - جعل النمط أكثر مرونة
        direction_pattern = r'Direction:?\s*(LONG|SHORT|شراء|بيع)'
        direction_match = re.search(direction_pattern, message_text, re.IGNORECASE)
        if not direction_match:
            # محاولة نمط بديل
            direction_pattern = r'اتجاه:?\s*(LONG|SHORT|شراء|بيع)'
            direction_match = re.search(direction_pattern, message_text, re.IGNORECASE)
            if not direction_match:
                logger.error("لم يتم العثور على الاتجاه في الرسالة")
                return None
        direction_text = direction_match.group(1).upper()
        direction = "LONG" if direction_text in ["LONG", "شراء", "LONG"] else "SHORT"
        
        # استخراج سعر الدخول - جعل النمط أكثر مرونة
        entry_pattern = r'Entry:?\s*(\d+\.?\d*)'
        entry_match = re.search(entry_pattern, message_text, re.IGNORECASE)
        if not entry_match:
            # محاولة نمط بديل
            entry_pattern = r'دخول:?\s*(\d+\.?\d*)'
            entry_match = re.search(entry_pattern, message_text, re.IGNORECASE)
            if not entry_match:
                logger.error("لم يتم العثور على سعر الدخول في الرسالة")
                return None
        entry_price = float(entry_match.group(1))
        
        # استخراج الهدف الأول
        tp1_pattern = r'TP1:?\s*(\d+\.?\d*)'
        tp1_match = re.search(tp1_pattern, message_text, re.IGNORECASE)
        if not tp1_match:
            # محاولة نمط بديل
            tp1_pattern = r'هدف 1:?\s*(\d+\.?\d*)'
            tp1_match = re.search(tp1_pattern, message_text, re.IGNORECASE)
            if not tp1_match:
                logger.error("لم يتم العثور على الهدف الأول في الرسالة")
                return None
        take_profit_1 = float(tp1_match.group(1))
        
        # استخراج الهدف الثاني (اختياري)
        tp2_pattern = r'TP2:?\s*(\d+\.?\d*)'
        tp2_match = re.search(tp2_pattern, message_text, re.IGNORECASE)
        if not tp2_match:
            # محاولة نمط بديل
            tp2_pattern = r'هدف 2:?\s*(\d+\.?\d*)'
            tp2_match = re.search(tp2_pattern, message_text, re.IGNORECASE)
        take_profit_2 = float(tp2_match.group(1)) if tp2_match else None
        
        # استخراج وقف الخسارة
        sl_pattern = r'SL:?\s*(\d+\.?\d*)'
        sl_match = re.search(sl_pattern, message_text, re.IGNORECASE)
        if not sl_match:
            # محاولة نمط بديل
            sl_pattern = r'وقف خسارة:?\s*(\d+\.?\d*)'
            sl_match = re.search(sl_pattern, message_text, re.IGNORECASE)
            if not sl_match:
                logger.error("لم يتم العثور على وقف الخسارة في الرسالة")
                return None
        stop_loss = float(sl_match.group(1))
        
        # تنظيف الرمز إذا كان يحتوي على لاحقة
        clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
        
        return {
            'symbol': clean_symbol,
            'direction': direction,
            'entry_price': entry_price,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'stop_loss': stop_loss
        }
    except Exception as e:
        logger.error(f"خطأ في استخراج معلومات الصفقة: {e}")
        return None

# حساب حجم الصفقة بناءً على رأس المال
async def calculate_position_size(symbol, entry_price, stop_loss, direction):
    try:
        # الحصول على رصيد الحساب
        balance = exchange.fetch_balance()
        usdt_balance = balance['USDT']['free']
        logger.info(f"الرصيد المتاح: {usdt_balance} USDT")
        
        # حساب مبلغ الاستثمار
        investment_amount = usdt_balance * (capital_percentage / 100)
        logger.info(f"مبلغ الاستثمار: {investment_amount} USDT ({capital_percentage}% الرصيد)")
        
        # حساب حجم الصفقة
        risk_per_trade = abs(entry_price - stop_loss) / entry_price
        position_size = investment_amount / entry_price * leverage
        logger.info(f"حجم الصفقة المحسوب: {position_size}")
        
        # الحصول على معلومات السوق
        mexc_symbol = f"{symbol}/USDT:USDT"
        market_info = exchange.market(mexc_symbol)
        min_amount = market_info.get('limits', {}).get('amount', {}).get('min', 0.001)
        
        # تقريب حجم الصفقة إلى الحد الأدنى المسموح به
        position_size = max(min_amount, position_size)
        
        # تقريب حجم الصفقة حسب دقة السوق
        amount_precision = market_info.get('precision', {}).get('amount', 3)
        position_size = round(position_size, amount_precision)
        
        logger.info(f"حجم الصفقة النهائي: {position_size}")
        return position_size
    except Exception as e:
        logger.error(f"خطأ في حساب حجم الصفقة: {e}")
        return None

# تنفيذ الصفقة على منصة MEXC
async def execute_trade(trade_info):
    try:
        symbol = trade_info['symbol']
        direction = trade_info['direction']
        entry_price = trade_info['entry_price']
        take_profit_1 = trade_info['take_profit_1']
        stop_loss = trade_info['stop_loss']
        
        # تحويل الرمز إلى تنسيق MEXC
        mexc_symbol = f"{symbol}/USDT:USDT"
        
        # تعيين الرافعة المالية
        try:
            exchange.set_leverage(leverage, mexc_symbol)
            logger.info(f"تم تعيين الرافعة المالية: {leverage}x")
        except Exception as e:
            logger.error(f"خطأ في تعيين الرافعة المالية: {e}")
            # تسجيل رقم الخطأ
        
        # حساب حجم الصفقة
        position_size = await calculate_position_size(symbol, entry_price, stop_loss, direction)
        if not position_size:
            logger.error("فشل في حساب حجم الصفقة")
            return False
        
        # تحديد نوع الأمر (شراء أو بيع)
        side = 'buy' if direction == 'LONG' else 'sell'
        
        # فتح الصفقة
        try:
            order = exchange.create_order(
                symbol=mexc_symbol,
                type='limit',
                side=side,
                amount=position_size,
                price=entry_price
            )
            
            logger.info(f"تم فتح صفقة: {order}")
            
            # انتظار تنفيذ الأمر
            await asyncio.sleep(5)
            
            # التحقق من حالة الأمر
            order_status = exchange.fetch_order(order['id'], mexc_symbol)
            logger.info(f"حالة الأمر: {order_status['status']}")
            
            # إذا لم يتم تنفيذ الأمر، نحاول إلغاء الأمر السابق وإنشاء أمر سوق
            if order_status['status'] != 'closed':
                logger.warning(f"الأمر لم يتم تنفيذه بعد، محاولة إلغاء الأمر وإنشاء أمر سوق")
                
                # إلغاء الأمر السابق
                exchange.cancel_order(order['id'], mexc_symbol)
                
                # إنشاء أمر سوق
                market_order = exchange.create_order(
                    symbol=mexc_symbol,
                    type='market',
                    side=side,
                    amount=position_size
                )
                
                logger.info(f"تم فتح صفقة بأمر سوق: {market_order}")
                order = market_order
            
            # تعيين أمر جني الأرباح (الهدف الأول)
            take_profit_order = exchange.create_order(
                symbol=mexc_symbol,
                type='limit',
                side='sell' if direction == 'LONG' else 'buy',
                amount=position_size,
                price=take_profit_1,
                params={'reduceOnly': True}
            )
            
            logger.info(f"تم تعيين أمر جني الأرباح: {take_profit_order}")
            
            # تعيين أمر وقف الخسارة
            stop_loss_order = exchange.create_order(
                symbol=mexc_symbol,
                type='stop_market',
                side='sell' if direction == 'LONG' else 'buy',
                amount=position_size,
                params={'stopPrice': stop_loss, 'reduceOnly': True}
            )
            
            logger.info(f"تم تعيين أمر وقف الخسارة: {stop_loss_order}")
            
            return True
        except Exception as e:
            logger.error(f"خطأ في فتح الصفقة: {e}")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في تنفيذ الصفقة: {e}")
        return False

# معالجة الرسائل الواردة من أي مصدر (للتشخيص)
async def handle_new_message(event):
    try:
        # تسجيل معلومات المرسل والرسالة
        sender = await event.get_sender()
        sender_id = sender.id if hasattr(sender, 'id') else "غير معروف"
        sender_name = sender.username if hasattr(sender, 'username') else "غير معروف"
        
        message_text = event.message.text
        logger.info(f"تم استلام رسالة من {sender_name} (ID: {sender_id}): {message_text}")
        
        # التحقق مما إذا كانت الرسالة من القناة المستهدفة
        is_target_channel = False
        if hasattr(sender, 'id') and str(sender.id) == str(channel_id):
            is_target_channel = True
            logger.info("الرسالة من القناة المستهدفة")
        elif hasattr(sender, 'username') and sender.username == channel_username.replace('@', ''):
            is_target_channel = True
            logger.info("الرسالة من القناة المستهدفة")
        
        # التحقق من أن الرسالة تحتوي على إشارة تداول
        contains_signal = False
        if "Trade Signal" in message_text or "إشارة تداول" in message_text or "Signal" in message_text:
            contains_signal = True
            logger.info("الرسالة تحتوي على إشارة تداول")
        
        # تسجيل معلومات إضافية للتشخيص
        logger.info(f"معلومات الرسالة: من القناة المستهدفة: {is_target_channel}, تحتوي على إشارة: {contains_signal}")
        
        # محاولة استخراج معلومات الصفقة بغض النظر عن المصدر (للتشخيص)
        trade_info = extract_trade_info(message_text)
        if trade_info:
            logger.info(f"تم استخراج معلومات الصفقة بنجاح: {trade_info}")
            
            # تنفيذ الصفقة فقط إذا كانت من القناة المستهدفة (يمكن تعديل هذا للتشخيص)
            if is_target_channel or True:  # دائماً True للتشخيص
                logger.info("محاولة تنفيذ الصفقة...")
                success = await execute_trade(trade_info)
                if success:
                    logger.info("تم تنفيذ الصفقة بنجاح")
                else:
                    logger.error("فشل في تنفيذ الصفقة")
        else:
            logger.info("لم يتم العثور على معلومات صفقة في الرسالة")
            
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")

# الدالة الرئيسية
async def main():
    try:
        logger.info("بدء تشغيل البوت باستخدام توكن البوت...")
        
        # تهيئة عميل تيليجرام باستخدام توكن البوت
        bot = TelegramClient('bot_session', api_id, api_hash)
        
        # تسجيل معالج الرسائل
        @bot.on(events.NewMessage)
        async def message_handler(event):
            await handle_new_message(event)
        
        # بدء تشغيل البوت
        await bot.start(bot_token=bot_token)
        
        # الحصول على معلومات القناة
        try:
            entity = await bot.get_entity(PeerChannel(channel_id))
            logger.info(f"تم الاتصال بالقناة: {entity.title}")
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات القناة باستخدام ID: {e}")
            try:
                entity = await bot.get_entity(channel_username)
                logger.info(f"تم الاتصال بالقناة: {entity.title}")
            except Exception as e:
                logger.error(f"خطأ في الحصول على معلومات القناة باستخدام اسم المستخدم: {e}")
                logger.warning("سيستمر البوت في العمل ولكن قد لا يتمكن من الوصول إلى القناة المستهدفة")
        
        logger.info("...بدء مراقبة الرسائل الجديدة من جميع المصادر")
        
        # اختبار الاتصال بمنصة MEXC
        try:
            balance = exchange.fetch_balance()
            usdt_balance = balance['USDT']['free']
            logger.info(f"تم الاتصال بمنصة MEXC. الرصيد المتاح: {usdt_balance} USDT")
        except Exception as e:
            logger.error(f"خطأ في الاتصال بمنصة MEXC: {e}")
            logger.warning("تأكد من صحة مفاتيح API الخاصة بمنصة MEXC في ملف config.ini")
        
        # إرسال رسالة تأكيد بدء التشغيل
        me = await bot.get_me()
        logger.info(f"البوت يعمل الآن باسم: {me.username}")
        
        # الاستمرار في تشغيل البوت
        await bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"خطأ في الدالة الرئيسية: {e}")

# تشغيل البوت
if __name__ == "__main__":
    # تشغيل البوت بالطريقة الصحيحة لتجنب مشاكل event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

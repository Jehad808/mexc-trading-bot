#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تيليجرام للتداول الآلي على منصة MEXC
البوت يقوم بقراءة إشارات التداول من قناة تيليجرام ويفتح صفقات تلقائية على منصة
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

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='trading_bot.log'
)
logger = logging.getLogger(__name__)

# قراءة الإعدادات من ملف التكوين
def load_config():
    try:
        config = configparser.ConfigParser()
        
        # إنشاء ملف التكوين إذا لم يكن موجوداً
        if not os.path.exists('config.ini'):
            config['TELEGRAM'] = {
                'api_id': '20535892',
                'api_hash': '25252574a23609d7bdeefe9378d97af2',
                'phone': '+966559336168',
                'channel_username': '@ALHAJRI_VIP_GROUP',
                'channel_id': '-1001757356492',
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
phone = config['TELEGRAM']['phone']
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

# تهيئة عميل تيليجرام
client = TelegramClient('trading_session', api_id, api_hash)

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
        direction = "LONG" if direction_text in ["LONG", "شراء", "شراء"] else "SHORT"
        
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

# معالجة الرسائل الواردة من القناة
@client.on(events.NewMessage(chats=[channel_id, channel_username]))
async def handle_new_message(event):
    try:
        message_text = event.message.text
        logger.info(f"تم استلام رسالة: {message_text}")
        
        # التحقق من أن الرسالة تحتوي على إشارة تداول
        if "Trade Signal" in message_text or "إشارة تداول" in message_text or "Signal" in message_text:
            logger.info(f"تم استلام إشارة تداول جديدة: {message_text}")
            
            # استخراج معلومات الصفقة
            trade_info = extract_trade_info(message_text)
            if not trade_info:
                logger.error("فشل في استخراج معلومات الصفقة")
                return
                
            logger.info(f"معلومات الصفقة: {trade_info}")
            
            # تنفيذ الصفقة
            success = await execute_trade(trade_info)
            if success:
                logger.info("تم تنفيذ الصفقة بنجاح")
            else:
                logger.error("فشل في تنفيذ الصفقة")
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")

# الدالة الرئيسية
async def main():
    try:
        # إذا لم يتوفر توكن البوت، نستخدم رقم الهاتف
        await client.start(phone)
        logger.info("تم تسجيل الدخول باستخدام رقم الهاتف")
        
        # الحصول على معلومات القناة
        try:
            entity = await client.get_entity(PeerChannel(channel_id))
            logger.info(f"تم الاتصال بالقناة: {entity.title}")
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات القناة باستخدام ID: {e}")
            try:
                entity = await client.get_entity(channel_username)
                logger.info(f"تم الاتصال بالقناة: {entity.title}")
            except Exception as e:
                logger.error(f"خطأ في الحصول على معلومات القناة باستخدام اسم المستخدم: {e}")
                return
        
        logger.info("...بدء مراقبة الرسائل الجديدة")
        
        # اختبار الاتصال بمنصة MEXC
        try:
            balance = exchange.fetch_balance()
            usdt_balance = balance['USDT']['free']
            logger.info(f"تم الاتصال بمنصة MEXC. الرصيد المتاح: {usdt_balance} USDT")
            
            # حساب مبلغ الاستثمار
            investment_amount = usdt_balance * (capital_percentage / 100)
            logger.info(f"مبلغ الاستثمار: {investment_amount} USDT ({capital_percentage}% الرصيد)")
        except Exception as e:
            logger.error(f"خطأ في الاتصال بمنصة MEXC: {e}")
        
        # الاستمرار في تشغيل البوت
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"خطأ في الدالة الرئيسية: {e}")

# تشغيل البوت
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")

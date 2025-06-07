import os, re, logging
from telethon.sync import TelegramClient, events
from telethon.sessions import StringSession
from mexc_api import MEXC

# إعدادات اللوغز
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# متغيرات البيئة
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
string = os.getenv("TELEGRAM_STRING_SESSION")

mexc_key = os.getenv("MEXC_API_KEY")
mexc_secret = os.getenv("MEXC_API_SECRET")
leverage = int(os.getenv("MEXC_LEVERAGE", 100))
capital = float(os.getenv("MEXC_CAPITAL_PERCENTAGE", 2.0))

# تهيئة العملاء
client = TelegramClient(StringSession(string), api_id, api_hash)
mexc = MEXC(mexc_key, mexc_secret)

# النمط للتعرف على الصفقات، مع قبول الرموز التي فيها لاحقة مثل BTCUSDT.P
pattern = re.compile(
    r'Symbol:\s*([\w\.]+)\s*'
    r'Direction:\s*(LONG|SHORT)\s*'
    r'Entry Price:\s*([\d.]+)\s*'
    r'Take Profit 1:\s*([\d.]+)\s*'
    r'(?:Take Profit 2:\s*([\d.]+)\s*)?'
    r'Stop Loss:\s*([\d.]+)',
    re.IGNORECASE
)

@client.on(events.NewMessage)
async def handler(event):
    try:
        match = pattern.search(event.raw_text)
        if not match:
            return

        raw_symbol, direction, entry, tp1, tp2, sl = match.groups()
        symbol = raw_symbol.upper().replace(".P", "").replace(".S", "")  # إزالة اللواحق مثل .P أو .S

        entry, tp1, sl = float(entry), float(tp1), float(sl)

        balance = mexc.get_balance()
        if not balance or balance <= 0:
            await event.reply("❌ لا يوجد رصيد متاح في MEXC.")
            return

        size = round((balance * (capital / 100)) / entry, 3)

        result = mexc.open_position(
            symbol=symbol,
            direction=direction,
            leverage=leverage,
            capital_percentage=capital,
            entry_price=entry,
            take_profit=tp1,
            stop_loss=sl
        )

        if result["status"] == "success":
            await event.reply(f"🚀 تم فتح صفقة {direction} على {symbol} بحجم {size}\n✅ النتيجة: {result['message']}")
        else:
            await event.reply(f"❌ فشل فتح الصفقة: {result['message']}")

    except Exception as e:
        logger.error(f"خطأ أثناء فتح الصفقة: {e}")
        await event.reply(f"⚠️ حدث خطأ: {e}")

# تشغيل البوت
client.start()
logger.info("✅ تم تسجيل الدخول، البوت يعمل الآن...")
client.run_until_disconnected()

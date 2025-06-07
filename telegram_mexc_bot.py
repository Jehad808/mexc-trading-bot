import os, re, logging
from telethon.sync import TelegramClient, events
from telethon.sessions import StringSession
from mexc_api import MEXC

logging.basicConfig(level=logging.INFO)

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
string = os.getenv("TELEGRAM_STRING_SESSION")

mexc_key = os.getenv("MEXC_API_KEY")
mexc_secret = os.getenv("MEXC_API_SECRET")
leverage = int(os.getenv("MEXC_LEVERAGE"))
capital = float(os.getenv("MEXC_CAPITAL_PERCENTAGE"))

client = TelegramClient(StringSession(string), api_id, api_hash)
mexc = MEXC(mexc_key, mexc_secret)

pattern = re.compile(r'Symbol:\s*(\w+)\s*Direction:\s*(LONG|SHORT)\s*Entry Price:\s*([\d.]+)\s*Take Profit 1:\s*([\d.]+)\s*Take Profit 2:\s*([\d.]+)?\s*Stop Loss:\s*([\d.]+)', re.IGNORECASE)

@client.on(events.NewMessage)
async def handler(event):
    match = pattern.search(event.raw_text)
    if not match:
        return
    symbol, direction, entry, tp1, _, sl = match.groups()
    entry, tp1, sl = float(entry), float(tp1), float(sl)
    balance = mexc.get_balance()
    size = round((balance * (capital / 100)) / entry, 3)
    order = mexc.create_order(symbol, entry, size, direction, leverage)
    await event.reply(f"🚀 صفقة {direction} على {symbol} بحجم {size}\nالنتيجة: {order}")

client.start()
client.run_until_disconnected()

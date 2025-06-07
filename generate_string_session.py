from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

api_id = int(config["TELEGRAM"]["api_id"])
api_hash = config["TELEGRAM"]["api_hash"]
phone = config["TELEGRAM"]["phone"]

with TelegramClient(StringSession(), api_id, api_hash) as client:
    client.start(phone=phone)
    session = client.session.save()
    print("String Session:\n", session)

import hmac
import hashlib
from urllib.parse import parse_qsl
import os

BOT_TOKEN = os.getenv("TOKEN")


def parse_telegram_init_data(init_data_str: str):
    data = dict(parse_qsl(init_data_str, strict_parsing=True))
    hash_ = data.pop("hash", None)
    check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key.encode(), check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_:
        raise ValueError("Invalid Telegram initData signature")

    return data

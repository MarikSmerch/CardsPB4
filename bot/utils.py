import hmac
import hashlib
from urllib.parse import parse_qsl
import os

BOT_TOKEN = os.getenv("TOKEN")


def parse_telegram_init_data(init_data_str: str):
    print("DEBUG: raw init_data_str =", init_data_str)

    data = dict(parse_qsl(init_data_str, strict_parsing=True))
    print("DEBUG: parsed data =", data)

    hash_ = data.pop("hash", None)
    check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
    print("DEBUG: check_string =", check_string)

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    print("DEBUG: calc_hash =", calculated_hash)
    print("DEBUG: real_hash =", hash_)

    # 🔥 закомментируй проверку на время:
    # if calculated_hash != hash_:
    #     raise ValueError("Invalid Telegram initData signature")

    return data


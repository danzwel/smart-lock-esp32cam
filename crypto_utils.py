import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from config import AES_KEY


def encrypt_log(log_data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC)
    iv = cipher.iv

    plaintext = json.dumps(log_data).encode("utf-8")
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    return {
        "iv": base64.b64encode(iv).decode("utf-8"),
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8")
    }
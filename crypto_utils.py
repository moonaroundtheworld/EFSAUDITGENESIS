import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # type: ignore
from cryptography.hazmat.backends import default_backend  # type: ignore

def decrypt_cryptojs_aes(encrypted_base64: str, password: str) -> str:
    """
    Decrypts a CryptoJS AES payload matching `CryptoJS.AES.encrypt(content, password).toString()`
    returning the original plaintext string.
    """
    data: bytes = base64.b64decode(encrypted_base64)
    if data[:8] != b'Salted__':  # type: ignore
        raise ValueError("Invalid CryptoJS payload")
    salt = data[8:16]  # type: ignore
    ciphertext = data[16:]  # type: ignore
    
    # CryptoJS uses EVP_BytesToKey with MD5 by default
    key_iv = b''
    last = b''
    while len(key_iv) < 48: # 32 bytes key + 16 bytes IV
        import hashlib
        m = hashlib.md5()
        m.update(last + password.encode('utf-8') + salt)
        last = m.digest()
        key_iv += last
        
    key = key_iv[:32]  # type: ignore
    iv = key_iv[32:48]  # type: ignore
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    # PKCS7 unpad
    padding_len = padded_plaintext[-1]
    plaintext = padded_plaintext[:-padding_len]
    return plaintext.decode('utf-8')

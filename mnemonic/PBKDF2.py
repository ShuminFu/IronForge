import argparse
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken

def derive_key(password, salt, iterations=100000):
    """从密码派生密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_text(text, password):
    """加密文本"""
    salt = os.urandom(16)
    key = derive_key(password, salt)
    f = Fernet(key)
    encrypted_text = f.encrypt(text.encode())
    result = base64.urlsafe_b64encode(salt + encrypted_text).decode()
    print("result length: ", len(result))
    return result

def decrypt_text(encrypted_text, password):
    """解密文本"""
    try:
        # 移除所有空白字符，包括换行符
        encrypted_text = ''.join(encrypted_text.split())
        decoded = base64.urlsafe_b64decode(encrypted_text)
        print("decoded length: ", len(decoded))
        salt, encrypted = decoded[:16], decoded[16:]
        key = derive_key(password, salt)
        f = Fernet(key)
        decrypted_text = f.decrypt(encrypted).decode()
        return decrypted_text
    except ValueError as e:
        raise ValueError(f"解密失败：无效的输入格式。{str(e)}")
    except InvalidToken:
        raise ValueError("解密失败：无效的令牌。可能是密码错误或数据被篡改。")
    except Exception as e:
        raise ValueError(f"解密失败：{str(e)}")

def main():
    parser = argparse.ArgumentParser(description="加密/解密工具")
    parser.add_argument('mode', choices=['encrypt', 'decrypt'], help="选择模式：加密或解密")
    parser.add_argument('input', help="输入文本或文件路径")
    parser.add_argument('output', help="输出文件路径")
    args = parser.parse_args()

    try:
        if args.mode == 'encrypt':
            if os.path.isfile(args.input):
                with open(args.input, 'r') as f:
                    text = f.read()
            else:
                text = args.input

            password = input("请输入加密密码: ")
            encrypted = encrypt_text(text, password)
            
            with open(args.output, 'w') as f:
                f.write(encrypted)
            print(f"加密结果已保存到 {args.output}")

        elif args.mode == 'decrypt':
            if os.path.isfile(args.input):
                with open(args.input, 'r') as f:
                    encrypted = f.read().strip()
            else:
                encrypted = args.input.strip()

            password = input("请输入解密密码: ")
            decrypted = decrypt_text(encrypted, password)
            
            with open(args.output, 'w') as f:
                f.write(decrypted)
            print(f"解密结果已保存到 {args.output}")

    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()

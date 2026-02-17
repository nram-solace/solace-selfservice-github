#!/usr/bin/env python3
###################################################################################################
# crypto_utils.py
# Cryptographic utilities for encrypting/decrypting sensitive data in configuration files
# Adapted from .dev/solace-gitlab-cicd-poc/scripts/crypto_utils.py
#
# Ramesh Natarajan (nram), Solace PSG
###################################################################################################

import base64
import os
import sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ConfigCrypto:

    def __init__(self, password=None):
        """Initialize crypto with optional password. If not provided, uses PASSWORD_ENC_KEY env var."""
        self.password = password or os.environ.get('PASSWORD_ENC_KEY')
        if not self.password:
            raise ValueError('No encryption key provided. Set PASSWORD_ENC_KEY env var or pass --password flag.')
        self.key = self._derive_key(self.password)
        self.cipher = Fernet(self.key)

    def _derive_key(self, password):
        """Derive encryption key from password using PBKDF2"""
        # Use a fixed salt for consistency (in production, you might want to store this separately)
        salt = b'solace_config_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext):
        """Encrypt plaintext string"""
        if not plaintext:
            return plaintext
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt(self, encrypted_text):
        """Decrypt encrypted string"""
        if not encrypted_text:
            return encrypted_text
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            # If decryption fails, assume it's plaintext
            return encrypted_text


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Encrypt/decrypt strings for Solace inventory files')
    parser.add_argument('--encrypt-string', help='Encrypt a single string and print result')
    parser.add_argument('--decrypt-string', help='Decrypt a single string and print result')
    parser.add_argument('--encryption-key', '--key', dest='key', help='Encryption key (default: use PASSWORD_ENC_KEY env var)')

    args = parser.parse_args()

    try:
        if args.encrypt_string:
            crypto = ConfigCrypto(args.key)
            encrypted = crypto.encrypt(args.encrypt_string)
            print(f"Encrypted string: {encrypted}")
        elif args.decrypt_string:
            crypto = ConfigCrypto(args.key)
            decrypted = crypto.decrypt(args.decrypt_string)
            print(f"Decrypted string: {decrypted}")
        else:
            parser.print_help()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

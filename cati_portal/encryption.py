import os
import os.path as osp
try:
    from secret import choice
except:
    from random import choice
import string

import pgpy
from flask import current_app


password_characters = string.ascii_letters + string.digits
def generate_password(size):
    return ''.join(choice(password_characters) for i in range(size))


def pgp_secret_key():
    default_key_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'pgp', 'secret.key')
    if current_app:
        secret_key_file = current_app.config.get('PGP_SECRET_KEY', default_key_file)
    else:
        secret_key_file = default_key_file
    if osp.exists(secret_key_file):
        pgp_secret_key, other = pgpy.PGPKey.from_file(secret_key_file)
        return pgp_secret_key
    raise FileNotFoundError('Cannot find pgp secret key file')


def pgp_public_key():
    default_key_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'pgp', 'public.key')
    if current_app:
        public_key_file = current_app.config.get('PGP_PUBLIC_KEY', default_key_file)
    else:
        public_key_file = default_key_file
    if osp.exists(public_key_file):
        pgp_public_key, other = pgpy.PGPKey.from_file(public_key_file)
        return pgp_public_key
    raise FileNotFoundError('Cannot find pgp public key file')


def hash_password(password):
    public_key = pgp_public_key()
    salted = pgpy.PGPMessage.new((password + generate_password(22)).encode('UTF8'), sensitive=True, format='b')
    return bytes(public_key.encrypt(salted))


def check_password(password, hash):
    secret_key = pgp_secret_key()
    # Salt length is 22 bytes
    pwd = secret_key.decrypt(pgpy.PGPMessage.from_blob(hash)).message[:-22].decode('UTF8')
    return password == pwd

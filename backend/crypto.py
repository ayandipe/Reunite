# backend/crypto.py
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
fernet = Fernet(os.environ["FERNET_KEY"])
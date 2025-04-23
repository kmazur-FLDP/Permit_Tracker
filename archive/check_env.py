# check_env.py
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env from cwd
print("DATABASE_URL =", os.getenv("DATABASE_URL"))
print("SECRET_KEY  =", os.getenv("SECRET_KEY"))
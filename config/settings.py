### config/settings.py ###
import os
from pathlib import Path

# --- محاسبه مسیر ریشه پروژه به صورت دینامیک ---
# این خط مسیر فایل settings.py را پیدا می‌کند و دو مرحله عقب می‌رود تا به ریشه پروژه برسد
BASE_DIR = Path(__file__).resolve().parent.parent

# --- تنظیمات مسیرها (تبدیل به مسیرهای مطلق) ---
# حالا DATA_DIR دقیقاً به C:\Users\...\trader\data اشاره می‌کند
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
MODEL_DIR = os.path.join(BASE_DIR, "outputs", "model_checkpoints")

# اطمینان از وجود پوشه‌های خروجی
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# --- پارامترهای استراتژی ---
STRATEGY_PARAMS = {
    "ema_period": 200,
    "st_period": 10,
    "st_multiplier": 3.0,
    "st_fast_period": 7,
    "st_fast_multiplier": 2.0,
    "atr_period": 14
}

# --- مدیریت ریسک و سرمایه ---
INITIAL_CAPITAL = 1000.0
RISK_PER_TRADE = 0.01

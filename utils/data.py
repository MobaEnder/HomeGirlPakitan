import json
import os
import asyncio

# ==== ĐƯỜNG DẪN DATA ====
# Nếu Railway có mount volume /data thì sẽ dùng /data/datauser.json
# Nếu không thì fallback về ./data/datauser.json (local test)
if os.path.exists("/data"):
    DATA_FILE = "/data/datauser.json"
else:
    DATA_FILE = "data/datauser.json"

# Biến global để lưu dữ liệu trong RAM
DATA = {}

# Danh sách key mặc định cho mỗi user
DEFAULT_USER = {
    "money": 0,
    "job": None,
    "salary": 0,
    "last_setjob": 0,
    "last_work": 0,
    "last_chuyentien": 0
}


def load_data():
    """Load dữ liệu từ file JSON vào biến global"""
    global DATA
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            DATA = json.load(f)
    except json.JSONDecodeError:
        DATA = {}


def save_data(data=None):
    """Lưu dữ liệu từ RAM xuống file"""
    global DATA
    if data is None:
        data = DATA
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_user(data, user_id: int):
    """Đảm bảo user tồn tại và có đủ key cần thiết"""
    uid = str(user_id)
    if uid not in data:
        data[uid] = DEFAULT_USER.copy()
    else:
        for k, v in DEFAULT_USER.items():
            if k not in data[uid]:
                data[uid][k] = v
    return data[uid]


async def autosave_loop():
    """Tự động lưu dữ liệu mỗi 60s"""
    while True:
        await asyncio.sleep(60)
        save_data()
        print("💾 Dữ liệu đã được autosave!")

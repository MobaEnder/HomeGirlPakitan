import json
import os

# ==== ĐƯỜNG DẪN FILE RIVEN ====
if os.path.exists("/data"):
    RIVENS_FILE = "/data/rivens.json"
else:
    RIVENS_FILE = "data/rivens.json"

# Biến global lưu riven của tất cả user
RIVENS = {}

def load_rivens():
    """Load dữ liệu từ file JSON vào RAM"""
    global RIVENS
    if not os.path.exists(RIVENS_FILE):
        os.makedirs(os.path.dirname(RIVENS_FILE), exist_ok=True)
        with open(RIVENS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    try:
        with open(RIVENS_FILE, "r", encoding="utf-8") as f:
            RIVENS = json.load(f)
    except json.JSONDecodeError:
        RIVENS = {}

def save_rivens(data=None):
    """Lưu dữ liệu từ RAM xuống file"""
    global RIVENS
    if data is None:
        data = RIVENS
    with open(RIVENS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_rivens(user_id: int):
    """Lấy danh sách riven của user"""
    uid = str(user_id)
    if uid not in RIVENS:
        RIVENS[uid] = []
    return RIVENS[uid]

def add_riven(user_id: int, riven_obj: dict):
    """Thêm riven vào inventory của user"""
    uid = str(user_id)
    get_user_rivens(user_id)  # đảm bảo có list
    RIVENS[uid].append(riven_obj)
    save_rivens()

def delete_riven(user_id: int, rid: int) -> bool:
    """Xoá riven theo ID"""
    uid = str(user_id)
    if uid not in RIVENS:
        return False
    for i, rv in enumerate(RIVENS[uid]):
        if rv.get("id") == rid:
            del RIVENS[uid][i]
            save_rivens()
            return True
    return False

# Load dữ liệu khi import
load_rivens()

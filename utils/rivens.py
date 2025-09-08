# utils/rivens.py
import json
import os

if os.path.exists("/data"):
    RIVENS_FILE = "/data/rivens.json"
else:
    RIVENS_FILE = "data/rivens.json"

RIVENS = {}

def load_rivens():
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

def save_rivens():
    global RIVENS
    with open(RIVENS_FILE, "w", encoding="utf-8") as f:
        json.dump(RIVENS, f, ensure_ascii=False, indent=4)

def get_user_rivens(user_id: int):
    uid = str(user_id)
    if uid not in RIVENS:
        RIVENS[uid] = []
    return RIVENS[uid]

def add_riven(user_id: int, riven_obj: dict):
    uid = str(user_id)
    get_user_rivens(user_id)  # ensure exists
    RIVENS[uid].append(riven_obj)
    save_rivens()

def delete_riven(user_id: int, rid: int) -> bool:
    """
    Xóa 1 riven theo ID. 
    Trả về True nếu xóa thành công, False nếu không tìm thấy.
    """
    uid = str(user_id)
    if uid not in RIVENS:
        return False
    for i, rv in enumerate(RIVENS[uid]):
        if rv.get("id") == rid:
            RIVENS[uid].pop(i)
            save_rivens()
            return True
    return False

# Load on import
load_rivens()

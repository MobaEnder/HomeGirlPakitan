import json
import os

# ==== ĐƯỜNG DẪN LƯU DỮ LIỆU TRONG VOLUME ====
VOLUME_PATH = "/data"   # Railway sẽ mount Volume vào /data
DATAUSER_FILE = os.path.join(VOLUME_PATH, "datauser.json")
USERS_FILE = os.path.join(VOLUME_PATH, "users.json")

# ===== HÀM ĐỌC / GHI JSON =====
def read_json(file_path):
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ===== QUẢN LÝ NGƯỜI DÙNG =====
def get_user(user_id: int):
    data = read_json(DATAUSER_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = {"money": 0}
        write_json(DATAUSER_FILE, data)
    return data[str(user_id)]


def update_balance(user_id: int, amount: int):
    data = read_json(DATAUSER_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = {"money": 0}
    data[str(user_id)]["money"] += amount
    write_json(DATAUSER_FILE, data)
    return data[str(user_id)]["money"]


# ===== QUẢN LÝ COOLDOWN =====
def get_cooldown(user_id: int, command: str):
    data = read_json(USERS_FILE)
    if str(user_id) in data and command in data[str(user_id)]:
        return data[str(user_id)][command]
    return 0


def set_cooldown(user_id: int, command: str, timestamp: float):
    data = read_json(USERS_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = {}
    data[str(user_id)][command] = timestamp
    write_json(USERS_FILE, data)

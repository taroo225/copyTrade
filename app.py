import os

from flask import Flask, jsonify
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()
app = Flask(__name__)


# Cấu hình tài khoản master
MT5_LOGIN = int(os.getenv('MT5_LOGIN'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD')
MT5_SERVER = os.getenv('MT5_SERVER')
MT5_PATH = rf"{os.getenv('MT5_PATH')}"


def connect_mt5():
    # Khởi tạo kết nối MT5
    if not mt5.initialize(MT5_PATH):
        print("❌ Lỗi init MT5:", mt5.last_error())
        return False
    # Đăng nhập
    if not mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print("❌ Lỗi login MT5:", mt5.last_error())
        return False
    return True


@app.route("/positions", methods=["GET"])
def get_positions():
    if not connect_mt5():
        return jsonify({"error": "mt5_connection_failed"}), 500

    positions = mt5.positions_get()
    mt5.shutdown()

    if positions is None:
        return jsonify({"error": "no_positions", "mt5_error": mt5.last_error()}), 404

    # Chuyển về list dict để trả JSON
    return jsonify([p._asdict() for p in positions])


@app.route("/orders", methods=["GET"])
def get_orders():
    if not connect_mt5():
        return jsonify({"error": "mt5_connection_failed"}), 500

    orders = mt5.orders_get()
    mt5.shutdown()

    if orders is None:
        return jsonify({"error": "no_orders", "mt5_error": mt5.last_error()}), 404

    return jsonify([o._asdict() for o in orders])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

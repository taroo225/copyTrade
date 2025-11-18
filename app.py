import os

from flask import Flask, jsonify, request
from dotenv import load_dotenv
import MetaTrader5 as mt5

from models import db, Ticket

load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Cấu hình tài khoản master
MT5_LOGIN = int(os.getenv('MT5_LOGIN'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD')
MT5_SERVER = os.getenv('MT5_SERVER')
MT5_PATH = rf"{os.getenv('MT5_PATH')}"


def connect_mt5():
    # Khởi tạo kết nối MT5
    if not mt5.initialize():
        print("❌ Lỗi init MT5:", mt5.last_error())
        return False
    # Đăng nhập
    if not mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print("❌ Lỗi login MT5:", mt5.last_error())
        return False
    return True


@app.route("/positions", methods=["GET"])
def get_positions():
    args = request.args
    broken = args.get("broken", "mt4")
    if broken == "mt4":
        return jsonify([ticket.to_dict() for ticket in Ticket.query.all()])
    else:
        if not connect_mt5():
            return jsonify({"error": "mt5_connection_failed"}), 500

        positions = mt5.positions_get()
        mt5.shutdown()

        if positions is None:
            return jsonify({"error": "no_positions", "mt5_error": mt5.last_error()}), 404

        # Chuyển về list dict để trả JSON
        return jsonify([p._asdict() for p in positions])


@app.route("/positions", methods=["POST"])
def report_positions():
    try:
        data = request.get_json()
        positions = data.get("positions", [])
        account = data.get("account", "")
        if not account:
            return jsonify({"success": False, "message": "Account not found"}), 404
        tickets = {ticket.ticket: ticket for ticket in Ticket.query.filter_by(account=account).all()}
        commit = False
        for position in positions:
            tk = position.get("ticket")
            if not tk:
                continue
            sl = position.get("sl", 0)
            tp = position.get("tp", 0)
            if tk in tickets:  # If ticket existed
                tick = tickets[tk]
                if sl != tick.sl:
                    tick.sl = sl
                    commit = True
                if tp != tick.tp:
                    tick.tp = tp
                    commit = True
                del tickets[tk]
            else:
                symbol = position.get("symbol")
                if "-" in symbol:
                    symbol = symbol.split("-")[0]
                db.session.add(Ticket(ticket=tk, sl=sl, tp=tp,
                                      account=account,
                                      symbol=symbol,
                                      comment=position.get("comment", ""),
                                      type=position.get("type", 0),
                                      volume=position.get("volume"),
                                      price_open=position.get("price_open")))
                commit = True
        if tickets:
            for ticket in tickets.values():
                db.session.delete(ticket)
            commit = True
        if commit:
            db.session.commit()
        return jsonify({"success": True, "message": "Update positions successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error => {str(e)}"}), 500


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
    app.run(port=6868, debug=True, host="0.0.0.0")

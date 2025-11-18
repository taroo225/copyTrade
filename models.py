from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Ticket(db.Model):
    ticket = db.Column(db.Integer, primary_key=True, autoincrement=False)
    account = db.Column(db.Integer)
    symbol = db.Column(db.String(45), nullable=False)
    comment = db.Column(db.String(100), default="", nullable=False)
    type = db.Column(db.Integer, nullable=False)
    volume = db.Column(db.Float, nullable=False)
    price_open = db.Column(db.Float, nullable=False)
    sl = db.Column(db.Float, nullable=False, default=0.0)
    tp = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        return {
            "ticket": self.ticket,
            "account": self.account,
            "symbol": self.symbol,
            "comment": self.comment,
            "type": self.type,
            "volume": self.volume,
            "price_open": self.price_open,
            "sl": self.sl,
            "tp": self.tp
        }

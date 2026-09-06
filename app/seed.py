from .extensions import db
from .models import Prize

PRIZES = [
    {'id': 'accessories-50', 'title': '50% Discount on Accessories', 'description': 'Half price on eligible accessories during your next purchase.', 'image_url': '/assets/accessories-50.svg', 'weight': 20},
    {'id': 'mobiles-5', 'title': '5% Discount on Mobiles', 'description': 'Save 5% on your next mobile purchase.', 'image_url': '/assets/discount-5.svg', 'weight': 20},
    {'id': 'neckband-149', 'title': 'Buy @149/- Neck band', 'description': 'Get a Neck band for the special price of @149/-.', 'image_url': '/assets/cable-offer.svg', 'weight': 15},
    {'id': 'tws-399', 'title': 'Buy @399/- TWS Buds', 'description': 'Get TWS Buds for the special price of @399/-.', 'image_url': '/assets/accessories-50.svg', 'weight': 15},
    {'id': 'watch-799', 'title': 'Buy @799/- Smart Watch', 'description': 'Get a Smart Watch for the special price of @799/-.', 'image_url': '/assets/discount-5.svg', 'weight': 15},
    {'id': 'glass-49', 'title': 'Buy @49/- Glass Protection', 'description': 'Get Glass Protection for the special price of @49/-.', 'image_url': '/assets/tempered-glass.svg', 'weight': 15},
]


def seed_prizes():
    active_ids = {item['id'] for item in PRIZES}
    for prize in db.session.scalars(db.select(Prize)).all():
        if prize.id not in active_ids:
            prize.is_active = False
    for data in PRIZES:
        prize = db.session.get(Prize, data['id'])
        if prize is None:
            db.session.add(Prize(**data))
        else:
            for key, value in data.items():
                setattr(prize, key, value)
            prize.is_active = True
    db.session.commit()

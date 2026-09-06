import re
from flask import jsonify

MOBILE_PATTERN = re.compile(r'^[6-9]\d{9}$')
PRIZE_SEGMENTS = {
    'accessories-50': 0, 'mobiles-5': 1, 'neckband-149': 2,
    'tws-399': 3, 'watch-799': 4, 'glass-49': 5,
}


def normalize_mobile(value):
    if not isinstance(value, str):
        return None
    digits = re.sub(r'\D', '', value)
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    return digits if MOBILE_PATTERN.fullmatch(digits) else None


def error(message, status=400):
    return jsonify({'success': False, 'message': message}), status


def prize_dict(prize):
    return {
        'id': prize.id, 'title': prize.title, 'description': prize.description,
        'image': prize.image_url, 'segmentIndex': PRIZE_SEGMENTS.get(prize.id),
    }


def customer_dict(customer):
    return {
        'mobile': customer.mobile_number, 'name': customer.name, 'address': customer.address,
        'facebookCompleted': customer.facebook_completed,
        'instagramCompleted': customer.instagram_completed,
        'whatsappCompleted': customer.whatsapp_completed,
        'socialComplete': all((customer.facebook_completed, customer.instagram_completed, customer.whatsapp_completed)),
        'createdAt': customer.created_at.isoformat(),
    }


def spin_dict(spin):
    return {'status': spin.status, 'spinDate': spin.spin_time.isoformat(), 'reward': prize_dict(spin.prize)}

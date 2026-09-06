import secrets
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .extensions import db
from .models import Customer, Prize, Spin

def choose_prize():
    """Return one active prize using its database-configured relative weight.

    A ticket is drawn with ``secrets`` (OS-provided randomness), rather than
    accepting any client-side outcome.  For example, weights 20, 20, 15, 15,
    15, 15 give the first two prizes a 20/100 chance each and the remainder a
    15/100 chance each.  Administrators can change only the ``weight`` values
    in the prizes table to change those odds.
    """
    prizes = list(db.session.scalars(
        select(Prize).where(Prize.is_active.is_(True)).order_by(Prize.id)
    ).all())
    if not prizes:
        raise RuntimeError('No active prizes are configured')
    total_weight = sum(prize.weight for prize in prizes)
    if total_weight <= 0:
        raise RuntimeError('Active prize weights must be positive')

    # randbelow(total) produces 0..total-1.  Each prize owns a consecutive
    # range exactly as large as its configured weight.
    ticket = secrets.randbelow(total_weight)
    cumulative_weight = 0
    for prize in prizes:
        cumulative_weight += prize.weight
        if ticket < cumulative_weight:
            return prize
    # Defensive only: an integer ticket is always below total_weight.
    raise RuntimeError('Unable to select a prize')


def create_spin(mobile):
    """Create exactly one spin. MySQL row locking + unique constraints handle races."""
    try:
        with db.session.begin():
            customer = db.session.scalar(select(Customer).where(Customer.mobile_number == mobile).with_for_update())
            if customer is None:
                return None, None, 'missing'
            if not all((customer.facebook_completed, customer.instagram_completed, customer.whatsapp_completed)):
                return customer, None, 'social_incomplete'
            existing = db.session.scalar(select(Spin).where(Spin.customer_id == customer.id))
            if existing:
                return customer, existing, 'existing'
            prize = choose_prize()
            spin = Spin(customer_id=customer.id, prize_id=prize.id, mobile_number=mobile)
            db.session.add(spin)
            db.session.flush()
            db.session.refresh(spin)
            return customer, spin, 'created'
    except IntegrityError:
        db.session.rollback()
        customer = db.session.scalar(select(Customer).where(Customer.mobile_number == mobile))
        existing = db.session.scalar(select(Spin).where(Spin.mobile_number == mobile))
        return customer, existing, 'existing' if existing else 'error'
    except SQLAlchemyError:
        db.session.rollback()
        raise

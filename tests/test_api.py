"""Integration tests. Set MYSQL_TEST_DATABASE_URL to a disposable MySQL database before running pytest."""
import os
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from openpyxl import load_workbook
import pytest

TEST_URL = os.environ.get('MYSQL_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not TEST_URL, reason='MYSQL_TEST_DATABASE_URL is required; tests never use SQLite.')


@pytest.fixture()
def app():
    from app import create_app
    from app.extensions import db
    from app.seed import seed_prizes
    application = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': TEST_URL, 'RATELIMIT_ENABLED': False, 'EXPORT_SECRET': 'test-export-secret'})
    with application.app_context():
        db.drop_all(); db.create_all(); seed_prizes()
    yield application
    with application.app_context(): db.session.remove(); db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, mobile='9876543210'):
    return client.post('/api/customer/register', json={'mobile': mobile, 'name': 'Test Customer', 'address': 'Tadepalligudem'})


def complete_social(client, mobile='9876543210'):
    return client.post('/api/customer/social', json={'mobile': mobile, 'completed': {'facebook': True, 'instagram': True, 'whatsapp': True}})


def test_health_and_validation(client):
    assert client.get('/api/health').status_code == 200
    assert client.post('/api/customer/check', json={'mobile': '5123456789'}).status_code == 400


def test_one_spin_and_existing_result(client):
    assert register(client).status_code == 201
    assert client.post('/api/spin', json={'mobile': '9876543210'}).status_code == 403
    assert complete_social(client).status_code == 200
    first = client.post('/api/spin', json={'mobile': '9876543210'})
    assert first.status_code == 200 and first.json['already_spun'] is False
    assert first.json['spin']['reward']['segmentIndex'] in range(6)
    second = client.post('/api/spin', json={'mobile': '9876543210'})
    assert second.status_code == 200 and second.json['already_spun'] is True
    assert second.json['spin']['reward']['id'] == first.json['spin']['reward']['id']


def test_twenty_simultaneous_requests_create_one_spin(app):
    with app.test_client() as client:
        assert register(client, '9876543211').status_code == 201
        assert complete_social(client, '9876543211').status_code == 200
    def spin_once(_):
        with app.test_client() as concurrent_client:
            return concurrent_client.post('/api/spin', json={'mobile': '9876543211'}).get_json()
    with ThreadPoolExecutor(max_workers=20) as pool:
        responses = list(pool.map(spin_once, range(20)))
    assert all(result['success'] for result in responses)
    assert len({result['spin']['reward']['id'] for result in responses}) == 1


def test_export_requires_secret(client):
    assert client.post('/api/export/customers').status_code == 401
    response = client.post('/api/export/customers', headers={'X-Export-Secret': 'test-export-secret'})
    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def test_today_export_has_requested_columns(client):
    assert client.post('/api/export/today').status_code == 401
    assert client.post('/api/admin/login', json={'password': 'wrong'}).status_code == 401
    assert client.post('/api/admin/login', json={'password': 'SSSM@2013'}).status_code == 200
    entries = client.get('/api/admin/entries')
    assert entries.status_code == 200
    assert entries.json['count'] == 0 and entries.json['entries'] == []
    response = client.post('/api/export/today')
    assert response.status_code == 200
    workbook = load_workbook(BytesIO(response.data))
    assert list(workbook.active.values)[0] == ('customer_name', 'mobile_no', 'address', 'gift')


def test_social_requires_all_confirmations(client):
    assert register(client).status_code == 201
    response = client.post('/api/customer/social', json={'mobile': '9876543210', 'completed': {'facebook': True, 'instagram': True, 'whatsapp': False}})
    assert response.status_code == 400


def test_active_prizes_are_the_six_configured_rewards(app):
    from sqlalchemy import select
    from app.extensions import db
    from app.models import Prize
    with app.app_context():
        prizes = list(db.session.scalars(select(Prize).where(Prize.is_active.is_(True))))
    assert len(prizes) == 6
    assert all(prize.weight > 0 for prize in prizes)

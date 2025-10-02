from app import create_app
from modules.pos.models import POSPaymentMethod

app = create_app('development')
with app.app_context():
    methods = POSPaymentMethod.query.all()
    print('Current payment methods:')
    for m in methods:
        print(f'ID: {m.id}, Name: {m.name}, Code: {m.code}, Is Cash: {m.is_cash}, Active: {m.is_active}')

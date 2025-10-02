from app import create_app, db
from modules.pos.models import POSPaymentMethod

def update_payment_methods():
    app = create_app('development')
    with app.app_context():
        # First, delete all existing payment methods
        POSPaymentMethod.query.delete()
        db.session.commit()
        
        # Create the three required payment methods
        payment_methods = [
            POSPaymentMethod(name='Cash', code='cash', is_cash=True, is_active=True),
            POSPaymentMethod(name='Debit Card', code='card', is_cash=False, is_active=True),
            POSPaymentMethod(name='Mobile Money', code='momo', is_cash=False, is_active=True)
        ]
        
        db.session.add_all(payment_methods)
        db.session.commit()
        
        # Verify the changes
        updated_methods = POSPaymentMethod.query.all()
        print(f"Updated payment methods ({len(updated_methods)}):")
        for method in updated_methods:
            print(f"- {method.name} (code: {method.code})")
        
        print("\nPayment methods have been successfully updated!")

if __name__ == '__main__':
    update_payment_methods()

from app import create_app, db
from modules.pos.models import POSPaymentMethod

def setup_payment_methods():
    """Set up payment methods for the POS system"""
    app = create_app('development')
    with app.app_context():
        # Check existing payment methods
        existing_methods = POSPaymentMethod.query.all()
        print(f"Found {len(existing_methods)} existing payment methods:")
        for method in existing_methods:
            print(f"ID: {method.id}, Name: {method.name}, Code: {method.code}, Is Cash: {method.is_cash}, Active: {method.is_active}")
        
        # Define our payment methods
        payment_methods = [
            {
                'name': 'Cash',
                'code': 'CASH',
                'is_cash': True,
                'is_active': True
            },
            {
                'name': 'Mobile Money (Paystack)',
                'code': 'MOMO',
                'is_cash': False,
                'is_active': True
            },
            {
                'name': 'Debit Card (Paystack)',
                'code': 'CARD',
                'is_cash': False,
                'is_active': True
            }
        ]
        
        # Add payment methods if they don't exist
        added_count = 0
        for method_data in payment_methods:
            # Check if method with this code already exists
            existing = POSPaymentMethod.query.filter_by(code=method_data['code']).first()
            if existing:
                print(f"Payment method with code {method_data['code']} already exists. Skipping.")
                continue
                
            # Create new payment method
            new_method = POSPaymentMethod(
                name=method_data['name'],
                code=method_data['code'],
                is_cash=method_data['is_cash'],
                is_active=method_data['is_active']
            )
            db.session.add(new_method)
            added_count += 1
            print(f"Added payment method: {method_data['name']}")
        
        if added_count > 0:
            db.session.commit()
            print(f"Successfully added {added_count} payment methods")
        else:
            print("No new payment methods were added")

if __name__ == '__main__':
    setup_payment_methods()

"""
This script creates default cash registers in the database.
"""

from app import create_app, db
from modules.pos.models import POSCashRegister

def create_cash_registers():
    """Create default cash registers if none exist"""
    app = create_app('development')
    with app.app_context():
        # Check if any cash registers exist
        existing_registers = POSCashRegister.query.count()
        
        if existing_registers == 0:
            # Create default cash registers
            registers = [
                POSCashRegister(name='Main Register', balance=0.0),
                POSCashRegister(name='Register 2', balance=0.0),
                POSCashRegister(name='Register 3', balance=0.0)
            ]
            
            db.session.add_all(registers)
            db.session.commit()
            
            print(f"Created {len(registers)} cash registers successfully!")
        else:
            print(f"Found {existing_registers} existing cash registers. No new registers created.")
            
            # List existing registers
            registers = POSCashRegister.query.all()
            for register in registers:
                print(f"- {register.name} (ID: {register.id}, Balance: {register.balance})")

if __name__ == '__main__':
    create_cash_registers()

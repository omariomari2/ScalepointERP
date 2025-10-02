"""
Direct Fix for Return Amounts

This script directly fixes the amounts displayed on return forms by updating
the total_amount and refund_amount fields in the database based on the actual 
return line data.
"""
import os
import sys
from app import create_app, db
from modules.pos.models import POSReturn

def fix_return_amounts():
    """Fix the return amounts in the database"""
    print("Starting to fix return amounts...")
    
    # Check if the database file exists
    db_path = 'erp_system.db' 
    if not os.path.exists(db_path):
        db_path = 'instance/erp_system.db'
        if not os.path.exists(db_path):
            print(f"Database file not found at {db_path}")
            print("Checking current directory for .db files...")
            # Find all .db files in the current directory
            db_files = [f for f in os.listdir('.') if f.endswith('.db')]
            if db_files:
                print(f"Found these database files: {', '.join(db_files)}")
                db_path = db_files[0]  # Use the first one
                print(f"Using {db_path}")
            else:
                print("No database files found in the current directory")
                return
    
    # Create app with database path explicitly set
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    app = create_app('development')  # Use development configuration
    
    with app.app_context():
        print(f"Connected to database: {db_path}")
        
        # Get all returns
        try:
            returns = POSReturn.query.all()
            print(f"Found {len(returns)} returns in the database")
            fixed_count = 0
            
            for pos_return in returns:
                print(f"Processing return {pos_return.name} (ID: {pos_return.id})...")
                
                # Calculate the correct total amount by summing all line subtotals
                return_lines = list(pos_return.return_lines)
                line_count = len(return_lines)
                
                if line_count == 0:
                    print(f"  No return lines found for {pos_return.name}, skipping")
                    continue
                    
                correct_total = sum(line.subtotal for line in return_lines)
                
                print(f"  Found {line_count} return lines with total value: {correct_total}")
                print(f"  Current values: total_amount={pos_return.total_amount}, refund_amount={pos_return.refund_amount}")
                
                # Update the total_amount
                pos_return.total_amount = correct_total
                
                # Also update refund_amount if not an exchange
                if pos_return.refund_method != 'exchange':
                    pos_return.refund_amount = correct_total
                
                fixed_count += 1
                print(f"  Updated values: total_amount={pos_return.total_amount}, refund_amount={pos_return.refund_amount}")
            
            # Commit changes
            if fixed_count > 0:
                db.session.commit()
                print(f"Successfully fixed amounts for {fixed_count} returns")
            else:
                print("No returns needed to be fixed")
                
        except Exception as e:
            print(f"Error processing returns: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    fix_return_amounts()
    print("Return amounts fix completed successfully!") 
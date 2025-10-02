"""
Fix Return Subtotals Script

This script fixes the subtotals for all return lines in the database,
ensuring there are no None values causing errors when calculating totals.
"""
from app import create_app
from extensions import db
import sys

def fix_return_subtotals():
    """Fix return subtotals by ensuring no None values and correct calculations"""
    try:
        print("Starting return subtotal fix...")
        app = create_app('production')
        
        with app.app_context():
            # Import models here to avoid circular imports
            from modules.pos.models import POSReturn, POSReturnLine
            
            # Fix return lines with None or incorrect subtotals
            return_lines = POSReturnLine.query.all()
            fixed_count = 0
            affected_returns = set()
            
            for line in return_lines:
                needs_update = False
                
                # Fix None quantities
                if line.quantity is None:
                    line.quantity = 1.0
                    needs_update = True
                    print(f"Fixed None quantity for return line ID {line.id}")
                
                # Fix None unit prices
                if line.unit_price is None:
                    line.unit_price = 0.0
                    needs_update = True
                    print(f"Fixed None unit price for return line ID {line.id}")
                
                # Ensure subtotal is correctly calculated and not None
                try:
                    expected_subtotal = float(line.quantity) * float(line.unit_price)
                    if line.subtotal is None or abs(line.subtotal - expected_subtotal) > 0.01:
                        line.subtotal = expected_subtotal
                        needs_update = True
                        print(f"Updated subtotal for return line ID {line.id}: {line.subtotal}")
                except (TypeError, ValueError) as e:
                    print(f"Error calculating subtotal for line {line.id}: {e}")
                    line.subtotal = 0.0
                    needs_update = True
                
                if needs_update:
                    db.session.add(line)
                    fixed_count += 1
                    affected_returns.add(line.return_id)
            
            if fixed_count > 0:
                db.session.commit()
                print(f"Fixed {fixed_count} return lines")
            else:
                print("No return lines needed fixing")
            
            # Update total amounts for all returns that had fixed lines
            fixed_returns = 0
            
            for return_id in affected_returns:
                return_obj = POSReturn.query.get(return_id)
                if not return_obj:
                    continue
                
                # Calculate total from return lines with safe handling of None values
                total = 0.0
                for line in return_obj.return_lines:
                    if line.subtotal is not None:
                        total += line.subtotal
                
                # Update the return total if needed
                if return_obj.total_amount is None or abs(return_obj.total_amount - total) > 0.01:
                    return_obj.total_amount = total
                    db.session.add(return_obj)
                    fixed_returns += 1
            
            if fixed_returns > 0:
                db.session.commit()
                print(f"Updated totals for {fixed_returns} returns")
            
            print("Return subtotal fix completed successfully")
            return True
            
    except Exception as e:
        print(f"Error fixing return subtotals: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run the fix if script is executed directly
if __name__ == "__main__":
    success = fix_return_subtotals()
    if success:
        print("Script completed successfully")
        sys.exit(0)
    else:
        print("Script failed")
        sys.exit(1) 
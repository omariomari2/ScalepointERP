"""
Patch for the return_detail route to ensure correct values are displayed.
"""
from flask import Flask
from app import create_app
from modules.pos.models import POSReturn, POSReturnLine
from extensions import db
import types

def patch_return_detail():
    """Patch the return_detail route to ensure correct values are displayed"""
    try:
        # Import the routes module
        from modules.pos.routes import return_detail, pos
        
        # Define the patched function
        def patched_return_detail(return_id):
            """Patched version of return_detail"""
            from flask import render_template, flash, redirect, url_for
            from modules.pos.models import POSReturn, POSOrder, db
            import traceback
            
            try:
                pos_return = POSReturn.query.get_or_404(return_id)
                
                # Ensure all return lines have valid products
                for line in pos_return.return_lines:
                    if not line.product:
                        print(f"Warning: Return line {line.id} has no associated product (product_id: {line.product_id})")
                
                # Get original order details
                original_order = None
                if pos_return.original_order_id:
                    original_order = POSOrder.query.get(pos_return.original_order_id)
                    
                    if original_order:
                        # Create a dictionary of valid products from the original order
                        valid_product_ids = set()
                        for line in original_order.lines:
                            valid_product_ids.add(line.product_id)
                        
                        # Check for any return lines with products not in the original order
                        for line in pos_return.return_lines:
                            if line.product_id not in valid_product_ids:
                                print(f"Warning: Return line {line.id} has product {line.product_id} which was not in the original order")
                
                # Debug logging for return line values
                print(f"Return line values:")
                for line in pos_return.return_lines:
                    print(f"  Line {line.id}: quantity={line.quantity}, unit_price={line.unit_price}, subtotal={line.subtotal}")
                    # Ensure subtotal is correctly calculated
                    if line.quantity and line.unit_price and (line.subtotal <= 0 or line.subtotal != line.quantity * line.unit_price):
                        line.subtotal = float(line.quantity) * float(line.unit_price)
                        print(f"  Updated subtotal to {line.subtotal}")
                        db.session.add(line)
                
                # Commit any changes
                if db.session.dirty:
                    db.session.commit()
                    print("Committed updates to return lines")
                
                return render_template('pos/return_detail.html', return_=pos_return, original_order=original_order)
            except Exception as e:
                print(f"Error viewing return details: {str(e)}")
                traceback.print_exc()
                flash(f"Error viewing return details: {str(e)}", "danger")
                return redirect(url_for('pos.returns'))
        
        # Replace the original function with our patched version
        pos.view_functions['return_detail'] = patched_return_detail
        
        print("Successfully patched return_detail route")
        return True
    except Exception as e:
        print(f"Error patching return_detail route: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Create the application context
    app = create_app()
    
    # Run the patch within the application context
    with app.app_context():
        if patch_return_detail():
            print("Successfully patched return_detail route")
        else:
            print("Failed to patch return_detail route")

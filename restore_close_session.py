"""
This script restores the close_session function to the modules/pos/routes.py file.
Run this script to fix the missing close_session function.
"""

import os
import re

def restore_close_session():
    # Path to the routes.py file
    routes_file = os.path.join('modules', 'pos', 'routes.py')
    
    # The close_session function code to insert
    close_session_code = '''
@pos.route('/sessions/<int:session_id>/close', methods=['GET', 'POST'])
@login_required
def close_session(session_id):
    session = POSSession.query.get_or_404(session_id)
    
    # Check if user has access to this session
    if session.user_id != current_user.id and not current_user.has_role('Admin'):
        flash('You do not have permission to close this session.', 'danger')
        return redirect(url_for('pos.sessions'))
    
    # Check if session is already closed
    if session.state == 'closed':
        flash('This session is already closed.', 'warning')
        return redirect(url_for('pos.sessions'))
    
    # Get all orders for this session
    orders = POSOrder.query.filter_by(session_id=session_id).all()
    
    # Calculate total sales
    cash_sales = sum(order.total_amount for order in orders if order.payment_method == 'cash')
    card_sales = sum(order.total_amount for order in orders if order.payment_method == 'card')
    mobile_sales = sum(order.total_amount for order in orders if order.payment_method == 'momo')
    other_sales = sum(order.total_amount for order in orders if order.payment_method not in ['cash', 'card', 'momo'])
    
    if request.method == 'POST':
        closing_balance = request.form.get('closing_balance', type=float)
        closing_notes = request.form.get('closing_notes', '')
        
        if closing_balance is None:
            flash('Please enter a valid closing balance.', 'danger')
        else:
            # Close the session
            session.state = 'closed'
            session.end_time = datetime.utcnow()
            session.closing_balance = closing_balance
            session.notes = closing_notes if not session.notes else session.notes + "\\n" + closing_notes
            
            db.session.commit()
            
            flash('Session closed successfully.', 'success')
            
            # Redirect to the sales report
            return redirect(url_for('pos.session_report', session_id=session.id))
    
    return render_template('pos/close_session.html',
                          session=session,
                          cash_sales=cash_sales,
                          card_sales=card_sales,
                          mobile_sales=mobile_sales,
                          other_sales=other_sales,
                          datetime=datetime,
                          title='Close POS Session')
'''
    
    # Read the current content of the file
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # Find the position to insert the close_session function
    # We'll insert it after the new_session function
    pattern = r'def new_session\(\).*?return render_template\(.*?\)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        insert_position = match.end()
        
        # Insert the close_session function
        new_content = content[:insert_position] + '\n\n' + close_session_code + content[insert_position:]
        
        # Write the updated content back to the file
        with open(routes_file, 'w') as f:
            f.write(new_content)
        
        print("Successfully restored the close_session function!")
    else:
        print("Could not find the new_session function in the routes.py file.")

if __name__ == '__main__':
    restore_close_session()

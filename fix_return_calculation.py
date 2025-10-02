"""
Fix Return Calculation

This module provides a simple function to ensure safe calculation of return totals
by handling None values that might cause the error:
"unsupported operand type(s) for +=: 'float' and 'NoneType'"
"""

def safe_calculate_return_total(return_lines):
    """
    Safely calculate the total amount from return lines, handling None values.
    
    Args:
        return_lines: A list or query result of POSReturnLine objects
        
    Returns:
        float: The calculated total
    """
    total = 0.0
    
    if not return_lines:
        return total
    
    for line in return_lines:
        # Handle case where the line object itself is None
        if line is None:
            continue
        
        # Handle case where the subtotal is None
        subtotal = getattr(line, 'subtotal', None)
        if subtotal is not None:
            total += float(subtotal)
        else:
            # If subtotal is None but we have quantity and unit_price, calculate it
            quantity = getattr(line, 'quantity', None)
            unit_price = getattr(line, 'unit_price', None)
            
            if quantity is not None and unit_price is not None:
                line_total = float(quantity) * float(unit_price)
                total += line_total
    
    return total

def update_return_subtotals(pos_return):
    """
    Update a return record's subtotals safely.
    
    Args:
        pos_return: A POSReturn object
        
    Returns:
        bool: True if the return was updated, False otherwise
    """
    if not pos_return:
        return False
    
    try:
        # Calculate the total amount
        total_amount = safe_calculate_return_total(pos_return.return_lines)
        
        # Update the return object
        pos_return.total_amount = total_amount
        
        # If it's not an exchange, also update refund amount
        if pos_return.refund_method != 'exchange':
            pos_return.refund_amount = total_amount
            
        return True
    except Exception as e:
        print(f"Error updating return subtotals: {e}")
        return False 
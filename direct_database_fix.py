"""
Direct database fix for the return quantity and pricing issues.
This script directly updates the database to fix existing returns.
"""
import sqlite3
import os
import sys

# Path to the database file
db_path = 'erp.db'

def fix_returns():
    """Fix all returns in the database directly using SQLite"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Get all return lines
        cursor.execute("SELECT id, return_id, product_id, quantity, unit_price, subtotal FROM pos_return_lines")
        return_lines = cursor.fetchall()
        
        print(f"Found {len(return_lines)} return lines to check")
        
        fixed_count = 0
        
        # Fix each return line
        for line in return_lines:
            line_id, return_id, product_id, quantity, unit_price, subtotal = line
            
            # Calculate the correct subtotal
            correct_subtotal = round(quantity * unit_price, 2)
            
            # Check if the subtotal is incorrect
            if abs(subtotal - correct_subtotal) > 0.01 or subtotal == 0:
                print(f"Fixing line {line_id}: quantity={quantity}, unit_price={unit_price}, subtotal={subtotal} -> {correct_subtotal}")
                
                # Update the subtotal
                cursor.execute(
                    "UPDATE pos_return_lines SET subtotal = ? WHERE id = ?",
                    (correct_subtotal, line_id)
                )
                fixed_count += 1
                
                # If the unit price is zero, try to get it from the original order line
                if unit_price == 0:
                    # Get the original order line ID
                    cursor.execute(
                        "SELECT original_order_line_id FROM pos_return_lines WHERE id = ?",
                        (line_id,)
                    )
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        original_line_id = result[0]
                        
                        # Get the unit price from the original order line
                        cursor.execute(
                            "SELECT unit_price FROM pos_order_lines WHERE id = ?",
                            (original_line_id,)
                        )
                        original_price_result = cursor.fetchone()
                        
                        if original_price_result:
                            original_price = original_price_result[0]
                            
                            # Update the unit price
                            cursor.execute(
                                "UPDATE pos_return_lines SET unit_price = ? WHERE id = ?",
                                (original_price, line_id)
                            )
                            
                            # Recalculate the subtotal
                            new_subtotal = round(quantity * original_price, 2)
                            cursor.execute(
                                "UPDATE pos_return_lines SET subtotal = ? WHERE id = ?",
                                (new_subtotal, line_id)
                            )
                            
                            print(f"  Updated unit price: 0 -> {original_price}")
                            print(f"  Updated subtotal: {correct_subtotal} -> {new_subtotal}")
        
        # Update the return totals
        cursor.execute("""
            UPDATE pos_returns
            SET total_amount = (
                SELECT SUM(subtotal)
                FROM pos_return_lines
                WHERE return_id = pos_returns.id
            )
        """)
        
        # Update the refund amounts to match the total amounts
        cursor.execute("""
            UPDATE pos_returns
            SET refund_amount = total_amount
        """)
        
        # Commit the changes
        conn.commit()
        print(f"Fixed {fixed_count} return lines")
        print("All return totals updated")
        
        # Close the connection
        conn.close()
        print("Database connection closed")
        
        return True
    except Exception as e:
        print(f"Error fixing returns: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_returns()

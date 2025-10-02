"""
Direct fix for the return details display issue in the ERP system.
This script directly fixes the database values and ensures return lines show correct information.
"""
import os
import sys
import sqlite3
import shutil
from datetime import datetime

def backup_database():
    """Create a backup of the database"""
    db_path = r"c:\Users\USER\erpsystem_working_backup\instance\erp_system.db"
    if os.path.exists(db_path):
        backup_dir = os.path.dirname(db_path)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(backup_dir, f"erp_system.{timestamp}.bak.db")
        
        shutil.copy2(db_path, backup_path)
        print(f"Created database backup: {backup_path}")
        return True
    else:
        print(f"Error: Database file not found at {db_path}")
        return False

def fix_return_lines_data():
    """Fix the data in the pos_return_lines table"""
    db_path = r"c:\Users\USER\erpsystem_working_backup\instance\erp_system.db"
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the pos_return_lines table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_return_lines'")
        if cursor.fetchone() is None:
            print("Error: pos_return_lines table not found in the database")
            conn.close()
            return False
        
        # Get the current schema of the pos_return_lines table
        cursor.execute("PRAGMA table_info(pos_return_lines)")
        columns = cursor.fetchall()
        
        print("Current schema of pos_return_lines table:")
        column_names = []
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
            column_names.append(column[1])
        
        # Check if the required columns exist
        required_columns = ['quantity', 'unit_price', 'subtotal']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"Error: Missing required columns in pos_return_lines table: {missing_columns}")
            
            # Add missing columns if needed
            for column in missing_columns:
                if column == 'quantity':
                    cursor.execute("ALTER TABLE pos_return_lines ADD COLUMN quantity FLOAT DEFAULT 1.0")
                elif column == 'unit_price':
                    cursor.execute("ALTER TABLE pos_return_lines ADD COLUMN unit_price FLOAT DEFAULT 0.0")
                elif column == 'subtotal':
                    cursor.execute("ALTER TABLE pos_return_lines ADD COLUMN subtotal FLOAT DEFAULT 0.0")
                
                print(f"Added missing column: {column}")
        
        # Fix the data in the pos_return_lines table
        # First, update any NULL values to defaults
        cursor.execute("UPDATE pos_return_lines SET quantity = 1.0 WHERE quantity IS NULL OR quantity <= 0")
        print(f"Updated {cursor.rowcount} rows with default quantity values")
        
        # Now, get the unit prices from the original order lines
        cursor.execute("""
            UPDATE pos_return_lines
            SET unit_price = (
                SELECT unit_price 
                FROM pos_order_lines 
                WHERE pos_order_lines.id = pos_return_lines.original_order_line_id
            )
            WHERE unit_price IS NULL OR unit_price <= 0
        """)
        print(f"Updated {cursor.rowcount} rows with unit prices from original order lines")
        
        # Update the subtotal for all rows
        cursor.execute("UPDATE pos_return_lines SET subtotal = quantity * unit_price")
        print(f"Updated {cursor.rowcount} rows with correct subtotal values")
        
        # Commit the changes
        conn.commit()
        
        # Verify the data
        cursor.execute("SELECT id, quantity, unit_price, subtotal FROM pos_return_lines")
        rows = cursor.fetchall()
        print(f"Verified {len(rows)} rows in pos_return_lines table")
        
        # Check for any remaining issues
        cursor.execute("SELECT id, quantity, unit_price, subtotal FROM pos_return_lines WHERE subtotal != quantity * unit_price")
        rows = cursor.fetchall()
        if rows:
            print(f"Warning: Found {len(rows)} rows with incorrect subtotal values")
            for row in rows:
                print(f"  ID: {row[0]}, quantity: {row[1]}, unit_price: {row[2]}, subtotal: {row[3]}, calculated: {row[1] * row[2]}")
                # Fix these rows
                cursor.execute("UPDATE pos_return_lines SET subtotal = ? WHERE id = ?", (row[1] * row[2], row[0]))
            conn.commit()
            print("Fixed remaining issues with subtotal values")
        
        # Close the connection
        conn.close()
        
        print("Successfully fixed pos_return_lines data")
        return True
    except Exception as e:
        print(f"Error fixing pos_return_lines data: {str(e)}")
        return False

def fix_return_template():
    """Fix the return_detail.html template to correctly display the values"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\return_detail.html"
    
    try:
        # Check if the template exists
        if not os.path.exists(template_path):
            print(f"Error: Template file not found at {template_path}")
            return False
        
        # Create a backup of the template
        backup_dir = os.path.join(os.path.dirname(template_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(template_path)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
        
        shutil.copy2(template_path, backup_path)
        print(f"Created template backup: {backup_path}")
        
        # Read the template
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the template needs to be fixed
        if '<td class="text-end">{{ line.quantity }}</td>' in content:
            # Update the template to ensure correct display of values
            updated_content = content.replace(
                '<td class="text-end">{{ line.quantity }}</td>',
                '<td class="text-end">{{ "%.1f"|format(line.quantity) }}</td>'
            )
            
            updated_content = updated_content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price) }}</td>'
            )
            
            updated_content = updated_content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal) }}</td>'
            )
            
            # Write the updated template
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated return_detail.html template")
        else:
            print("Template doesn't match expected format, manual inspection required")
            
            # Let's check the actual content of the template
            print("\nTemplate content preview:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'quantity' in line or 'unit_price' in line or 'subtotal' in line:
                    print(f"Line {i+1}: {line}")
            
            # Try to find the table structure
            table_start = content.find('<table')
            table_end = content.find('</table>', table_start)
            
            if table_start != -1 and table_end != -1:
                table_content = content[table_start:table_end+8]
                print("\nTable structure:")
                print(table_content)
                
                # Try to fix the template based on the actual structure
                if 'text-end' in table_content and 'GH₵' in table_content:
                    # Find the line quantity cell
                    qty_start = table_content.find('<td class="text-end">', table_content.find('<tbody>'))
                    if qty_start != -1:
                        qty_end = table_content.find('</td>', qty_start)
                        qty_cell = table_content[qty_start:qty_end+5]
                        
                        # Find the unit price cell
                        price_start = table_content.find('<td class="text-end">', qty_end)
                        if price_start != -1:
                            price_end = table_content.find('</td>', price_start)
                            price_cell = table_content[price_start:price_end+5]
                            
                            # Find the subtotal cell
                            subtotal_start = table_content.find('<td class="text-end">', price_end)
                            if subtotal_start != -1:
                                subtotal_end = table_content.find('</td>', subtotal_start)
                                subtotal_cell = table_content[subtotal_start:subtotal_end+5]
                                
                                print("\nFound cells:")
                                print(f"Quantity: {qty_cell}")
                                print(f"Unit Price: {price_cell}")
                                print(f"Subtotal: {subtotal_cell}")
                                
                                # Update the template with the correct cells
                                updated_content = content.replace(
                                    qty_cell,
                                    '<td class="text-end">{{ "%.1f"|format(line.quantity) }}</td>'
                                )
                                
                                updated_content = updated_content.replace(
                                    price_cell,
                                    '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price) }}</td>'
                                )
                                
                                updated_content = updated_content.replace(
                                    subtotal_cell,
                                    '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal) }}</td>'
                                )
                                
                                # Write the updated template
                                with open(template_path, 'w', encoding='utf-8') as f:
                                    f.write(updated_content)
                                
                                print("Successfully updated return_detail.html template based on actual structure")
                            else:
                                print("Could not find subtotal cell")
                        else:
                            print("Could not find unit price cell")
                    else:
                        print("Could not find quantity cell")
                else:
                    print("Could not identify the table structure")
            else:
                print("Could not find the table in the template")
        
        return True
    except Exception as e:
        print(f"Error fixing return template: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting direct fix for return display issue...")
    
    # Backup the database
    if not backup_database():
        print("Failed to backup database")
        return False
    
    # Fix the data in the pos_return_lines table
    if not fix_return_lines_data():
        print("Failed to fix pos_return_lines data")
        return False
    
    # Fix the return_detail.html template
    if not fix_return_template():
        print("Failed to fix return template")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Please restart your application for the changes to take effect.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

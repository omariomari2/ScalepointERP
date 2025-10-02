"""
Fix for the partial return form to ensure correct prices are submitted.
This script fixes the issue where the price is being set to 0 in the form submission.
"""
import os
import sys
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the specified file"""
    if os.path.exists(file_path):
        backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
        
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
        return True
    else:
        print(f"Error: File not found at {file_path}")
        return False

def fix_partial_return_route():
    """Fix the partial_return route to ensure correct prices are used"""
    routes_path = r"c:\Users\USER\erpsystem_working_backup\modules\pos\routes.py"
    
    if not backup_file(routes_path):
        return False
    
    try:
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where form data is processed in the partial_return function
        if "# Process form data for partial return" in content:
            # Add debug logging for the form data
            updated_content = content.replace(
                "# Process form data for partial return",
                """# Process form data for partial return
            print("==== RETURN FORM SUBMISSION DEBUG ====")
            print("All form data:")
            for key, value in request.form.items():
                print(f"  {key}: {value}")"""
            )
            
            # Fix the price handling in the partial_return function
            if "price = float(request.form.getlist('price[]')[i]) if i < len(request.form.getlist('price[]')) else 0" in updated_content:
                # The price handling code already exists, but might not be working correctly
                # Let's enhance it to ensure it gets the correct price from the original order line if needed
                updated_content = updated_content.replace(
                    "price = float(request.form.getlist('price[]')[i]) if i < len(request.form.getlist('price[]')) else 0",
                    """# Get price from form or original order line
                price = 0
                if i < len(request.form.getlist('price[]')) and request.form.getlist('price[]')[i]:
                    try:
                        price = float(request.form.getlist('price[]')[i])
                    except (ValueError, TypeError):
                        price = 0
                
                # If price is still 0, try to get it from the original order line
                if price <= 0 and original_line_id:
                    original_line = POSOrderLine.query.get(original_line_id)
                    if original_line:
                        price = original_line.unit_price
                        print(f"Retrieved price {price} from original order line {original_line_id}")"""
                )
            else:
                # If the price handling code doesn't exist, we need to find where the return line is created
                if "return_line = POSReturnLine(" in updated_content:
                    # Find the section where the return line is created
                    return_line_section = updated_content.find("return_line = POSReturnLine(")
                    price_section = updated_content.find("price = ", max(0, return_line_section - 500), return_line_section)
                    
                    if price_section > 0:
                        # Find the end of the price line
                        price_line_end = updated_content.find("\n", price_section)
                        price_line = updated_content[price_section:price_line_end]
                        
                        # Replace the price line with our enhanced version
                        updated_content = updated_content.replace(
                            price_line,
                            """# Get price from form or original order line
                price = 0
                if i < len(request.form.getlist('price[]')) and request.form.getlist('price[]')[i]:
                    try:
                        price = float(request.form.getlist('price[]')[i])
                    except (ValueError, TypeError):
                        price = 0
                
                # If price is still 0, try to get it from the original order line
                if price <= 0 and original_line_id:
                    original_line = POSOrderLine.query.get(original_line_id)
                    if original_line:
                        price = original_line.unit_price
                        print(f"Retrieved price {price} from original order line {original_line_id}")"""
                        )
            
            # Ensure the subtotal is calculated correctly
            if "line_subtotal = price * quantity" not in updated_content:
                # Find the section where the return line is created
                return_line_section = updated_content.find("return_line = POSReturnLine(")
                
                if return_line_section > 0:
                    # Find the line before the return line creation
                    prev_line_end = updated_content.rfind("\n", 0, return_line_section)
                    
                    # Insert the subtotal calculation before the return line creation
                    updated_content = updated_content[:prev_line_end] + "\n                # Calculate subtotal\n                line_subtotal = price * quantity" + updated_content[prev_line_end:]
            
            # Ensure the subtotal is set in the return line
            if "subtotal=line_subtotal" not in updated_content:
                # Find the return line creation
                return_line_section = updated_content.find("return_line = POSReturnLine(")
                unit_price_section = updated_content.find("unit_price=price", return_line_section)
                
                if unit_price_section > 0:
                    # Find the end of the unit_price line
                    unit_price_line_end = updated_content.find(",", unit_price_section)
                    
                    # Insert the subtotal after the unit_price
                    updated_content = updated_content[:unit_price_line_end + 1] + "\n                    subtotal=line_subtotal" + updated_content[unit_price_line_end + 1:]
            
            # Add debug logging for the return line creation
            if "print(f\"Creating return line for product {product_id} with quantity {quantity}\")" in updated_content:
                updated_content = updated_content.replace(
                    "print(f\"Creating return line for product {product_id} with quantity {quantity}\")",
                    "print(f\"Creating return line for product {product_id} with quantity {quantity}, price {price}, subtotal {line_subtotal}\")"
                )
            
            with open(routes_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated partial_return route to ensure correct prices are used")
        else:
            print("Could not find the expected section in routes.py")
            return False
        
        return True
    except Exception as e:
        print(f"Error fixing partial_return route: {str(e)}")
        return False

def fix_return_detail_route():
    """Fix the return_detail route to ensure correct values are displayed"""
    routes_path = r"c:\Users\USER\erpsystem_working_backup\modules\pos\routes.py"
    
    try:
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the return_detail function
        if "@pos.route('/returns/<int:return_id>')" in content:
            # Find the section where the template is rendered
            render_template_section = content.find("return render_template('pos/return_detail.html'", content.find("def return_detail(return_id):"))
            
            if render_template_section > 0:
                # Find the line before the template rendering
                prev_line_end = content.rfind("\n", 0, render_template_section)
                
                # Add code to fix return line values before rendering the template
                fix_code = """
        # Fix return line values before rendering
        for line in pos_return.return_lines:
            # Debug log the line values
            print(f"Return line {line.id}: quantity={line.quantity}, unit_price={line.unit_price}, subtotal={line.subtotal}")
            
            # If unit price is 0, try to get it from the original order line
            if line.unit_price <= 0 and line.original_order_line_id:
                original_line = POSOrderLine.query.get(line.original_order_line_id)
                if original_line:
                    line.unit_price = original_line.unit_price
                    print(f"Updated line {line.id} unit price to {line.unit_price} from original order line")
                    db.session.add(line)
            
            # Ensure subtotal is correctly calculated
            correct_subtotal = float(line.quantity) * float(line.unit_price)
            if line.subtotal <= 0 or abs(line.subtotal - correct_subtotal) > 0.01:
                line.subtotal = correct_subtotal
                print(f"Updated line {line.id} subtotal to {line.subtotal}")
                db.session.add(line)
        
        # Commit any changes
        if db.session.dirty:
            db.session.commit()
            print("Committed updates to return lines")
"""
                
                # Insert the fix code before the template rendering
                updated_content = content[:prev_line_end] + fix_code + content[prev_line_end:]
                
                with open(routes_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print("Successfully updated return_detail route to ensure correct values are displayed")
            else:
                print("Could not find the template rendering in return_detail function")
                return False
        else:
            print("Could not find the return_detail function in routes.py")
            return False
        
        return True
    except Exception as e:
        print(f"Error fixing return_detail route: {str(e)}")
        return False

def fix_return_detail_template():
    """Fix the return_detail.html template to correctly display values"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\return_detail.html"
    
    if not backup_file(template_path):
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the table row for return lines
        if '<td class="text-end">{{ line.quantity }}</td>' in content:
            # Replace the quantity, unit price, and subtotal cells
            updated_content = content.replace(
                '<td class="text-end">{{ line.quantity }}</td>',
                '<td class="text-end">{{ "%.1f"|format(line.quantity|float) }}</td>'
            )
            
            updated_content = updated_content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price|float) }}</td>'
            )
            
            updated_content = updated_content.replace(
                '<td class="text-end">GH₵{{ "%.2f"|format(line.quantity * line.unit_price) }}</td>',
                '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal|float) }}</td>'
            )
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully updated return_detail.html template")
        else:
            # Try to find the table structure using a more general approach
            table_section = content.find('<table class="table">')
            if table_section > 0:
                # Find the table body
                tbody_section = content.find('<tbody>', table_section)
                if tbody_section > 0:
                    # Find the first row in the table body
                    tr_section = content.find('<tr>', tbody_section)
                    if tr_section > 0:
                        # Find the quantity, unit price, and subtotal cells
                        td_sections = []
                        start_pos = tr_section
                        for _ in range(7):  # Assuming there are 7 cells in the row
                            td_start = content.find('<td', start_pos)
                            if td_start > 0:
                                td_end = content.find('</td>', td_start)
                                if td_end > 0:
                                    td_sections.append((td_start, td_end + 5))
                                    start_pos = td_end + 5
                        
                        if len(td_sections) >= 4:  # We need at least 4 cells (product, quantity, price, subtotal)
                            # Get the quantity, unit price, and subtotal cells
                            quantity_cell = content[td_sections[1][0]:td_sections[1][1]]
                            unit_price_cell = content[td_sections[2][0]:td_sections[2][1]]
                            subtotal_cell = content[td_sections[3][0]:td_sections[3][1]]
                            
                            # Create the updated cells
                            updated_quantity_cell = '<td class="text-end">{{ "%.1f"|format(line.quantity|float) }}</td>'
                            updated_unit_price_cell = '<td class="text-end">GH₵{{ "%.2f"|format(line.unit_price|float) }}</td>'
                            updated_subtotal_cell = '<td class="text-end">GH₵{{ "%.2f"|format(line.subtotal|float) }}</td>'
                            
                            # Replace the cells in the content
                            updated_content = content.replace(quantity_cell, updated_quantity_cell)
                            updated_content = updated_content.replace(unit_price_cell, updated_unit_price_cell)
                            updated_content = updated_content.replace(subtotal_cell, updated_subtotal_cell)
                            
                            with open(template_path, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            
                            print("Successfully updated return_detail.html template using general approach")
                        else:
                            print("Could not find all required cells in the table row")
                            return False
                    else:
                        print("Could not find table row in the table body")
                        return False
                else:
                    print("Could not find table body in the table")
                    return False
            else:
                print("Could not find table in the template")
                return False
        
        return True
    except Exception as e:
        print(f"Error fixing return_detail template: {str(e)}")
        return False

def fix_partial_return_form():
    """Fix the partial_return_form.html template to ensure prices are correctly submitted"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\partial_return_form.html"
    
    if not backup_file(template_path):
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where the product selection changes
        if "// Product selection change" in content:
            # Find the section where the price is updated
            price_update_section = content.find("// Update price", content.find("// Product selection change"))
            
            if price_update_section > 0:
                # Find the end of the price update section
                price_update_end = content.find("}", price_update_section)
                
                # Get the price update code
                price_update_code = content[price_update_section:price_update_end]
                
                # Check if the price is being set correctly
                if "priceInput.value = productData.price.toFixed(2);" in price_update_code:
                    # Add additional code to ensure the price is set correctly
                    updated_price_code = price_update_code.replace(
                        "priceInput.value = productData.price.toFixed(2);",
                        """priceInput.value = productData.price.toFixed(2);
                        console.log('Setting price to', productData.price.toFixed(2));
                        // Ensure the price is set as a number, not a string
                        priceInput.valueAsNumber = parseFloat(productData.price.toFixed(2));"""
                    )
                    
                    # Replace the price update code
                    updated_content = content.replace(price_update_code, updated_price_code)
                    
                    # Find the form submission section
                    form_submit_section = updated_content.find("// Form submission", price_update_end)
                    
                    if form_submit_section > 0:
                        # Add code to ensure prices are included in the form submission
                        form_submit_code = """
        // Form submission
        document.getElementById('returnForm').addEventListener('submit', function(e) {
            // Debug log all form data before submission
            console.log('Form submission:');
            const formData = new FormData(this);
            for (const [key, value] of formData.entries()) {
                console.log(`  ${key}: ${value}`);
            }
            
            // Ensure all prices are included
            const priceInputs = document.querySelectorAll('.price-input');
            priceInputs.forEach((input, index) => {
                if (!input.value || parseFloat(input.value) <= 0) {
                    // Try to get the price from the product select
                    const line = input.closest('.return-line');
                    const productSelect = line.querySelector('.product-select');
                    if (productSelect && productSelect.selectedIndex > 0) {
                        const productData = JSON.parse(productSelect.options[productSelect.selectedIndex].dataset.product || '{}');
                        if (productData.price) {
                            input.value = productData.price.toFixed(2);
                            console.log(`Set price for line ${index} to ${input.value}`);
                        }
                    }
                }
            });
            
            // Continue with form submission
        });
        """
                        
                        # Check if the form submission code already exists
                        if "// Form submission" in updated_content:
                            # Replace the existing form submission code
                            updated_content = updated_content.replace(
                                updated_content[form_submit_section:updated_content.find("});", form_submit_section) + 3],
                                form_submit_code
                            )
                        else:
                            # Add the form submission code before the script end
                            script_end = updated_content.rfind("</script>")
                            updated_content = updated_content[:script_end] + form_submit_code + updated_content[script_end:]
                    
                    with open(template_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    print("Successfully updated partial_return_form.html template")
                else:
                    print("Could not find the price update code in the template")
                    return False
            else:
                print("Could not find the price update section in the template")
                return False
        else:
            print("Could not find the product selection change section in the template")
            return False
        
        return True
    except Exception as e:
        print(f"Error fixing partial_return_form template: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting fix for partial return form...")
    
    # Fix the partial_return route
    if not fix_partial_return_route():
        print("Failed to fix partial_return route")
        return False
    
    # Fix the return_detail route
    if not fix_return_detail_route():
        print("Failed to fix return_detail route")
        return False
    
    # Fix the return_detail.html template
    if not fix_return_detail_template():
        print("Failed to fix return_detail template")
        return False
    
    # Fix the partial_return_form.html template
    if not fix_partial_return_form():
        print("Failed to fix partial_return_form template")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Please restart your application for the changes to take effect.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

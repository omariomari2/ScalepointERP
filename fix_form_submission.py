"""
Fix for the form submission issue in the partial return functionality.
This script ensures that the correct price is passed from the form to the server.
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

def fix_partial_return_form():
    """Fix the partial_return_form.html template to ensure prices are correctly submitted"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\partial_return_form.html"
    
    if not backup_file(template_path):
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add form submission handler to ensure prices are included
        if "</script>" in content and "document.getElementById('returnForm').addEventListener('submit'" not in content:
            # Add the form submission handler before the closing script tag
            form_submit_handler = """
        // Form submission handler to ensure prices are correctly submitted
        document.getElementById('returnForm').addEventListener('submit', function(e) {
            // Prevent the default form submission
            e.preventDefault();
            
            // Debug log all form data before submission
            console.log('Form submission - before fixes:');
            const formData = new FormData(this);
            for (const [key, value] of formData.entries()) {
                console.log(`  ${key}: ${value}`);
            }
            
            // Ensure all prices are included and correct
            const priceInputs = document.querySelectorAll('.price-input');
            const productSelects = document.querySelectorAll('.product-select');
            
            priceInputs.forEach((input, index) => {
                // Skip the template
                if (input.closest('#line-template')) {
                    return;
                }
                
                // Check if price is missing or zero
                if (!input.value || parseFloat(input.value) <= 0) {
                    const line = input.closest('.return-line');
                    const productSelect = line.querySelector('.product-select');
                    
                    if (productSelect && productSelect.selectedIndex > 0) {
                        try {
                            // Get product data from the data attribute
                            const productData = JSON.parse(productSelect.options[productSelect.selectedIndex].dataset.product || '{}');
                            
                            if (productData.price) {
                                // Set the price value
                                input.value = productData.price.toFixed(2);
                                console.log(`Set price for line ${index} to ${input.value}`);
                            } else {
                                console.log(`No price data found for product at index ${index}`);
                            }
                        } catch (error) {
                            console.error(`Error parsing product data for line ${index}:`, error);
                        }
                    }
                }
            });
            
            // Log the updated form data
            console.log('Form submission - after fixes:');
            const updatedFormData = new FormData(this);
            for (const [key, value] of updatedFormData.entries()) {
                console.log(`  ${key}: ${value}`);
            }
            
            // Continue with form submission
            this.submit();
        });
        """
            
            # Insert the form submission handler before the closing script tag
            updated_content = content.replace("</script>", form_submit_handler + "\n    </script>")
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully added form submission handler to partial_return_form.html")
        else:
            print("Form submission handler already exists or script tag not found")
        
        return True
    except Exception as e:
        print(f"Error fixing partial_return_form.html: {str(e)}")
        return False

def fix_product_selection_handler():
    """Fix the product selection handler in the partial_return_form.html template"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\partial_return_form.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the product selection handler
        product_selection_start = content.find("productSelect.addEventListener('change'")
        if product_selection_start == -1:
            print("Could not find product selection handler")
            return False
        
        # Find the section where the price is updated
        price_update_start = content.find("// Update price", product_selection_start)
        if price_update_start == -1:
            print("Could not find price update section")
            return False
        
        # Find the end of the price update section
        price_update_end = content.find("}", price_update_start)
        if price_update_end == -1:
            print("Could not find end of price update section")
            return False
        
        # Get the current price update code
        current_price_code = content[price_update_start:price_update_end + 1]
        
        # Check if the price update code needs to be fixed
        if "priceInput.value = productData.price.toFixed(2);" in current_price_code:
            # Create the updated price update code
            updated_price_code = """                    // Update price
                    if (priceInput && productData.price) {
                        // Set the price value and ensure it's a number
                        priceInput.value = productData.price.toFixed(2);
                        console.log(`Setting price to ${productData.price.toFixed(2)} for product ${productId}`);
                        
                        // Ensure the price input has the correct name attribute
                        priceInput.name = 'price[]';
                        
                        // Force a change event to ensure the price is registered
                        const event = new Event('change', { bubbles: true });
                        priceInput.dispatchEvent(event);
                    }
                    """
            
            # Replace the price update code
            updated_content = content.replace(current_price_code, updated_price_code)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully fixed product selection handler")
        else:
            print("Price update code already fixed or not in expected format")
        
        return True
    except Exception as e:
        print(f"Error fixing product selection handler: {str(e)}")
        return False

def fix_new_partial_return():
    """Fix the price handling in new_partial_return.py"""
    file_path = r"c:\Users\USER\erpsystem_working_backup\new_partial_return.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add debug logging for the form data
        if "# Get form data" in content and "print(\"All form data:\")" not in content:
            updated_content = content.replace(
                "# Get form data",
                """# Get form data
            # Debug log all form data
            print("==== PARTIAL RETURN FORM SUBMISSION DEBUG ====")
            print("All form data:")
            for key, value in request.form.items():
                print(f"  {key}: {value}")"""
            )
            
            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully added debug logging to new_partial_return.py")
        else:
            print("Debug logging already exists or section not found")
        
        # Now fix the price handling in the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where the price is processed
        price_section_start = content.find("# Process price with proper validation")
        if price_section_start == -1:
            print("Could not find price processing section")
            return False
        
        # Find the end of the price processing section
        price_section_end = content.find("# If price is still 0", price_section_start)
        if price_section_end == -1:
            print("Could not find end of price processing section")
            return False
        
        # Get the current price processing code
        current_price_code = content[price_section_start:price_section_end]
        
        # Create the updated price processing code with more robust handling
        updated_price_code = """# Process price with proper validation
                price = 0.0  # Default to 0 if invalid
                if i < len(prices):
                    price_str = prices[i]
                    if price_str and price_str != 'undefined':
                        try:
                            price = float(price_str)
                            print(f"Successfully parsed price from form: {price}")
                        except (ValueError, TypeError):
                            print(f"Invalid price: {price_str}, using default of 0.0")
                    else:
                        print(f"Empty or undefined price at index {i}")
                else:
                    print(f"No price found at index {i}")
                """
        
        # Replace the price processing code
        updated_content = content.replace(current_price_code, updated_price_code)
        
        # Make sure the original order line price retrieval is working correctly
        if "# If price is still 0, try to get it from the original order line" in updated_content:
            original_line_section_start = updated_content.find("# If price is still 0, try to get it from the original order line")
            original_line_section_end = updated_content.find("# If price is still 0, try to get it from the valid_products dictionary", original_line_section_start)
            
            if original_line_section_end > original_line_section_start:
                current_original_line_code = updated_content[original_line_section_start:original_line_section_end]
                
                updated_original_line_code = """# If price is still 0, try to get it from the original order line
                if price <= 0 and original_line_id:
                    try:
                        original_line = POSOrderLine.query.get(original_line_id)
                        if original_line and original_line.unit_price > 0:
                            price = original_line.unit_price
                            print(f"Using price {price} from original order line {original_line_id}")
                        else:
                            print(f"Original order line {original_line_id} not found or has zero price")
                    except Exception as e:
                        print(f"Error getting price from original order line: {str(e)}")
                """
                
                updated_content = updated_content.replace(current_original_line_code, updated_original_line_code)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Successfully fixed price handling in new_partial_return.py")
        return True
    except Exception as e:
        print(f"Error fixing new_partial_return.py: {str(e)}")
        return False

def create_api_endpoint_for_order_lines():
    """Create an API endpoint to get order line details"""
    file_path = r"c:\Users\USER\erpsystem_working_backup\new_partial_return.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the API endpoint already exists
        if "@partial_return_bp.route('/api/order_line/<int:line_id>')" not in content:
            # Find the end of the file
            file_end = content.rfind("return True")
            if file_end == -1:
                print("Could not find end of file")
                return False
            
            # Create the API endpoint
            api_endpoint = """

@partial_return_bp.route('/api/order_line/<int:line_id>', methods=['GET'])
@login_required
def get_order_line(line_id):
    \"\"\"API endpoint to get order line details\"\"\"
    try:
        # Get the order line
        order_line = POSOrderLine.query.get_or_404(line_id)
        
        # Return the order line details
        return jsonify({
            'success': True,
            'line': {
                'id': order_line.id,
                'product_id': order_line.product_id,
                'quantity': order_line.quantity,
                'unit_price': order_line.unit_price,
                'subtotal': order_line.subtotal,
                'returned_quantity': order_line.returned_quantity
            }
        })
    except Exception as e:
        print(f"Error getting order line details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error getting order line details: {str(e)}"
        })
"""
            
            # Add the API endpoint to the file
            updated_content = content[:file_end + 10] + api_endpoint + content[file_end + 10:]
            
            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("Successfully added API endpoint for order lines")
        else:
            print("API endpoint already exists")
        
        return True
    except Exception as e:
        print(f"Error creating API endpoint: {str(e)}")
        return False

def update_partial_return_form_to_fetch_prices():
    """Update the partial_return_form.html template to fetch prices from the API"""
    template_path = r"c:\Users\USER\erpsystem_working_backup\templates\pos\partial_return_form.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the section where the original line ID is set
        original_line_section_start = content.find("// Set original line ID if available")
        if original_line_section_start == -1:
            print("Could not find original line ID section")
            return False
        
        # Find the end of the original line ID section
        original_line_section_end = content.find("}", original_line_section_start)
        if original_line_section_end == -1:
            print("Could not find end of original line ID section")
            return False
        
        # Get the current original line ID code
        current_original_line_code = content[original_line_section_start:original_line_section_end + 1]
        
        # Create the updated original line ID code with price fetching
        updated_original_line_code = """                    // Set original line ID if available
                    if (originalLineInput && productData.line_id) {
                        originalLineInput.value = productData.line_id;
                        originalLineInput.name = 'original_line_id[]';
                        
                        // Fetch the original order line details to get the price
                        fetch(`/pos/returns/api/order_line/${productData.line_id}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.success && data.line && data.line.unit_price > 0) {
                                    // Update the price input with the original line price
                                    if (priceInput) {
                                        priceInput.value = data.line.unit_price.toFixed(2);
                                        console.log(`Updated price to ${data.line.unit_price.toFixed(2)} from original order line ${productData.line_id}`);
                                        
                                        // Force a change event to ensure the price is registered
                                        const event = new Event('change', { bubbles: true });
                                        priceInput.dispatchEvent(event);
                                        
                                        // Update totals
                                        updateTotals();
                                    }
                                }
                            })
                            .catch(error => {
                                console.error('Error fetching order line details:', error);
                            });
                    }
                    """
        
        # Replace the original line ID code
        updated_content = content.replace(current_original_line_code, updated_original_line_code)
        
        # Write the updated content back to the file
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Successfully updated partial_return_form.html to fetch prices from the API")
        return True
    except Exception as e:
        print(f"Error updating partial_return_form.html: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    print("Starting fix for form submission issue...")
    
    # Fix the partial_return_form.html template
    if not fix_partial_return_form():
        print("Failed to fix partial_return_form.html")
        return False
    
    # Fix the product selection handler
    if not fix_product_selection_handler():
        print("Failed to fix product selection handler")
        return False
    
    # Fix the new_partial_return.py file
    if not fix_new_partial_return():
        print("Failed to fix new_partial_return.py")
        return False
    
    # Create the API endpoint for order lines
    if not create_api_endpoint_for_order_lines():
        print("Failed to create API endpoint for order lines")
        return False
    
    # Update the partial_return_form.html template to fetch prices from the API
    if not update_partial_return_form_to_fetch_prices():
        print("Failed to update partial_return_form.html to fetch prices from the API")
        return False
    
    print("\nAll fixes applied successfully!")
    print("Please restart your application for the changes to take effect.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

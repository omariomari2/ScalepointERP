from app import create_app
from modules.inventory.models import Product, Category
from modules.inventory.models_warehouse import WarehouseProduct
from flask import Flask
import pandas as pd
import os
from sqlalchemy import text

app = create_app()

def fix_categories_from_excel(excel_path):
    """
    Fix categories for existing products based on an Excel file
    """
    print(f"Reading Excel file: {excel_path}")
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        print(f"Excel columns: {df.columns.tolist()}")
        
        # Map the actual column names to expected names
        # Based on the Excel columns we found: ['Code', 'Name', 'Cost Price', 'Sales Price', 'Quantity on Hand', 'Warehouse', 'POS Category', 'Category', 'Available in POS']
        sku_column = 'Code'  # Assuming 'Code' is the SKU
        category_column = 'Category'  # This seems to be correct
        
        # Check if required columns exist
        if sku_column not in df.columns or category_column not in df.columns:
            print(f"Error: Excel file must contain '{sku_column}' and '{category_column}' columns")
            print(f"Available columns: {df.columns.tolist()}")
            return
        
        with app.app_context():
            # Get all categories
            categories = Category.query.all()
            category_map = {cat.name.lower(): cat for cat in categories}
            print(f"Found {len(categories)} categories in database")
            
            # Process each row
            updated = 0
            not_found = 0
            already_set = 0
            category_not_found = 0
            
            for _, row in df.iterrows():
                sku = str(row[sku_column]).strip() if pd.notna(row[sku_column]) else None
                category_name = str(row[category_column]).strip() if pd.notna(row[category_column]) else None
                
                if not sku or not category_name:
                    continue
                
                # Find product by SKU
                product = Product.query.filter_by(sku=sku).first()
                if not product:
                    print(f"Product with SKU '{sku}' not found")
                    not_found += 1
                    continue
                
                # Find category (case insensitive)
                category = None
                category_key = category_name.lower()
                if category_key in category_map:
                    category = category_map[category_key]
                
                if not category:
                    print(f"Category '{category_name}' not found for product '{sku}'")
                    category_not_found += 1
                    continue
                
                # Update product category
                if product.category_id == category.id:
                    print(f"Product '{sku}' already has category '{category.name}'")
                    already_set += 1
                else:
                    old_category = product.category.name if product.category else "None"
                    product.category_id = category.id
                    print(f"Updated product '{sku}' category from '{old_category}' to '{category.name}'")
                    updated += 1
            
            # Commit changes
            if updated > 0:
                from app import db
                db.session.commit()
                print(f"Committed {updated} category updates")
            
            # Print summary
            print("\nSummary:")
            print(f"- Products updated: {updated}")
            print(f"- Products already set: {already_set}")
            print(f"- Products not found: {not_found}")
            print(f"- Categories not found: {category_not_found}")
            
            # Verify results
            print("\nVerifying results...")
            products_with_categories = Product.query.filter(Product.category_id.isnot(None)).count()
            total_products = Product.query.count()
            print(f"Products with categories: {products_with_categories}/{total_products}")
            
            # Run a SQL query to check category assignments
            from app import db
            result = db.session.execute(text("""
                SELECT c.name as category_name, COUNT(p.id) as product_count
                FROM products p
                JOIN product_categories c ON p.category_id = c.id
                GROUP BY c.name
                ORDER BY product_count DESC
            """))
            
            print("\nCategory distribution:")
            for row in result:
                print(f"- {row.category_name}: {row.product_count} products")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check if the Excel file exists in the uploads/temp directory
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'temp')
    excel_files = [f for f in os.listdir(temp_dir) if f.endswith('.xlsx')]
    
    if excel_files:
        # Use the most recent Excel file
        excel_files.sort(key=lambda x: os.path.getmtime(os.path.join(temp_dir, x)), reverse=True)
        latest_file = excel_files[0]
        excel_path = os.path.join(temp_dir, latest_file)
        print(f"Using most recent Excel file: {latest_file}")
        fix_categories_from_excel(excel_path)
    else:
        print("No Excel files found in the uploads/temp directory")

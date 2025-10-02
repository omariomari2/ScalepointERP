"""
This file contains the implementation for adding a category column to the warehouse transfers report.
It includes all the necessary changes to ensure the category is displayed correctly in both the HTML report and Excel export.

Instructions:
1. Update the query in get_warehouse_transfers_data to join with the Category model
2. Update all processing functions (daily, weekly, monthly, quarterly) to include the category information
3. Update the Excel export function to include the category column
4. Update the HTML report template to display the category column

This file is for reference only and should not be executed directly.
"""

# 1. Update imports to include Category model
from modules.inventory.models import Product, StockLocation, Warehouse, StockMove, Category
from modules.inventory.models_warehouse import WarehouseProduct, WarehouseMovement

# 2. Update the query in get_warehouse_transfers_data to join with the Category model
def get_warehouse_transfers_data(start_date, end_date, granularity='weekly'):
    """Get warehouse transfers data based on date range and granularity"""
    # Use aliases for the User table to avoid ambiguous column names
    creator_alias = db.aliased(User)
    approver_alias = db.aliased(User)
    source_location_alias = db.aliased(StockLocation)
    dest_location_alias = db.aliased(StockLocation)
    
    query = db.session.query(
        StockMove,
        Product,
        creator_alias.username.label('inventory_manager'),
        approver_alias.username.label('shop_manager'),
        Category.name.label('category_name')
    ).join(
        Product, StockMove.product_id == Product.id
    ).outerjoin(
        Category, Product.category_id == Category.id
    ).join(
        creator_alias, StockMove.created_by_id == creator_alias.id, isouter=True
    ).join(
        approver_alias, StockMove.approved_by_id == approver_alias.id, isouter=True
    ).join(
        source_location_alias, StockMove.source_location_id == source_location_alias.id
    ).join(
        dest_location_alias, StockMove.destination_location_id == dest_location_alias.id
    )
    
    # Filter for completed transfers (state='done') from warehouse to shop
    query = query.filter(
        StockMove.created_at.between(start_date, end_date),
        StockMove.state == 'done',
        source_location_alias.warehouse_id.isnot(None),  # Source is a warehouse location
        dest_location_alias.warehouse_id.is_(None)  # Destination is not a warehouse location (i.e., shop)
    )
    
    # Execute query
    transfers = query.all()
    
    # Process data based on granularity
    if granularity == 'daily':
        return process_daily_transfers(transfers, start_date, end_date)
    elif granularity == 'weekly':
        return process_weekly_transfers(transfers, start_date, end_date)
    elif granularity == 'monthly':
        return process_monthly_transfers(transfers, start_date, end_date)
    else:
        return process_quarterly_transfers(transfers, start_date, end_date)

# 3. Update the process_daily_transfers function to include the category information
def process_daily_transfers(transfers, start_date, end_date):
    """Process warehouse transfers data by day"""
    # Create a dictionary to store product quantities by day
    product_quantities = {}
    
    # Create a list of all days in the date range
    days = []
    current_date = start_date
    while current_date <= end_date:
        days.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Get warehouse starting quantities at start date
    warehouse_starting_quantities = get_warehouse_starting_quantities(start_date)
    
    # Process each transfer
    for transfer, product, inventory_manager, shop_manager, category_name in transfers:
        transfer_date = transfer.created_at.strftime('%Y-%m-%d')
        
        if transfer_date in days:
            product_key = f"{product.sku}_{product.name}"
            
            if product_key not in product_quantities:
                product_quantities[product_key] = {
                    'sku': product.sku,
                    'model': product.name,
                    'category': category_name or 'Uncategorized',
                    'inventory_manager': inventory_manager,
                    'shop_manager': shop_manager,
                    'total_quantity': 0,
                    'warehouse_starting_quantity': warehouse_starting_quantities.get(product.id, 0),
                    'warehouse_quantity': get_warehouse_quantity(product.id),
                    'inventory_quantity': get_inventory_quantity(product.id)
                }
                
                # Initialize all days with zero quantity
                for day in days:
                    product_quantities[product_key][day] = 0
            
            # Add quantity for the specific day
            product_quantities[product_key][transfer_date] += transfer.quantity
            product_quantities[product_key]['total_quantity'] += transfer.quantity
    
    # Convert to list for easier rendering in template
    result = []
    for product_key, data in product_quantities.items():
        result.append(data)
    
    # Sort by total quantity (descending)
    result.sort(key=lambda x: x['total_quantity'], reverse=True)
    
    return {
        'granularity': 'daily',
        'days': days,
        'products': result
    }

# 4. Update the process_weekly_transfers function to include the category information
def process_weekly_transfers(transfers, start_date, end_date):
    """Process warehouse transfers data by week"""
    # Create a dictionary to store product quantities by week
    product_quantities = {}
    
    # Create a list of all weeks in the date range
    weeks = []
    week_dates = {}
    
    # Adjust start_date to the beginning of the week (Monday)
    start_week = start_date - timedelta(days=start_date.weekday())
    
    # Adjust end_date to the end of the week (Sunday)
    end_week = end_date + timedelta(days=6-end_date.weekday())
    
    current_week = start_week
    week_num = 1
    
    while current_week <= end_week:
        week_end = current_week + timedelta(days=6)
        week_key = f"WEEK {week_num}"
        weeks.append(week_key)
        week_dates[week_key] = (current_week, week_end)
        
        current_week += timedelta(days=7)
        week_num += 1
    
    # Get warehouse starting quantities at start date
    warehouse_starting_quantities = get_warehouse_starting_quantities(start_date)
    
    # Process each transfer
    for transfer, product, inventory_manager, shop_manager, category_name in transfers:
        transfer_date = transfer.created_at.date()
        
        # Find which week this transfer belongs to
        for week_key, (week_start, week_end) in week_dates.items():
            if week_start.date() <= transfer_date <= week_end.date():
                product_key = f"{product.sku}_{product.name}"
                
                if product_key not in product_quantities:
                    product_quantities[product_key] = {
                        'sku': product.sku,
                        'model': product.name,
                        'category': category_name or 'Uncategorized',
                        'inventory_manager': inventory_manager,
                        'shop_manager': shop_manager,
                        'total_quantity': 0,
                        'warehouse_starting_quantity': warehouse_starting_quantities.get(product.id, 0),
                        'warehouse_quantity': get_warehouse_quantity(product.id),
                        'inventory_quantity': get_inventory_quantity(product.id)
                    }
                    
                    # Initialize all weeks with zero quantity
                    for week in weeks:
                        product_quantities[product_key][week] = 0
                
                # Add quantity for the specific week
                product_quantities[product_key][week_key] += transfer.quantity
                product_quantities[product_key]['total_quantity'] += transfer.quantity
                break
    
    # Convert to list for easier rendering in template
    result = []
    for product_key, data in product_quantities.items():
        result.append(data)
    
    # Sort by total quantity (descending)
    result.sort(key=lambda x: x['total_quantity'], reverse=True)
    
    return {
        'granularity': 'weekly',
        'weeks': weeks,
        'products': result
    }

# 5. Update the process_monthly_transfers function to include the category information
def process_monthly_transfers(transfers, start_date, end_date):
    """Process warehouse transfers data by month"""
    # Create a dictionary to store product quantities by month
    product_quantities = {}
    
    # Create a list of all months in the date range
    months = []
    month_dates = {}
    
    # Adjust start_date to the beginning of the month
    start_month = start_date.replace(day=1)
    
    # Adjust end_date to the end of the month
    next_month = end_date.replace(day=28) + timedelta(days=4)
    end_month = next_month.replace(day=1) - timedelta(days=1)
    
    current_month = start_month
    month_num = 1
    
    while current_month <= end_month:
        # Get the last day of the current month
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        
        month_key = current_month.strftime('%b %Y')
        months.append(month_key)
        month_dates[month_key] = (current_month, month_end)
        
        current_month = next_month
        month_num += 1
    
    # Get warehouse starting quantities at start date
    warehouse_starting_quantities = get_warehouse_starting_quantities(start_date)
    
    # Process each transfer
    for transfer, product, inventory_manager, shop_manager, category_name in transfers:
        transfer_date = transfer.created_at.date()
        
        # Find which month this transfer belongs to
        for month_key, (month_start, month_end) in month_dates.items():
            if month_start.date() <= transfer_date <= month_end.date():
                product_key = f"{product.sku}_{product.name}"
                
                if product_key not in product_quantities:
                    product_quantities[product_key] = {
                        'sku': product.sku,
                        'model': product.name,
                        'category': category_name or 'Uncategorized',
                        'inventory_manager': inventory_manager,
                        'shop_manager': shop_manager,
                        'total_quantity': 0,
                        'warehouse_starting_quantity': warehouse_starting_quantities.get(product.id, 0),
                        'warehouse_quantity': get_warehouse_quantity(product.id),
                        'inventory_quantity': get_inventory_quantity(product.id)
                    }
                    
                    # Initialize all months with zero quantity
                    for month in months:
                        product_quantities[product_key][month] = 0
                
                # Add quantity for the specific month
                product_quantities[product_key][month_key] += transfer.quantity
                product_quantities[product_key]['total_quantity'] += transfer.quantity
                break
    
    # Convert to list for easier rendering in template
    result = []
    for product_key, data in product_quantities.items():
        result.append(data)
    
    # Sort by total quantity (descending)
    result.sort(key=lambda x: x['total_quantity'], reverse=True)
    
    return {
        'granularity': 'monthly',
        'months': months,
        'products': result
    }

# 6. Update the process_quarterly_transfers function to include the category information
def process_quarterly_transfers(transfers, start_date, end_date):
    """Process warehouse transfers data by quarter"""
    # Create a dictionary to store product quantities by quarter
    product_quantities = {}
    
    # Create a list of all quarters in the date range
    quarters = []
    quarter_dates = {}
    
    # Determine the quarter for start_date
    start_quarter = (start_date.month - 1) // 3 + 1
    start_year = start_date.year
    
    # Determine the quarter for end_date
    end_quarter = (end_date.month - 1) // 3 + 1
    end_year = end_date.year
    
    # Create a list of all quarters between start_date and end_date
    current_year = start_year
    current_quarter = start_quarter
    
    while current_year < end_year or (current_year == end_year and current_quarter <= end_quarter):
        quarter_key = f"Q{current_quarter} {current_year}"
        quarters.append(quarter_key)
        
        # Calculate the start and end dates for this quarter
        quarter_start_month = (current_quarter - 1) * 3 + 1
        quarter_start = datetime(current_year, quarter_start_month, 1)
        
        if current_quarter == 4:
            quarter_end_month = 12
            quarter_end_day = 31
        else:
            quarter_end_month = quarter_start_month + 2
            # Get the last day of the month
            next_month = datetime(current_year, quarter_end_month, 28) + timedelta(days=4)
            quarter_end_day = (next_month.replace(day=1) - timedelta(days=1)).day
        
        quarter_end = datetime(current_year, quarter_end_month, quarter_end_day, 23, 59, 59)
        
        quarter_dates[quarter_key] = (quarter_start, quarter_end)
        
        # Move to the next quarter
        current_quarter += 1
        if current_quarter > 4:
            current_quarter = 1
            current_year += 1
    
    # Get warehouse starting quantities at start date
    warehouse_starting_quantities = get_warehouse_starting_quantities(start_date)
    
    # Process each transfer
    for transfer, product, inventory_manager, shop_manager, category_name in transfers:
        transfer_date = transfer.created_at
        
        # Find which quarter this transfer belongs to
        for quarter_key, (quarter_start, quarter_end) in quarter_dates.items():
            if quarter_start <= transfer_date <= quarter_end:
                product_key = f"{product.sku}_{product.name}"
                
                if product_key not in product_quantities:
                    product_quantities[product_key] = {
                        'sku': product.sku,
                        'model': product.name,
                        'category': category_name or 'Uncategorized',
                        'inventory_manager': inventory_manager,
                        'shop_manager': shop_manager,
                        'total_quantity': 0,
                        'warehouse_starting_quantity': warehouse_starting_quantities.get(product.id, 0),
                        'warehouse_quantity': get_warehouse_quantity(product.id),
                        'inventory_quantity': get_inventory_quantity(product.id)
                    }
                    
                    # Initialize all quarters with zero quantity
                    for quarter in quarters:
                        product_quantities[product_key][quarter] = 0
                
                # Add quantity for the specific quarter
                product_quantities[product_key][quarter_key] += transfer.quantity
                product_quantities[product_key]['total_quantity'] += transfer.quantity
                break
    
    # Convert to list for easier rendering in template
    result = []
    for product_key, data in product_quantities.items():
        result.append(data)
    
    # Sort by total quantity (descending)
    result.sort(key=lambda x: x['total_quantity'], reverse=True)
    
    return {
        'granularity': 'quarterly',
        'quarters': quarters,
        'products': result
    }

# 7. Update the export_transfers_to_excel function to include the category column
def export_transfers_to_excel(transfers_data, start_date, end_date, granularity):
    """Export warehouse transfers data to Excel"""
    # Create DataFrame from transfers data
    data = []
    
    # Determine time periods based on granularity
    time_periods = []
    if granularity == 'daily':
        time_periods = transfers_data['days']
    elif granularity == 'weekly':
        time_periods = transfers_data['weeks']
    elif granularity == 'monthly':
        time_periods = transfers_data['months']
    elif granularity == 'quarterly':
        time_periods = transfers_data['quarters']
    
    # Prepare data for DataFrame
    for product in transfers_data['products']:
        # Get product category from database if not already included
        category_name = product.get('category', 'Uncategorized')
        
        row_data = {
            'SKU': product['sku'],
            'MODEL': product['model'],
            'CATEGORY': category_name,
            'INVENTORY MANAGER': product['inventory_manager'],
            'SHOP MANAGER': product['shop_manager'],
            'WAREHOUSE STARTING QUANTITY': product['warehouse_starting_quantity']
        }
        
        # Add quantities for each time period
        for period in time_periods:
            row_data[period] = product[period]
        
        # Add total and current quantities
        row_data['TOTAL QUANTITY SENT TO SHOP'] = product['total_quantity']
        row_data['WAREHOUSE QUANTITY LEFT'] = product['warehouse_quantity']
        row_data['INVENTORY QUANTITY'] = product['inventory_quantity']
        
        data.append(row_data)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Warehouse Transfers', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Warehouse Transfers']
        
        # Add some formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Set column widths
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)
    
    # Reset file pointer
    output.seek(0)
    
    # Generate filename based on date range and granularity
    filename = f"warehouse_transfers_{granularity}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# 8. HTML Template Changes (transfers_report.html)
# - Add a new column header for Category after Model
# - Add a new column cell for Category in the table body

# 9. PDF Template Changes (transfers_report_pdf.html)
# - Add a new column header for Category after Model
# - Add a new column cell for Category in the table body

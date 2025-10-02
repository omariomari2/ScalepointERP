from app import create_app, db
from modules.inventory.models import Product, StockMove
from modules.inventory.models_warehouse import WarehouseProduct, WarehouseMovement
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Check product 559
    product = Product.query.filter_by(name='559').first()
    
    if product:
        print(f"Product: {product.name} (ID: {product.id}, SKU: {product.sku})")
        
        # Check current warehouse stock
        warehouse_entries = WarehouseProduct.query.filter_by(product_id=product.id).all()
        if warehouse_entries:
            print("\nCurrent warehouse quantities:")
            for entry in warehouse_entries:
                print(f"Warehouse ID: {entry.warehouse_id}, Quantity: {entry.quantity}")
        else:
            print("\nNo warehouse entries found for this product.")
        
        # Check recent transfers
        recent_time = datetime.utcnow() - timedelta(hours=1)
        recent_transfers = StockMove.query.filter_by(
            product_id=product.id
        ).filter(
            StockMove.created_at >= recent_time
        ).order_by(StockMove.created_at.desc()).all()
        
        if recent_transfers:
            print("\nRecent transfers (last hour):")
            for transfer in recent_transfers:
                print(f"Transfer ID: {transfer.id}")
                print(f"  Quantity: {transfer.quantity}")
                print(f"  State: {transfer.state}")
                print(f"  Created at: {transfer.created_at}")
                print(f"  Reference: {transfer.reference}")
                print(f"  Reference type: {transfer.reference_type}")
                print(f"  Source location ID: {transfer.source_location_id}")
                print(f"  Source location warehouse ID: {transfer.source_location.warehouse_id if transfer.source_location else 'None'}")
        else:
            print("\nNo recent transfers found.")
        
        # Check recent warehouse movements
        recent_movements = WarehouseMovement.query.filter_by(
            product_id=product.id
        ).filter(
            WarehouseMovement.created_at >= recent_time
        ).order_by(WarehouseMovement.created_at.desc()).all()
        
        if recent_movements:
            print("\nRecent warehouse movements (last hour):")
            for movement in recent_movements:
                print(f"Movement ID: {movement.id}")
                print(f"  Type: {movement.movement_type}")
                print(f"  Quantity: {movement.quantity}")
                print(f"  Created at: {movement.created_at}")
                print(f"  Reference: {movement.reference}")
                print(f"  Reference type: {movement.reference_type}")
        else:
            print("\nNo recent warehouse movements found.")
    else:
        print("Product '559' not found in database.")

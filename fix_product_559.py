from app import create_app, db
from modules.inventory.models import Product, StockMove
from modules.inventory.models_warehouse import WarehouseProduct, WarehouseMovement
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def fix_product_559():
    """
    Fix the warehouse stock for product 559 by:
    1. Finding all rejected transfers for this product
    2. Creating inbound movements to restore stock if needed
    3. Directly updating the warehouse product quantity
    """
    with app.app_context():
        # Get product 559
        product = Product.query.filter_by(name='559').first()
        
        if not product:
            logger.error("Product 559 not found")
            return False
        
        logger.info(f"Found product: {product.name} (ID: {product.id})")
        
        # Get the current warehouse stock
        warehouse_product = WarehouseProduct.query.filter_by(
            product_id=product.id,
            warehouse_id=1  # Assuming warehouse ID 1
        ).first()
        
        if not warehouse_product:
            logger.error("Warehouse product entry not found")
            return False
        
        current_qty = warehouse_product.quantity
        logger.info(f"Current warehouse quantity: {current_qty}")
        
        # Find all rejected transfers for this product
        rejected_transfers = StockMove.query.filter_by(
            product_id=product.id,
            state='rejected'
        ).all()
        
        logger.info(f"Found {len(rejected_transfers)} rejected transfers")
        
        # Calculate how much stock should be restored
        total_restore_qty = 0
        for transfer in rejected_transfers:
            # Check if this transfer has an outbound movement
            outbound_movements = WarehouseMovement.query.filter_by(
                product_id=transfer.product_id,
                reference=f'Transfer #{transfer.id}',
                movement_type='out'
            ).all()
            
            # Check if this transfer already has an inbound movement
            inbound_movements = WarehouseMovement.query.filter_by(
                product_id=transfer.product_id,
                reference=f'Rejected Transfer #{transfer.id}',
                movement_type='in'
            ).all()
            
            # If we have outbound movements but no inbound movements, we need to restore stock
            if outbound_movements and not inbound_movements:
                restore_qty = int(transfer.quantity)
                total_restore_qty += restore_qty
                
                logger.info(f"Transfer #{transfer.id} needs {restore_qty} units restored")
                
                # Create an inbound movement to record the restoration
                movement = WarehouseMovement(
                    product_id=transfer.product_id,
                    warehouse_id=1,  # Assuming warehouse ID 1
                    quantity=restore_qty,
                    movement_type='in',
                    reference=f'Rejected Transfer #{transfer.id}',
                    reference_type='transfer_reject',
                    created_by_id=1,  # Assuming user ID 1
                    notes=f'Manual fix: Restoration for rejected transfer request #{transfer.id}'
                )
                
                db.session.add(movement)
        
        if total_restore_qty > 0:
            # Update the warehouse product quantity directly
            new_qty = current_qty + total_restore_qty
            warehouse_product.quantity = new_qty
            
            logger.info(f"Updating warehouse quantity from {current_qty} to {new_qty}")
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Successfully restored {total_restore_qty} units to warehouse")
            return True
        else:
            logger.info("No stock needs to be restored")
            return False

if __name__ == '__main__':
    success = fix_product_559()
    if success:
        print("Successfully fixed product 559 warehouse stock")
    else:
        print("No changes were needed for product 559")

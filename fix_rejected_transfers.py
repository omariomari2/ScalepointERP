from app import create_app, db
from modules.inventory.models import StockMove
from modules.inventory.models_warehouse import WarehouseProduct, WarehouseMovement
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def fix_rejected_transfers():
    """
    Fix rejected transfers that didn't properly restore warehouse stock.
    This script will:
    1. Find all rejected transfers that have an outbound movement but no inbound movement
    2. Create the missing inbound movements to restore stock
    """
    with app.app_context():
        # Find all rejected transfers
        rejected_transfers = StockMove.query.filter_by(state='rejected').all()
        
        fixed_count = 0
        for transfer in rejected_transfers:
            # Check if this transfer has an outbound movement but no inbound movement
            outbound_movements = WarehouseMovement.query.filter_by(
                product_id=transfer.product_id,
                reference=f'Transfer #{transfer.id}',
                movement_type='out'
            ).all()
            
            inbound_movements = WarehouseMovement.query.filter_by(
                product_id=transfer.product_id,
                reference=f'Rejected Transfer #{transfer.id}',
                movement_type='in'
            ).all()
            
            # If we have outbound movements but no inbound movements, we need to fix this transfer
            if outbound_movements and not inbound_movements:
                source_location = transfer.source_location
                if source_location and source_location.location_type == 'internal' and source_location.warehouse_id:
                    restore_qty = int(transfer.quantity)
                    
                    logger.info(f"Fixing rejected transfer #{transfer.id} for product {transfer.product_id}")
                    logger.info(f"Restoring {restore_qty} units to warehouse {source_location.warehouse_id}")
                    
                    try:
                        # First, check if the warehouse product exists
                        warehouse_product = WarehouseProduct.query.filter_by(
                            product_id=transfer.product_id,
                            warehouse_id=source_location.warehouse_id
                        ).first()
                        
                        if not warehouse_product:
                            # Create the warehouse product if it doesn't exist
                            warehouse_product = WarehouseProduct(
                                product_id=transfer.product_id,
                                warehouse_id=source_location.warehouse_id,
                                quantity=0
                            )
                            db.session.add(warehouse_product)
                            db.session.commit()
                            logger.info(f"Created new warehouse product entry for product {transfer.product_id}")
                        
                        # Create the movement to restore stock
                        movement = WarehouseMovement(
                            product_id=transfer.product_id,
                            warehouse_id=source_location.warehouse_id,
                            quantity=restore_qty,
                            movement_type='in',
                            reference=f'Rejected Transfer #{transfer.id}',
                            reference_type='transfer_reject',
                            created_by_id=transfer.approved_by_id,
                            notes=f'Automatic restoration for rejected transfer request #{transfer.id} (fixed)'
                        )
                        
                        db.session.add(movement)
                        db.session.commit()
                        
                        # Update the warehouse product quantity directly
                        current_qty = warehouse_product.quantity
                        warehouse_product.quantity = current_qty + restore_qty
                        db.session.commit()
                        
                        logger.info(f"Successfully restored {restore_qty} units to warehouse {source_location.warehouse_id}")
                        logger.info(f"New warehouse quantity: {warehouse_product.quantity}")
                        
                        fixed_count += 1
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error fixing transfer #{transfer.id}: {str(e)}")
        
        logger.info(f"Fixed {fixed_count} rejected transfers")
        return fixed_count

if __name__ == '__main__':
    fixed_count = fix_rejected_transfers()
    print(f"Fixed {fixed_count} rejected transfers")

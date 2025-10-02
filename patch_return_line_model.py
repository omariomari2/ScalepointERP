"""
Patch for the POSReturnLine model to ensure correct values are saved.
This script should be added to app.py to be executed at startup.
"""
from modules.pos.models import POSReturnLine

def patch_return_line_model():
    """Patch the POSReturnLine model to ensure correct values are saved"""
    try:
        # Store the original __init__ method
        original_init = POSReturnLine.__init__
        
        def patched_init(self, *args, **kwargs):
            # Call the original __init__ method
            original_init(self, *args, **kwargs)
            
            # Ensure subtotal is calculated correctly
            if hasattr(self, 'quantity') and hasattr(self, 'unit_price'):
                if self.quantity > 0 and self.unit_price > 0:
                    self.subtotal = self.quantity * self.unit_price
                    print(f"POSReturnLine: Set subtotal={self.subtotal} (quantity={self.quantity}, unit_price={self.unit_price})")
        
        # Replace the __init__ method with our patched version
        POSReturnLine.__init__ = patched_init
        
        print("Successfully patched POSReturnLine model")
        return True
    except Exception as e:
        print(f"Error patching POSReturnLine model: {str(e)}")
        return False

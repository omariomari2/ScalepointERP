"""
Fix for the POSReturnLine model to change quantity from Integer to Float.
This script creates a monkey patch that will be applied when the application starts.
"""

def apply_model_fix():
    """
    Apply the fix to the POSReturnLine model by changing quantity to Float.
    """
    try:
        # Import the necessary modules
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy import Float
        from modules.pos.models import POSReturnLine
        
        # Monkey patch the quantity column to be a float
        POSReturnLine.quantity = SQLAlchemy().Column(Float, default=0.0)
        
        print("POSReturnLine.quantity patched to be a Float")
        return True
    except Exception as e:
        print(f"Error applying model fix: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Apply the model fix
    apply_model_fix()

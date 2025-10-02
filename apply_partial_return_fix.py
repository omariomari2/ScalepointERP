"""
Script to apply the partial return fix to the ERP system.
Run this script to fix the partial return functionality.
"""
from flask import Flask
from modules.pos.routes import pos
from partial_return_fix_new import apply_partial_return_fix
import sys

def apply_fix():
    """Apply the partial return fix to the POS module"""
    print("Applying partial return fix...")
    
    # Apply the fix to the POS blueprint
    fixed_route = apply_partial_return_fix(pos)
    
    print("Partial return fix applied successfully!")
    print("The fixed route is now available at: /pos/returns/partial")
    print("Please restart your application for the changes to take effect.")
    return True

if __name__ == "__main__":
    # Apply the fix
    success = apply_fix()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

// This file contains the fixed JavaScript for the partial return form
// Replace the product selection handler in templates/pos/partial_return_form.html with this code

// Product select change handler
productSelect.addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    if (selectedOption.value) {
        // Set price - ensure it's a valid number
        const price = parseFloat(selectedOption.dataset.price);
        if (!isNaN(price) && price > 0) {
            priceInput.value = price.toFixed(2);
            console.log(`Setting price to ${price.toFixed(2)} for product ${selectedOption.textContent}`);
        } else {
            console.error(`Invalid price for product ${selectedOption.textContent}: ${selectedOption.dataset.price}`);
            priceInput.value = '0.00';
        }
        
        // Set original line ID
        originalLineId.value = selectedOption.dataset.lineId;
        
        // Set quantity info
        const origQty = parseInt(selectedOption.dataset.originalQty);
        const retQty = parseInt(selectedOption.dataset.returnedQty);
        const availQty = parseInt(selectedOption.dataset.availableQty);
        
        originalQuantity.textContent = `Original: ${origQty}`;
        returnedQuantity.textContent = `Returned: ${retQty}`;
        availableQuantity.textContent = `Available: ${availQty}`;
        
        // Set max quantity
        quantityInput.max = availQty;
        quantityInput.min = 1; 
        quantityInput.step = 1; 
        quantityInput.value = 1;
        
        // Show product info
        productInfo.style.display = 'block';
    } else {
        priceInput.value = '0.00';
        originalLineId.value = '';
        productInfo.style.display = 'none';
    }
});

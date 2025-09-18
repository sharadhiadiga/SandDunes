// Form confirmation handlers
document.addEventListener('DOMContentLoaded', function() {
    // Add confirmation to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to proceed?')) {
                e.preventDefault();
            }
        });
    });

    // Add loading spinner to form submissions
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
                submitBtn.disabled = true;
            }
        });
    });

    // Date validation for check-in/check-out
    const checkInInput = document.getElementById('check_in_date');
    const checkOutInput = document.getElementById('check_out_date');

    if (checkInInput && checkOutInput) {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        checkInInput.min = today;
        checkOutInput.min = today;

        // Update check-out minimum date when check-in changes
        checkInInput.addEventListener('change', function() {
            checkOutInput.min = this.value;
            if (checkOutInput.value && checkOutInput.value < this.value) {
                checkOutInput.value = this.value;
            }
        });
    }

    // Phone number formatting
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
            e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
        });
    }

    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });

    // Room availability status colors
    const statusCells = document.querySelectorAll('.room-status');
    statusCells.forEach(cell => {
        const status = cell.textContent.toLowerCase();
        cell.classList.add(`room-${status}`);
    });

    // Service quantity validation
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value < 1) {
                this.value = 1;
            }
        });
    });

    // Price calculation for services
    const calculateServiceTotal = (price, quantity) => {
        return (parseFloat(price) * parseInt(quantity)).toFixed(2);
    };

    // Update service totals when quantity changes
    const serviceForms = document.querySelectorAll('.service-form');
    serviceForms.forEach(form => {
        const quantityInput = form.querySelector('input[name="quantity"]');
        const priceElement = form.querySelector('.service-price');
        const totalElement = form.querySelector('.service-total');

        if (quantityInput && priceElement && totalElement) {
            quantityInput.addEventListener('change', function() {
                const total = calculateServiceTotal(priceElement.dataset.price, this.value);
                totalElement.textContent = `$${total}`;
            });
        }
    });

    // Print bill functionality
    const printButton = document.querySelector('.print-bill');
    if (printButton) {
        printButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    }

    // Responsive table handling
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-wrapper';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}); 
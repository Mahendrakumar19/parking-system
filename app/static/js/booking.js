// Booking form functionality
const PRICING = {
    'bike': 20,
    'car': 30
};

function updatePricing() {
    checkAvailability();
}

function checkAvailability() {
    const vehicleType = document.getElementById('vehicle_type').value;
    const entryTime = document.getElementById('entry_time').value;
    const exitTime = document.getElementById('exit_time').value;
    
    if (!vehicleType || !entryTime || !exitTime) {
        document.getElementById('availabilityInfo').style.display = 'none';
        document.getElementById('submitBtn').disabled = true;
        return;
    }
    
    const entry = new Date(entryTime);
    const exit = new Date(exitTime);
    
    if (exit <= entry) {
        alert('Exit time must be after entry time');
        return;
    }
    
    // Calculate duration in hours
    const duration = (exit - entry) / (1000 * 60 * 60);
    const amount = duration * PRICING[vehicleType];
    
    // Update display
    document.getElementById('duration').textContent = duration.toFixed(1);
    document.getElementById('amount').textContent = amount.toFixed(0);
    
    // Check availability via API
    fetch(`/check_availability?vehicle_type=${vehicleType}&entry_time=${entryTime}&exit_time=${exitTime}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('availableSlots').textContent = data.available_slots;
            document.getElementById('availabilityInfo').style.display = 'block';
            
            if (data.available_slots > 0) {
                document.getElementById('submitBtn').disabled = false;
            } else {
                document.getElementById('submitBtn').disabled = true;
                alert('No slots available for the selected time period');
            }
        })
        .catch(error => {
            console.error('Error checking availability:', error);
        });
}

// Set minimum date/time to current
document.addEventListener('DOMContentLoaded', function() {
    const now = new Date();
    const currentDateTime = now.toISOString().slice(0, 16);
    
    const entryTimeInput = document.getElementById('entry_time');
    const exitTimeInput = document.getElementById('exit_time');
    
    if (entryTimeInput) {
        entryTimeInput.min = currentDateTime;
        entryTimeInput.value = currentDateTime;
    }
    
    if (exitTimeInput) {
        exitTimeInput.min = currentDateTime;
        // Set default exit time to 2 hours from now
        const twoHoursLater = new Date(now.getTime() + 2 * 60 * 60 * 1000);
        exitTimeInput.value = twoHoursLater.toISOString().slice(0, 16);
    }
});

// Update exit time minimum when entry time changes
document.getElementById('entry_time')?.addEventListener('change', function() {
    const entryTime = this.value;
    const exitTimeInput = document.getElementById('exit_time');
    
    if (entryTime && exitTimeInput) {
        exitTimeInput.min = entryTime;
        
        // If exit time is before entry time, update it
        if (exitTimeInput.value <= entryTime) {
            const entryDate = new Date(entryTime);
            const newExitTime = new Date(entryDate.getTime() + 60 * 60 * 1000); // 1 hour later
            exitTimeInput.value = newExitTime.toISOString().slice(0, 16);
        }
    }
    
    checkAvailability();
});

document.getElementById('exit_time')?.addEventListener('change', checkAvailability);
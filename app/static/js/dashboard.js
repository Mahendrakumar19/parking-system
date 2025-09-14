// Dashboard functionality
let currentBookingId = null;

// Modal functionality
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function hideModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking the X
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', function() {
        this.closest('.modal').style.display = 'none';
    });
});

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// Show QR Code
function showQRCode(qrCodeData) {
    const qrDisplay = document.getElementById('qrCodeDisplay');
    qrDisplay.innerHTML = `<img src="data:image/png;base64,${qrCodeData}" alt="QR Code" style="max-width: 300px;">`;
    showModal('qrModal');
}

// Extend booking
function extendBooking(bookingId) {
    currentBookingId = bookingId;
    showModal('extendModal');
}

// Handle extend booking form submission
document.getElementById('extendForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const hours = document.getElementById('additionalHours').value;
    
    if (!currentBookingId) {
        alert('Error: No booking selected');
        return;
    }
    
    fetch(`/extend_booking/${currentBookingId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ hours: parseInt(hours) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`${data.message}\nAdditional cost: ₹${data.additional_cost}\nNew exit time: ${data.new_exit_time}`);
            hideModal('extendModal');
            // Reload page to show updated booking
            window.location.reload();
        } else {
            alert(`Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error extending booking:', error);
        alert('Error extending booking. Please try again.');
    });
});

// Show booking details
function showBookingDetails() {
    // This would show detailed booking information
    // For now, just scroll to the booking section
    document.querySelector('.recent-bookings')?.scrollIntoView({ behavior: 'smooth' });
}

// Auto-refresh dashboard every 5 minutes
setInterval(function() {
    // Only refresh if no modals are open
    const modals = document.querySelectorAll('.modal');
    const hasOpenModal = Array.from(modals).some(modal => modal.style.display === 'block');
    
    if (!hasOpenModal) {
        window.location.reload();
    }
}, 5 * 60 * 1000); // 5 minutes

// Notification for upcoming exit time
function checkUpcomingExit() {
    // This would check if exit time is approaching and show notification
    // Implementation would require server-side support for real-time notifications
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check for upcoming exit time on load
    checkUpcomingExit();
});
// Dark mode toggle
const darkModeToggle = document.getElementById('darkModeToggle');
const html = document.documentElement;

darkModeToggle.addEventListener('click', () => {
    html.classList.toggle('dark');
    localStorage.setItem('darkMode', html.classList.contains('dark'));
    
    // Update chart colors if chart exists
    if (typeof window.updateChartTheme === 'function') {
        window.updateChartTheme();
    }
});

// Check for saved dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
    html.classList.add('dark');
} else if (localStorage.getItem('darkMode') === null) {
    // Check for system preference if no saved preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        html.classList.add('dark');
        localStorage.setItem('darkMode', 'true');
    }
}

// Auto-hide messages after 5 seconds
const notifications = document.querySelectorAll('.notification');
notifications.forEach(notification => {
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        notification.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
});

// Close notification on click
document.querySelectorAll('.close-notification').forEach(button => {
    button.addEventListener('click', () => {
        const notification = button.closest('.notification');
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        notification.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        setTimeout(() => {
            notification.remove();
        }, 500);
    });
});

// Tooltip positioning
document.addEventListener('DOMContentLoaded', () => {
    const tooltips = document.querySelectorAll('.tooltip');
    tooltips.forEach(tooltip => {
        const rect = tooltip.getBoundingClientRect();
        const tooltipWidth = 200; // Approximate width of tooltip
        
        if (rect.left < tooltipWidth / 2) {
            tooltip.classList.add('tooltip-right');
        } else if (window.innerWidth - rect.right < tooltipWidth / 2) {
            tooltip.classList.add('tooltip-left');
        }
    });
});

// Add ripple effect to buttons
const buttons = document.querySelectorAll('button, a.btn, .action-btn');
buttons.forEach(button => {
    button.addEventListener('click', function(e) {
        const x = e.clientX - e.target.getBoundingClientRect().left;
        const y = e.clientY - e.target.getBoundingClientRect().top;
        
        const ripple = document.createElement('span');
        ripple.style.position = 'absolute';
        ripple.style.width = '1px';
        ripple.style.height = '1px';
        ripple.style.borderRadius = '50%';
        ripple.style.transform = 'scale(0)';
        ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.animation = 'ripple 0.6s linear';
        
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    });
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(15);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
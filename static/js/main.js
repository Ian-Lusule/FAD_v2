// Main JavaScript for Fraud App Analyzer

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation enhancements
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Password strength indicator
    var passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            checkPasswordStrength(this);
        });
    });

    // Auto-refresh dashboard data every 60 seconds
    if (window.location.pathname.includes('/dashboard')) {
        setInterval(function() {
            fetchDashboardData();
        }, 60000);
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Copy to clipboard functionality
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            if (textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(function() {
                    const originalText = button.innerHTML;
                    button.innerHTML = '<i class="bi bi-check"></i> Copied!';
                    button.classList.add('btn-success');
                    setTimeout(function() {
                        button.innerHTML = originalText;
                        button.classList.remove('btn-success');
                    }, 2000);
                });
            }
        });
    });

    // Chart initialization (if charts are present on the page)
    initializeCharts();
});

// Password strength checker
function checkPasswordStrength(input) {
    const password = input.value;
    const strengthIndicator = input.parentNode.querySelector('.password-strength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    let feedback = '';
    
    // Check length
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Check for uppercase
    if (/[A-Z]/.test(password)) strength++;
    
    // Check for lowercase
    if (/[a-z]/.test(password)) strength++;
    
    // Check for numbers
    if (/[0-9]/.test(password)) strength++;
    
    // Check for special characters
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    // Update display
    strengthIndicator.className = 'password-strength mt-2';
    
    if (password.length === 0) {
        strengthIndicator.innerHTML = '';
        return;
    }
    
    let strengthClass = '';
    let strengthText = '';
    
    if (strength <= 2) {
        strengthClass = 'text-danger';
        strengthText = 'Weak';
    } else if (strength <= 4) {
        strengthClass = 'text-warning';
        strengthText = 'Medium';
    } else {
        strengthClass = 'text-success';
        strengthText = 'Strong';
    }
    
    strengthIndicator.innerHTML = `
        <div class="progress" style="height: 5px;">
            <div class="progress-bar ${strengthClass.replace('text-', 'bg-')}" 
                 style="width: ${(strength / 6) * 100}%"></div>
        </div>
        <small class="${strengthClass}">Password strength: ${strengthText}</small>
    `;
}

// Fetch dashboard data
function fetchDashboardData() {
    if (window.location.pathname.includes('/admin')) {
        fetch('/admin/api/stats')
            .then(response => response.json())
            .then(data => {
                // Update stats on admin dashboard
                updateDashboardStats(data);
            });
    }
}

// Update dashboard stats
function updateDashboardStats(data) {
    // This would update specific elements on the page with new data
    // Implementation depends on specific dashboard structure
    console.log('Dashboard data updated:', data);
}

// Initialize charts
function initializeCharts() {
    const chartElements = document.querySelectorAll('[data-chart]');
    
    chartElements.forEach(element => {
        const chartType = element.getAttribute('data-chart-type') || 'bar';
        const chartData = JSON.parse(element.getAttribute('data-chart-data') || '{}');
        const chartOptions = JSON.parse(element.getAttribute('data-chart-options') || '{}');
        
        if (chartData && Object.keys(chartData).length > 0) {
            createChart(element, chartType, chartData, chartOptions);
        }
    });
}

// Create chart
function createChart(canvas, type, data, options) {
    const ctx = canvas.getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    color: '#e0e0e0'
                }
            }
        },
        scales: {
            x: {
                ticks: {
                    color: '#e0e0e0'
                },
                grid: {
                    color: '#3d3d3d'
                }
            },
            y: {
                ticks: {
                    color: '#e0e0e0'
                },
                grid: {
                    color: '#3d3d3d'
                }
            }
        }
    };
    
    const mergedOptions = {...defaultOptions, ...options};
    
    return new Chart(ctx, {
        type: type,
        data: data,
        options: mergedOptions
    });
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Show loading spinner
function showLoading(container) {
    if (!container) container = document.body;
    const spinner = document.createElement('div');
    spinner.className = 'spinner-container';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    container.appendChild(spinner);
    return spinner;
}

// Hide loading spinner
function hideLoading(spinner) {
    if (spinner && spinner.parentNode) {
        spinner.parentNode.removeChild(spinner);
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Export functions to global scope
window.FraudAppAnalyzer = {
    showToast,
    formatNumber,
    formatDate,
    showLoading,
    hideLoading
};
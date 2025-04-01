document.addEventListener("DOMContentLoaded", function () {
    // Initialize Bootstrap Tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Copy Command Functionality
    function handleCopyCommand(event) {
        const button = event.currentTarget;
        const command = button.getAttribute('data-command');
        if (!command) return;

        navigator.clipboard.writeText(command)
            .then(() => {
                // Provide visual feedback by changing the icon
                button.innerHTML = '<i class="fas fa-check"></i>';
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-success');

                // Revert back to the original icon after 2 seconds
                setTimeout(() => {
                    button.innerHTML = '<i class="fas fa-copy"></i>';
                    button.classList.remove('btn-success');
                    button.classList.add('btn-outline-secondary');
                }, 2000);
            })
            .catch(err => {
                console.error("Failed to copy command: ", err);
                // Optional: Display an error message to the user
            });
    }

    // Attach event listeners to all copy-command buttons
    const copyButtons = document.querySelectorAll('.copy-command');
    copyButtons.forEach(button => {
        button.addEventListener('click', handleCopyCommand);
    });

    // Copy Button for Kubectl Commands in Pod Details
    const copyKubectlButtons = document.querySelectorAll('.copy-button');
    copyKubectlButtons.forEach(button => {
        button.addEventListener('click', function () {
            const commandText = this.previousElementSibling.textContent.trim();
            navigator.clipboard.writeText(commandText)
                .then(() => {
                    // Provide visual feedback by changing the icon
                    this.innerHTML = '<i class="fas fa-check"></i>';
                    this.classList.remove('btn-light');
                    this.classList.add('btn-success');

                    // Revert back to the original icon after 2 seconds
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-copy"></i>';
                        this.classList.remove('btn-success');
                        this.classList.add('btn-light');
                    }, 2000);
                })
                .catch(err => {
                    console.error("Failed to copy kubectl command: ", err);
                });
        });
    });

    // Generic Copy to Clipboard Function
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function () {
            var toastEl = document.getElementById('copyToast');
            if (toastEl) {
                var toast = new bootstrap.Toast(toastEl);
                toast.show();
            }
        }, function (err) {
            console.error('Could not copy text: ', err);
        });
    };

    // Filter Tables
    const tableFilters = document.querySelectorAll('.table-filter');
    tableFilters.forEach(filter => {
        filter.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableId = this.getAttribute('data-table');
            const table = document.getElementById(tableId);
            
            if (!table) return;
            
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // Resource Status Indicators
    const statusIndicators = document.querySelectorAll('.status-indicator');
    statusIndicators.forEach(indicator => {
        const status = indicator.getAttribute('data-status').toLowerCase();
        if (status === 'running') {
            indicator.classList.add('status-running');
        } else if (status === 'pending') {
            indicator.classList.add('status-pending');
        } else if (status === 'failed') {
            indicator.classList.add('status-failed');
        } else {
            indicator.classList.add('status-unknown');
        }
    });
});
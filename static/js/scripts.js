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

                    // Show toast notification
                    const toastEl = document.getElementById('copyToast');
                    if (toastEl) {
                        const toast = new bootstrap.Toast(toastEl);
                        toast.show();
                    }

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
    
    // Add kubectl command hover functionality
    const commandHoverElements = document.querySelectorAll('.command-hover');
    commandHoverElements.forEach(element => {
        const resourceType = element.getAttribute('data-resource-type');
        const resourceName = element.getAttribute('data-resource-name');
        const namespace = element.getAttribute('data-namespace');
        
        if (resourceType && resourceName) {
            let command = `kubectl get ${resourceType} ${resourceName}`;
            if (namespace && namespace !== 'default') {
                command += ` -n ${namespace}`;
            }
            
            // Create the tooltip element if it doesn't exist
            if (!element.querySelector('.kubectl-command')) {
                const tooltipElement = document.createElement('div');
                tooltipElement.className = 'kubectl-command';
                tooltipElement.textContent = command;
                
                // Add copy button to tooltip
                const copyButton = document.createElement('button');
                copyButton.className = 'btn btn-sm btn-primary position-absolute';
                copyButton.style.top = '5px';
                copyButton.style.right = '5px';
                copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                copyButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    copyToClipboard(command);
                });
                
                tooltipElement.appendChild(copyButton);
                element.appendChild(tooltipElement);
            }
        }
    });
    
    // Initialize WebSocket for real-time updates if available
    function initWebSocket() {
        // Check if the page has a data attribute for real-time updates
        const realTimeContainer = document.querySelector('[data-realtime="true"]');
        if (!realTimeContainer) return;
        
        const resourceType = realTimeContainer.getAttribute('data-resource-type');
        const namespace = realTimeContainer.getAttribute('data-namespace');
        
        if (!resourceType) return;
        
        // Create WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${resourceType}/`;
        const socket = new WebSocket(wsUrl);
        
        // Connection opened
        socket.addEventListener('open', (event) => {
            console.log('WebSocket connected for', resourceType);
            // Send initial message with namespace filter if applicable
            if (namespace) {
                socket.send(JSON.stringify({
                    action: 'subscribe',
                    resourceType: resourceType,
                    namespace: namespace
                }));
            } else {
                socket.send(JSON.stringify({
                    action: 'subscribe',
                    resourceType: resourceType
                }));
            }
        });
        
        // Listen for messages
        socket.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data);
                
                // Handle different types of updates
                if (data.type === 'update' && data.resourceType === resourceType) {
                    updateResourceDisplay(data.resources);
                } else if (data.type === 'error') {
                    console.error('WebSocket error:', data.message);
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        });
        
        // Connection closed
        socket.addEventListener('close', (event) => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after a delay
            setTimeout(initWebSocket, 5000);
        });
        
        // Connection error
        socket.addEventListener('error', (event) => {
            console.error('WebSocket error:', event);
            socket.close();
        });
    }
    
    // Function to update resource display based on WebSocket data
    function updateResourceDisplay(resources) {
        // This function will be implemented based on the specific resource type
        // and how it's displayed in the UI
        console.log('Received resource update:', resources);
        
        // Example implementation for updating a Tabulator table
        const table = Tabulator.findTable('#resources-table')[0];
        if (table) {
            table.replaceData(resources);
        }
    }
    
    // Initialize WebSocket if the page supports real-time updates
    initWebSocket();
});
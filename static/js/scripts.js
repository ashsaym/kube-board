document.addEventListener("DOMContentLoaded", function () {

    // Copy Command Functionality
    function handleCopyCommand(event) {
        const button = event.currentTarget;
        const command = button.getAttribute('data-command');
        if (!command) return;

        navigator.clipboard.writeText(command)
            .then(() => {
                // Provide visual feedback by changing the icon
                button.innerHTML = '<i class="bi bi-clipboard-check"></i>';
                button.classList.remove('btn-outline-light');
                button.classList.add('btn-success');

                // Revert back to the original icon after 2 seconds
                setTimeout(() => {
                    button.innerHTML = '<i class="bi bi-clipboard"></i>';
                    button.classList.remove('btn-success');
                    button.classList.add('btn-outline-light');
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
                    this.innerHTML = '<i class="bi bi-clipboard-check"></i>';
                    this.classList.remove('btn-dark');
                    this.classList.add('btn-success');

                    // Revert back to the original icon after 2 seconds
                    setTimeout(() => {
                        this.innerHTML = '<i class="bi bi-clipboard"></i>';
                        this.classList.remove('btn-success');
                        this.classList.add('btn-dark');
                    }, 2000);
                })
                .catch(err => {
                    console.error("Failed to copy kubectl command: ", err);
                });
        });
    });
});
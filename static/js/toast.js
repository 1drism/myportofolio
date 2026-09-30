let toastTimer;

function showToast(title, message, type = 'normal', duration = 3000) {
    const toastComponent = document.getElementById('toast-component');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');

    if (!toastComponent) return;

    // Remove the previous type class
    toastComponent.classList.remove('toast-success', 'toast-error', 'toast-normal');

    // Apply the new class based on type
    if (type === 'success') {
        toastComponent.classList.add('toast-success');
    } else if (type === 'error') {
        toastComponent.classList.add('toast-error');
    } else {
        toastComponent.classList.add('toast-normal');
    }

    // Update the text content
    toastTitle.textContent = title;
    toastMessage.textContent = message;

    // Cancel the previous timer if a toast is still showing
    clearTimeout(toastTimer);

    // Show animation
    if (!toastComponent.matches(':popover-open')) {
        toastComponent.showPopover();
        void toastComponent.offsetHeight; // force a style recalculation so the transition runs
    }
    toastComponent.classList.remove('toast-hidden');
    toastComponent.classList.add('toast-show');

    // Auto-hide animation
    toastTimer = setTimeout(() => {
        toastComponent.classList.remove('toast-show');
        toastComponent.classList.add('toast-hidden');
        toastTimer = setTimeout(() => toastComponent.hidePopover(), 300);
    }, duration);
}
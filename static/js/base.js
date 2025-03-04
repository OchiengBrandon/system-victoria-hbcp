document.addEventListener('alpine:init', () => {
    Alpine.data('quickActions', () => ({
        quickActionsOpen: false,
        toggle() {
            this.quickActionsOpen = !this.quickActionsOpen;
        },
        close() {
            this.quickActionsOpen = false;
        }
    }));
});
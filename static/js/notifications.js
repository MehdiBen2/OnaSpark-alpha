// Lightweight Notification System
class NotificationManager {
    constructor() {
        // Queue to store pending notifications
        this.queue = [];
        // Flag to track if a notification is currently being displayed
        this.isDisplaying = false;
        // Default notification duration
        this.duration = 3000; // 3 seconds
    }

    /**
     * Show a notification
     * @param {string} type - Notification type (success, error, warning, info)
     * @param {string} message - Notification message
     * @param {Object} [options] - Additional configuration options
     */
    show(type, message, options = {}) {
        console.log(`Showing notification: ${type} - ${message}`);
        
        // Validate input
        if (!['success', 'error', 'warning', 'info'].includes(type)) {
            console.error('Invalid notification type');
            return;
        }

        // Create notification object
        const notification = { type, message, options };

        // Add to queue
        this.queue.push(notification);

        // Try to display notifications
        this.processQueue();
    }

    /**
     * Process the notification queue
     */
    processQueue() {
        // If already displaying a notification or queue is empty, return
        if (this.isDisplaying || this.queue.length === 0) {
            return;
        }

        // Get the next notification
        const notification = this.queue.shift();

        // Default options
        const defaultOptions = {
            duration: this.duration,
            position: 'bottom-left'
        };

        // Merge default options with provided options
        const config = { ...defaultOptions, ...notification.options };

        // Ensure notification container exists
        let notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-container';
            document.body.appendChild(notificationContainer);
        }

        // Create notification element
        const notificationElement = document.createElement('div');
        notificationElement.className = notification.type;
        
        // Add icon based on type
        const icon = this.getIcon(notification.type);
        const message = this.decodeHtmlEntities(notification.message);
        notificationElement.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
        `;

        // Add to container
        notificationContainer.appendChild(notificationElement);

        // Set displaying flag
        this.isDisplaying = true;

        // Trigger reflow to enable transition
        notificationElement.offsetHeight;

        // Show notification
        notificationElement.style.opacity = '1';
        notificationElement.style.transform = 'translateX(0)';

        // Auto-remove after duration
        const removeTimer = setTimeout(() => {
            this.remove(notificationElement);
        }, config.duration);

        // Allow manual close on click
        notificationElement.addEventListener('click', () => {
            clearTimeout(removeTimer);
            this.remove(notificationElement);
        });
    }

    /**
     * Remove a specific notification
     * @param {HTMLElement} notificationElement - Notification to remove
     */
    remove(notificationElement) {
        notificationElement.style.opacity = '0';
        notificationElement.style.transform = 'translateX(-100%)';
        
        // Actually remove from DOM after animation
        setTimeout(() => {
            notificationElement.remove();
            
            // Reset displaying flag
            this.isDisplaying = false;
            
            // Process next notification in queue
            this.processQueue();
        }, 300);
    }

    /**
     * Get icon class based on notification type
     * @param {string} type - Notification type
     * @returns {string} Icon class
     */
    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    /**
     * Decode HTML entities to their corresponding characters
     * @param {string} html - String with HTML entities
     * @returns {string} Decoded string
     */
    decodeHtmlEntities(html) {
        const txt = document.createElement('textarea');
        txt.innerHTML = html;
        return txt.value;
    }

    /**
     * Convenience methods for different notification types
     */
    success(message, options = {}) {
        console.log('Notification success called:', message);
        this.show('success', message, options);
    }

    error(message, options = {}) {
        console.log('Notification error called:', message);
        this.show('error', message, options);
    }

    warning(message, options = {}) {
        console.log('Notification warning called:', message);
        this.show('warning', message, options);
    }

    info(message, options = {}) {
        console.log('Notification info called:', message);
        this.show('info', message, options);
    }
}

// Create a singleton instance
window.Notifications = new NotificationManager();

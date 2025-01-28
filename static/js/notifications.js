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
            notificationContainer.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                max-width: 300px;
                width: 100%;
            `;
            document.body.appendChild(notificationContainer);
        }

        // Clear any existing notifications
        notificationContainer.innerHTML = '';

        // Create notification element
        const notificationElement = document.createElement('div');
        notificationElement.style.cssText = `
            background-color: ${this.getBackgroundColor(notification.type)};
            color: white;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            max-width: 100%;
            word-wrap: break-word;
            opacity: 0;
            transform: translateX(-100%);
            transition: all 0.3s ease;
        `;
        notificationElement.innerHTML = this.decodeHtmlEntities(notification.message);

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
     * Get background color based on notification type
     * @param {string} type - Notification type
     * @returns {string} Background color
     */
    getBackgroundColor(type) {
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        return colors[type] || '#17a2b8';
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

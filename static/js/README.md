# Notification System

## Usage

### Basic Usage
```javascript
// Success notification
Notifications.success('Operation completed successfully');

// Error notification
Notifications.error('An error occurred');

// Warning notification
Notifications.warning('Please check your inputs');

// Info notification
Notifications.info('Additional information');
```

### Advanced Usage with Options
```javascript
Notifications.show('success', 'Custom message', {
    duration: 3000,  // Custom duration in milliseconds
    position: 'top-right'  // Position of notification
});
```

## Positions
- `top-right` (default)
- More positions can be added in future updates

## Customization
- Modify the CSS in `notifications.js` to change appearance
- Add more positions or styling as needed

## Installation
1. Include the `notifications.js` script in your HTML
2. Ensure it's loaded before your page scripts
```html
<script src="/static/js/notifications.js"></script>
```

## Browser Compatibility
- Modern browsers supporting ES6

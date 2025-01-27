// Logo Click Counter
let logoClicks = 0;
let lastClickTime = 0;
const CLICK_TIMEOUT = 2000; // 2 seconds to reset counter

document.addEventListener('DOMContentLoaded', function() {
    // Mobile enhancements
    const metaViewport = document.querySelector('meta[name="viewport"]');
    const inputs = document.querySelectorAll('input');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            metaViewport.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=1');
        });
        
        input.addEventListener('blur', function() {
            metaViewport.setAttribute('content', 'width=device-width, initial-scale=1');
        });
    });

    // Form handling
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const usernameError = document.getElementById('usernameError');
    const passwordError = document.getElementById('passwordError');

    // Form submission handler
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset error states
        usernameError.textContent = '';
        passwordError.textContent = '';
        document.getElementById('loginError').classList.add('d-none');
        
        const formData = new FormData(this);
        
        try {
            const response = await fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                const overlay = document.querySelector('.login-animation-overlay');
                const welcomeMessage = document.querySelector('.welcome-message');
                const onaLogo = document.querySelector('.ona-logo');
                const nicknameSpan = document.querySelector('.welcome-message .nickname');
                
                nicknameSpan.textContent = data.nickname || data.username;
                overlay.classList.add('active');
                
                setTimeout(() => {
                    welcomeMessage.classList.add('active');
                    setTimeout(() => {
                        onaLogo.classList.add('active');
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    }, 500);
                }, 100);
            } else {
                const loginError = document.getElementById('loginError');
                loginError.textContent = data.message || "Une erreur s'est produite lors de la connexion.";
                loginError.classList.remove('d-none');
                
                // Add shake animation to form for invalid credentials
                loginForm.classList.add('shake-animation');
                setTimeout(() => {
                    loginForm.classList.remove('shake-animation');
                }, 500);
            }
        } catch (error) {
            console.error('Error:', error);
            const loginError = document.getElementById('loginError');
            loginError.textContent = "Une erreur s'est produite lors de la connexion.";
            loginError.classList.remove('d-none');
        }
    });

    // Toggle password visibility
    document.getElementById('togglePassword').addEventListener('click', function() {
        const passwordInput = document.getElementById('password');
        const icon = this.querySelector('i');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
        } else {
            passwordInput.type = 'password';
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
        }
    });

    function showMobileError(input, errorElement, message) {
        input.classList.add('error');
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }

    function clearMobileError(input, errorElement) {
        input.classList.remove('error');
        errorElement.textContent = '';
        errorElement.classList.remove('show');
    }

    usernameInput.addEventListener('input', function() {
        if (this.value.trim() === '') {
            showMobileError(this, usernameError, 'Nom d\'utilisateur requis');
        } else {
            clearMobileError(this, usernameError);
        }
    });

    passwordInput.addEventListener('input', function() {
        if (this.value.trim() === '') {
            showMobileError(this, passwordError, 'Mot de passe requis');
        } else {
            clearMobileError(this, passwordError);
        }
    });

    // Improve touch interactions
    const touchableElements = document.querySelectorAll('.btn-primary, .btn-return, #togglePassword');
    touchableElements.forEach(el => {
        el.addEventListener('touchstart', function() {
            this.classList.add('touch-active');
        });
        el.addEventListener('touchend', function() {
            this.classList.remove('touch-active');
        });
    });
});

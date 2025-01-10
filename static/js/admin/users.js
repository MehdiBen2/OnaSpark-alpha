// users.js: User Management Page Functionality
(function() {
    // Configuration and Constants
    const CONFIG = {
        SELECTORS: {
            createUserBtn: '#createUserBtn',
            panel: '#userPanel',
            closeBtn: '#closePanelBtn',
            form: '#createUserForm',
            roleSelect: '#role',
            zoneContainer: '#zoneContainer',
            unitContainer: '#unitContainer',
            zoneSelect: '#zone_id',
            unitSelect: '#unit_id',
            submitBtn: '#submitBtn',
            searchInput: '#searchInput',
            deleteModal: '#deleteModal',
            confirmDeleteBtn: '#confirmDelete',
            editUserButtons: '.edit-user',
            deleteUserButtons: '.delete-user'
        },
        ROLE_DESCRIPTIONS: {
            'Admin': 'Accès administrateur complet avec capacité d\'assigner des rôles et des permissions aux utilisateurs.',
            'Employeur DG': 'Accès global à toutes les données à travers toutes les zones et unités.',
            'Employeur Zone': 'Accès et gestion des données pour une zone spécifique uniquement.',
            'Employeur Unité': 'Accès et gestion des données pour une unité spécifique dans une zone.',
            'Utilisateur': 'Accès restreint à une zone et une unité spécifiques.'
        },
        ENDPOINTS: {
            createUser: '/admin/users/create',
            updateUser: (userId) => `/admin/users/${userId}/update`,
            deleteUser: (userId) => `/admin/users/${userId}/delete`,
            fetchUnits: (zoneId) => `/api/zones/${zoneId}/units`
        }
    };

    // Utility Functions
    const utils = {
        // Prevent duplicate toast messages
        toastMessages: new Set(),

        showToast: function(message, type = 'success') {
            // Prevent duplicate messages
            if (this.toastMessages.has(message)) return;
            this.toastMessages.add(message);
            
            // Auto-remove from set after 5 seconds
            setTimeout(() => this.toastMessages.delete(message), 5000);

            const flashContainer = document.querySelector('.notification-container');
            if (!flashContainer) return;

            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.setAttribute('role', 'alert');

            const iconClass = {
                'success': 'fa-check-circle text-success',
                'error': 'fa-times-circle text-danger',
                'warning': 'fa-exclamation-triangle text-warning',
                'info': 'fa-info-circle text-info'
            }[type] || 'fa-info-circle text-info';

            notification.innerHTML = `
                <div class="notification-content">
                    <i class="fas ${iconClass} notification-icon"></i>
                    <span class="notification-message">${message}</span>
                </div>
                <button type="button" class="notification-close" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            `;

            const closeButton = notification.querySelector('.notification-close');
            closeButton.addEventListener('click', () => {
                notification.style.transform = 'translateX(-100%)';
                notification.style.opacity = '0';
                setTimeout(() => {
                    notification.remove();
                    this.toastMessages.delete(message);
                }, 300);
            });

            flashContainer.appendChild(notification);
            notification.offsetHeight;
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';

            setTimeout(() => {
                notification.style.transform = 'translateX(-100%)';
                notification.style.opacity = '0';
                setTimeout(() => {
                    notification.remove();
                    this.toastMessages.delete(message);
                }, 300);
            }, 5000);
        },

        // Form validation helper
        validateForm: function(form) {
            const requiredFields = ['username', 'nickname', 'role'];
            let isValid = true;

            requiredFields.forEach(field => {
                const input = form.querySelector(`#${field}`);
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    input.focus();
                    isValid = false;
                }
            });

            return isValid;
        },

        // Loading state management
        setLoadingState: function(button, isLoading, originalText) {
            const spinnerElement = button.querySelector('.spinner-border');
            const buttonTextElement = button.querySelector('.button-text');

            if (isLoading) {
                button.disabled = true;
                spinnerElement.classList.remove('d-none');
                buttonTextElement.textContent = originalText;
                button.classList.add('btn-loading');
                button.style.color = '#ffffff';
                button.style.backgroundColor = '#007bff';
            } else {
                button.disabled = false;
                spinnerElement.classList.add('d-none');
                buttonTextElement.textContent = originalText;
                button.classList.remove('btn-loading');
                button.style.color = '';
                button.style.backgroundColor = '';
            }
        }
    };

    // User Management Class
    class UserManager {
        constructor() {
            this.currentUserId = null;
            this.isEditing = false;
            this.currentUserToDelete = null;
            this.deleteModal = new bootstrap.Modal(document.querySelector(CONFIG.SELECTORS.deleteModal));
            this.searchTimeout = null;
            this.initializeEventListeners();
        }

        initializeEventListeners() {
            // Create user button
            document.querySelector(CONFIG.SELECTORS.createUserBtn).addEventListener('click', () => this.resetForm());

            // Form submission
            document.querySelector(CONFIG.SELECTORS.form).addEventListener('submit', (e) => this.handleFormSubmission(e));

            // Edit user buttons
            document.querySelectorAll(CONFIG.SELECTORS.editUserButtons).forEach(button => {
                button.addEventListener('click', () => this.prepareEditUser(button));
            });

            // Delete user buttons
            document.querySelectorAll(CONFIG.SELECTORS.deleteUserButtons).forEach(button => {
                button.addEventListener('click', () => {
                    this.currentUserToDelete = button.dataset.userId;
                    this.deleteModal.show();
                });
            });

            // Confirm delete button
            document.querySelector(CONFIG.SELECTORS.confirmDeleteBtn).addEventListener('click', () => this.handleUserDeletion());

            // Role change handler
            document.querySelector(CONFIG.SELECTORS.roleSelect).addEventListener('change', this.handleRoleChange.bind(this));

            // Zone change handler
            document.querySelector(CONFIG.SELECTORS.zoneSelect).addEventListener('change', this.handleZoneChange.bind(this));

            // Search functionality
            document.querySelector(CONFIG.SELECTORS.searchInput).addEventListener('input', () => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(this.handleSearch.bind(this), 300);
            });
        }

        resetForm() {
            const form = document.querySelector(CONFIG.SELECTORS.form);
            const panel = document.querySelector(CONFIG.SELECTORS.panel);
            
            form.reset();
            form.classList.remove('was-validated');
            
            this.currentUserId = null;
            this.isEditing = false;
            
            document.querySelector(CONFIG.SELECTORS.zoneContainer).style.display = 'none';
            document.querySelector(CONFIG.SELECTORS.unitContainer).style.display = 'none';
            
            document.querySelector('.role-description').textContent = '';
            
            this.updatePanelForEditing(false);
            panel.classList.add('open');
        }

        async handleFormSubmission(e) {
            e.preventDefault();
            const form = e.target;
            const submitButton = form.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.querySelector('.button-text').textContent;

            try {
                if (!utils.validateForm(form)) return;

                utils.setLoadingState(submitButton, true, originalButtonText);

                const formData = new FormData(form);
                const endpoint = this.isEditing 
                    ? CONFIG.ENDPOINTS.updateUser(this.currentUserId)
                    : CONFIG.ENDPOINTS.createUser;

                const response = await fetch(endpoint, {
                    method: this.isEditing ? 'PUT' : 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    utils.showToast(
                        data.message || (this.isEditing ? 'Utilisateur modifié avec succès' : 'Utilisateur créé avec succès'), 
                        'success'
                    );
                    document.querySelector(CONFIG.SELECTORS.panel).classList.remove('open');
                    location.reload();
                } else {
                    utils.showToast(
                        data.message || (this.isEditing ? 'Erreur lors de la modification' : 'Erreur lors de la création'), 
                        'error'
                    );
                }
            } catch (error) {
                console.error('Form submission error:', error);
                utils.showToast('Une erreur est survenue', 'error');
            } finally {
                utils.setLoadingState(submitButton, false, originalButtonText);
            }
        }

        prepareEditUser(button) {
            const userId = button.dataset.userId;
            const username = button.dataset.username;
            const nickname = button.dataset.nickname;
            const role = button.dataset.role;
            const zoneId = button.dataset.zone;
            const unitId = button.dataset.unit;

            this.currentUserId = userId;
            this.isEditing = true;
            
            const panel = document.querySelector(CONFIG.SELECTORS.panel);
            
            // Update form
            document.getElementById('username').value = username;
            document.getElementById('nickname').value = nickname || '';
            document.getElementById('role').value = role;
            document.getElementById('password').value = '';
            
            // Trigger role change to show/hide zone and unit fields
            const roleSelect = document.getElementById('role');
            const roleEvent = new Event('change');
            roleSelect.dispatchEvent(roleEvent);
            
            // Set zone if present
            if (zoneId) {
                const zoneSelect = document.getElementById('zone_id');
                zoneSelect.value = zoneId;
                
                // Trigger zone change to load units
                const zoneEvent = new Event('change');
                zoneSelect.dispatchEvent(zoneEvent);
                
                // Set unit after a small delay to ensure units are loaded
                if (unitId) {
                    setTimeout(() => {
                        document.getElementById('unit_id').value = unitId;
                    }, 500);
                }
            }
            
            this.updatePanelForEditing(true);
            panel.classList.add('open');
        }

        updatePanelForEditing(editing) {
            const panelTitle = document.getElementById('panelTitle');
            const buttonText = document.querySelector('#submitBtn .button-text');
            const passwordRequired = document.querySelector('.password-required');
            const passwordInput = document.getElementById('password');

            if (editing) {
                panelTitle.textContent = 'Modifier l\'utilisateur';
                buttonText.textContent = 'Enregistrer les modifications';
                passwordRequired.style.display = 'none';
                passwordInput.required = false;
            } else {
                panelTitle.textContent = 'Créer un utilisateur';
                buttonText.textContent = 'Créer l\'utilisateur';
                passwordRequired.style.display = 'inline';
                passwordInput.required = true;
            }
        }

        handleRoleChange() {
            const roleSelect = document.querySelector(CONFIG.SELECTORS.roleSelect);
            const role = roleSelect.value;
            const zoneContainer = document.getElementById('zoneContainer');
            const unitContainer = document.getElementById('unitContainer');
            const zoneSelect = document.getElementById('zone_id');
            const unitSelect = document.getElementById('unit_id');
            const description = document.querySelector('.role-description');

            // Update role description
            description.textContent = CONFIG.ROLE_DESCRIPTIONS[role] || '';

            // Reset validations
            zoneSelect.required = false;
            unitSelect.required = false;

            // Hide containers by default
            zoneContainer.style.display = 'none';
            unitContainer.style.display = 'none';

            // Show/hide containers based on role
            switch(role) {
                case 'Admin':
                case 'Employeur DG':
                    // Admin and DG don't need zone or unit
                    zoneSelect.value = '';
                    unitSelect.value = '';
                    break;
                case 'Employeur Zone':
                    // Zone employer needs zone only
                    zoneContainer.style.display = 'block';
                    zoneSelect.required = true;
                    unitSelect.value = '';
                    break;
                case 'Employeur Unité':
                case 'Utilisateur':
                    // Unit employer and regular user need both zone and unit
                    zoneContainer.style.display = 'block';
                    unitContainer.style.display = 'block';
                    zoneSelect.required = true;
                    unitSelect.required = true;
                    break;
            }
        }

        handleZoneChange() {
            const zoneId = document.getElementById('zone_id').value;
            const unitSelect = document.getElementById('unit_id');
            const unitContainer = document.getElementById('unitContainer');
            
            // Clear current units
            unitSelect.innerHTML = '<option value="">Sélectionnez une unité</option>';
            
            if (!zoneId) {
                unitContainer.style.display = 'none';
                return;
            }

            // Show loading state
            unitSelect.disabled = true;
            unitSelect.innerHTML = '<option value="">Chargement des unités...</option>';

            // Fetch units for selected zone
            fetch(CONFIG.ENDPOINTS.fetchUnits(zoneId))
                .then(response => response.json())
                .then(data => {
                    unitSelect.innerHTML = '<option value="">Sélectionner une unité</option>';
                    
                    if (data.success) {
                        if (data.units && data.units.length > 0) {
                            data.units.forEach(unit => {
                                const option = document.createElement('option');
                                option.value = unit.id;
                                option.textContent = `${unit.name} (${unit.code})`;
                                unitSelect.appendChild(option);
                            });
                        } else {
                            unitSelect.innerHTML = '<option value="">Aucune unité disponible</option>';
                        }
                    } else {
                        utils.showToast(data.message || 'Erreur lors du chargement des unités', 'error');
                        unitSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    utils.showToast('Erreur lors du chargement des unités', 'error');
                    unitSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                })
                .finally(() => {
                    unitSelect.disabled = false;
                });
        }

        handleUserDeletion() {
            if (!this.currentUserToDelete) return;
            
            fetch(CONFIG.ENDPOINTS.deleteUser(this.currentUserToDelete), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    utils.showToast('Utilisateur supprimé avec succès', 'success');
                    location.reload();
                } else {
                    throw new Error(data.error || data.message || 'Erreur lors de la suppression');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                utils.showToast(error.message, 'error');
            })
            .finally(() => {
                this.deleteModal.hide();
                this.currentUserToDelete = null;
            });
        }

        handleSearch() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#usersTable tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        new UserManager();
        
        // Initialize tooltips
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
    });
})();

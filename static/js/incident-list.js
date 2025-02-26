document.addEventListener('DOMContentLoaded', function() {
    const toggleViewBtn = document.getElementById('toggleView');
    const cardView = document.getElementById('cardView');
    const listView = document.getElementById('listView');
    const emailButton = document.getElementById('emailButton');
    const emailPanel = document.getElementById('emailPanel');
    const closeEmailPanel = document.getElementById('closeEmailPanel');
    const gmailButton = document.getElementById('gmailButton');
    const receiverEmail = document.getElementById('receiverEmail');
    const saveEmailBtn = document.getElementById('saveEmailBtn');
    const savedEmailsList = document.getElementById('savedEmailsList');
    
    // Get current user ID
    const currentUserId = emailPanel.dataset.userId;
    const STORAGE_KEY = `savedEmails_${currentUserId}`;
    
    // Get the saved view preference
    let isListView = localStorage.getItem('incidentViewPreference') === 'list';

    // Load saved emails for current user
    function loadSavedEmails() {
        const savedEmails = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        savedEmailsList.innerHTML = '';
        
        if (savedEmails.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'text-center text-muted p-3';
            emptyState.innerHTML = `
                <i class="fas fa-inbox fa-2x mb-2"></i>
                <p class="mb-0">Aucun email enregistré</p>
            `;
            savedEmailsList.appendChild(emptyState);
            return;
        }
        
        savedEmails.forEach(email => {
            const emailItem = document.createElement('div');
            emailItem.className = 'saved-email-item';
            emailItem.innerHTML = `
                <span class="email-text">${email}</span>
                <div class="email-actions">
                    <button class="btn btn-sm btn-outline-primary btn-action use-email" title="Utiliser cet email">
                        <i class="fas fa-arrow-up"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger btn-action delete-email" title="Supprimer">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            // Use email button
            emailItem.querySelector('.use-email').addEventListener('click', () => {
                receiverEmail.value = email;
            });
            
            // Delete email button
            emailItem.querySelector('.delete-email').addEventListener('click', () => {
                if (confirm('Êtes-vous sûr de vouloir supprimer cet email ?')) {
                    const savedEmails = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
                    const updatedEmails = savedEmails.filter(e => e !== email);
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedEmails));
                    loadSavedEmails();
                    
                    // Show delete confirmation
                    const toast = document.createElement('div');
                    toast.className = 'alert alert-info position-fixed bottom-0 end-0 m-3';
                    toast.style.zIndex = '1060';
                    toast.innerHTML = `
                        <i class="fas fa-trash me-2"></i>
                        Email supprimé
                    `;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3000);
                }
            });
            
            savedEmailsList.appendChild(emailItem);
        });
    }

    // Save email button handler
    if (saveEmailBtn && receiverEmail) {
        saveEmailBtn.addEventListener('click', function() {
            const email = receiverEmail.value.trim();
            if (email) {
                const savedEmails = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
                if (!savedEmails.includes(email)) {
                    savedEmails.push(email);
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(savedEmails));
                    loadSavedEmails();
                    receiverEmail.value = '';
                    // Show success message
                    const toast = document.createElement('div');
                    toast.className = 'alert alert-success position-fixed bottom-0 end-0 m-3';
                    toast.style.zIndex = '1060';
                    toast.innerHTML = `
                        <i class="fas fa-check-circle me-2"></i>
                        Email enregistré avec succès
                    `;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3000);
                } else {
                    // Show duplicate warning
                    const toast = document.createElement('div');
                    toast.className = 'alert alert-warning position-fixed bottom-0 end-0 m-3';
                    toast.style.zIndex = '1060';
                    toast.innerHTML = `
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Cet email existe déjà
                    `;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3000);
                }
            }
        });
    }

    // Gmail Button Handler
    if (gmailButton && receiverEmail) {
        gmailButton.addEventListener('click', function() {
            const email = receiverEmail.value.trim();
            if (email) {
                const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(email)}`;
                window.open(gmailUrl, '_blank');
            } else {
                alert('Veuillez saisir une adresse email');
            }
        });
    }

    // Email Panel Functions
    function openEmailPanel() {
        emailPanel.style.display = 'block';
        // Force reflow
        emailPanel.offsetHeight;
        emailPanel.classList.add('show');
        document.body.style.overflow = 'hidden';
        loadSavedEmails();
    }

    function closeEmailPanelFunc() {
        emailPanel.classList.remove('show');
        document.body.style.overflow = '';
        setTimeout(() => {
            emailPanel.style.display = 'none';
        }, 300);
    }

    // Email Panel Event Listeners
    if (emailButton && emailPanel && closeEmailPanel) {
        emailButton.addEventListener('click', openEmailPanel);
        closeEmailPanel.addEventListener('click', closeEmailPanelFunc);

        // Close panel when clicking outside the content
        emailPanel.addEventListener('click', function(event) {
            if (event.target === emailPanel) {
                closeEmailPanelFunc();
            }
        });

        // Prevent panel close when clicking inside content
        emailPanel.querySelector('.email-panel-content').addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }

    function updateView() {
        if (isListView) {
            cardView.classList.add('d-none');
            listView.classList.remove('d-none');
            toggleViewBtn.innerHTML = '<i class="fas fa-th-large me-2"></i>Vue Cartes';
        } else {
            listView.classList.add('d-none');
            cardView.classList.remove('d-none');
            toggleViewBtn.innerHTML = '<i class="fas fa-list me-2"></i>Vue Liste';
        }
        // Save the preference
        localStorage.setItem('incidentViewPreference', isListView ? 'list' : 'card');
    }

    if (toggleViewBtn && cardView && listView) {
        // Set initial view
        updateView();

        toggleViewBtn.addEventListener('click', function() {
            isListView = !isListView;
            updateView();
        });
    }

    // Handle form submissions to maintain view
    document.querySelectorAll('form[action^="/delete_incident/"]').forEach(form => {
        form.addEventListener('submit', function() {
            // Store the current view preference before form submission
            localStorage.setItem('incidentViewPreference', isListView ? 'list' : 'card');
        });
    });

    // Sorting functionality
    const sortSelect = document.getElementById('sortIncidents');
    const sortInput = document.getElementById('sortInput');
    const searchSortForm = document.getElementById('searchSortForm');

    if (sortSelect && sortInput && searchSortForm) {
        // Set initial selected option based on the current sort value
        const currentSort = sortInput.value;
        
        // Find and set the correct option as selected
        Array.from(sortSelect.options).forEach(option => {
            if (option.value === currentSort) {
                option.selected = true;
            }
        });

        // Update hidden input and submit form when sort changes
        sortSelect.addEventListener('change', function() {
            // Update the hidden input with the selected sort value
            sortInput.value = this.value;
            
            // Submit the form to reload with new sorting
            searchSortForm.submit();
        });
    }

    // Actions Dropdown Functionality
    const toggleButtons = document.querySelectorAll('.actions-toggle');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.nextElementSibling;
            // Close all other menus
            document.querySelectorAll('.actions-menu.show').forEach(m => {
                if (m !== menu) m.classList.remove('show');
            });
            menu.classList.toggle('show');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.actions-dropdown')) {
            document.querySelectorAll('.actions-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });

    // Warning dismissal function
    function dismissWarning() {
        document.getElementById('mobileWarning').style.display = 'none';
        document.querySelector('.container-fluid').style.paddingTop = '1rem';
    }
    
    // Make dismissWarning available globally
    window.dismissWarning = dismissWarning;

    // Dynamic unit filtering based on selected zone
    function updateUnitFilter() {
        const zoneSelect = document.getElementById('zoneFilter');
        const unitSelect = document.getElementById('unitFilter');
        const selectedZoneId = zoneSelect.value;

        // Reset unit options
        unitSelect.innerHTML = '<option value="">Toutes les unités</option>';

        // If no zone selected, return
        if (!selectedZoneId) return;

        // Filter units based on selected zone
        const allUnits = document.querySelectorAll('#unitFilter option');
        allUnits.forEach(unit => {
            const zoneId = unit.getAttribute('data-zone-id');
            if (zoneId === selectedZoneId) {
                unitSelect.appendChild(unit.cloneNode(true));
            }
        });
    }

    // Apply filters to the incident list
    function applyFilters() {
        const zoneSelect = document.getElementById('zoneFilter');
        const unitSelect = document.getElementById('unitFilter');
        const searchForm = document.getElementById('searchSortForm');

        // Create or update hidden inputs for zone and unit
        let zoneInput = searchForm.querySelector('input[name="zone"]');
        if (!zoneInput) {
            zoneInput = document.createElement('input');
            zoneInput.type = 'hidden';
            zoneInput.name = 'zone';
            searchForm.appendChild(zoneInput);
        }
        zoneInput.value = zoneSelect.value;

        let unitInput = searchForm.querySelector('input[name="unit"]');
        if (!unitInput) {
            unitInput = document.createElement('input');
            unitInput.type = 'hidden';
            unitInput.name = 'unit';
            searchForm.appendChild(unitInput);
        }
        unitInput.value = unitSelect.value;

        // Submit the form
        searchForm.submit();
    }

    // Add event listeners for dynamic filtering
    const zoneFilter = document.getElementById('zoneFilter');
    const unitFilter = document.getElementById('unitFilter');
    const filterButton = document.getElementById('filterButton');

    if (zoneFilter) {
        zoneFilter.addEventListener('change', updateUnitFilter);
    }

    if (filterButton) {
        filterButton.addEventListener('click', applyFilters);
    }

    // Toggle sort and filter panel
    function toggleSortFilterPanel() {
        const sortFilterPanel = document.getElementById('sortFilterPanel');
        const sortFilterToggle = document.getElementById('sortFilterToggle');

        if (sortFilterPanel.classList.contains('show')) {
            sortFilterPanel.classList.remove('show');
            sortFilterToggle.classList.remove('active');
        } else {
            sortFilterPanel.classList.add('show');
            sortFilterToggle.classList.add('active');
        }
    }

    // Add event listeners when the document is ready
    const sortFilterToggle = document.getElementById('sortFilterToggle');
    
    if (sortFilterToggle) {
        sortFilterToggle.addEventListener('click', toggleSortFilterPanel);
    }
});

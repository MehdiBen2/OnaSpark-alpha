// Infrastructure Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Update status badge color based on infrastructure state
    function updateStatusBadge() {
        const etatElement = document.getElementById('detailEtat');
        const etat = etatElement.textContent.trim().toLowerCase();
        
        // Remove existing classes
        etatElement.classList.remove('badge-success', 'badge-warning', 'badge-danger');
        
        // Add appropriate badge class based on state
        if (etat.includes('actif') || etat.includes('opérationnel')) {
            etatElement.classList.add('badge');
            etatElement.classList.add('badge-success');
        } else if (etat.includes('maintenance') || etat.includes('en cours')) {
            etatElement.classList.add('badge');
            etatElement.classList.add('badge-warning');
        } else {
            etatElement.classList.add('badge');
            etatElement.classList.add('badge-danger');
        }
    }

    // Vérifier les dépendances
    const deps = {
        jQuery: typeof jQuery !== 'undefined',
        Bootstrap: typeof bootstrap !== 'undefined',
        DataTables: typeof $.fn.DataTable !== 'undefined'
    };

    // Initialiser uniquement si toutes les dépendances sont chargées
    if (Object.values(deps).every(Boolean)) {
        // Initialiser DataTable
        if (document.getElementById('infrastructuresTable')) {
            const infrastructuresTable = $('#infrastructuresTable').DataTable({
                responsive: true,
                language: {
                    paginate: {
                        first: '&laquo;',
                        last: '&raquo;',
                        next: '&rsaquo;',
                        previous: '&lsaquo;'
                    },
                    search: 'Rechercher:',
                    lengthMenu: 'Afficher _MENU_ entrées',
                    info: 'Affichage de _START_ à _END_ sur _TOTAL_ entrées',
                    infoEmpty: 'Aucune donnée disponible',
                    infoFiltered: '(filtré de _MAX_ entrées totales)',
                    zeroRecords: 'Aucun résultat trouvé'
                },
                // Disable default search
                searching: false,
                // Disable length menu
                lengthChange: false,
                // Default page length
                pageLength: 10,
                // Possible page lengths
                lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Tout"]]
            });

            // Length menu event handler
            const lengthSelect = document.querySelector('select[name="infrastructuresTable_length"]');
            if (lengthSelect) {
                lengthSelect.addEventListener('change', function() {
                    infrastructuresTable.page.len(parseInt(this.value)).draw();
                });
            }

            // Custom search input functionality
            const customSearchInput = document.getElementById('customSearchInput');
            if (customSearchInput) {
                customSearchInput.addEventListener('keyup', function() {
                    const searchTerm = this.value.toLowerCase();
                    
                    // Custom search across multiple columns
                    infrastructuresTable.rows().every(function() {
                        const rowData = this.data();
                        const match = Object.values(rowData).some(value => 
                            String(value).toLowerCase().includes(searchTerm)
                        );
                        
                        this.nodes().to$().toggle(match);
                    });
                    
                    // Update table info and pagination
                    infrastructuresTable.draw(false);
                });
            }
        }

        // Gestionnaire d'enregistrement d'infrastructure
        const saveButton = document.querySelector('#saveInfrastructureBtn');
        if (saveButton) {
            // Add type selection handler
            const typeSelect = document.getElementById('type');
            const epurationTypeContainer = document.getElementById('epurationType-container');
            const epurationTypeSelect = document.getElementById('epurationType');

            typeSelect.addEventListener('change', function() {
                if (this.value === 'STEP') {
                    epurationTypeContainer.classList.remove('d-none');
                    epurationTypeSelect.required = true;
                } else {
                    epurationTypeContainer.classList.add('d-none');
                    epurationTypeSelect.required = false;
                    epurationTypeSelect.value = ''; // Reset selection
                }
            });

            saveButton.addEventListener('click', function(event) {
                event.preventDefault();

                const formData = {
                    nom: document.getElementById('nom').value,
                    type: typeSelect.value,
                    localisation: document.getElementById('localisation').value,
                    capacite: document.getElementById('capacite').value,
                    etat: document.getElementById('etat').value
                };

                // Add epuration type for Station d'Épuration
                if (formData.type === 'STEP') {
                    formData.epurationType = epurationTypeSelect.value;
                }

                // Valider les données du formulaire
                const missingFields = Object.entries(formData)
                    .filter(([_, value]) => !value)
                    .map(([key]) => key);

                if (missingFields.length > 0) {
                    alert('Veuillez remplir tous les champs: ' + missingFields.join(', '));
                    return;
                }

                // Envoyer la requête
                fetch('/departements/infrastructure/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => {
                    // Check if response is not OK
                    if (!response.ok) {
                        // Try to parse error response as JSON
                        return response.text().then(text => {
                            try {
                                const errorData = JSON.parse(text);
                                throw new Error(errorData.message || errorData.error || 'Erreur de création');
                            } catch (jsonError) {
                                // If parsing fails, throw the original text
                                throw new Error(text || 'Erreur de création non spécifiée');
                            }
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.message) {
                        // Show success toast or alert
                        const successToast = document.getElementById('successToast');
                        if (successToast) {
                            const successMessage = document.getElementById('successToastMessage');
                            if (successMessage) {
                                successMessage.textContent = data.message;
                            }
                            new bootstrap.Toast(successToast).show();
                        } else {
                            alert(data.message);
                        }
                        
                        const modal = bootstrap.Modal.getInstance(document.getElementById('infrastructureModal'));
                        if (modal) {
                            modal.hide();
                        }
                        location.reload();
                    }
                })
                .catch(error => {
                    console.error('Erreur de création:', error);
                    
                    // Show error toast or alert
                    const errorToast = document.getElementById('errorToast');
                    if (errorToast) {
                        const errorMessage = document.getElementById('errorToastMessage');
                        if (errorMessage) {
                            errorMessage.textContent = `Erreur lors de la création de l'infrastructure: ${error.message || 'Erreur inconnue'}`;
                        }
                        new bootstrap.Toast(errorToast).show();
                    } else {
                        alert(`Erreur lors de la création de l'infrastructure: ${error.message || 'Erreur inconnue'}`);
                    }
                });
            });
        }

        // Gestionnaire de suppression d'infrastructure
        const deleteButtons = document.querySelectorAll('.delete-infrastructure');
        let currentInfrastructureId = null;
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                currentInfrastructureId = this.getAttribute('data-id');
            });
        });

        // Confirmation de suppression dans le modal
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        const deleteButtonText = confirmDeleteBtn.querySelector('.delete-btn-text');
        const deleteSpinner = confirmDeleteBtn.querySelector('.delete-spinner');
        
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', function(event) {
                if (!currentInfrastructureId) {
                    console.error('Aucun ID d\'infrastructure sélectionné');
                    return;
                }

                // Disable button and show spinner
                confirmDeleteBtn.disabled = true;
                deleteButtonText.classList.add('d-none');
                deleteSpinner.classList.remove('d-none');

                // Mandatory 2-second delay before deletion
                setTimeout(() => {
                    // Envoyer la requête de suppression
                    fetch(`/departements/infrastructure/delete/${currentInfrastructureId}`, {
                        method: 'DELETE',
                        headers: {
                            'Accept': 'application/json'
                        }
                    })
                    .then(response => {
                        // Check if response is not OK
                        if (!response.ok) {
                            // Try to parse error response as JSON
                            return response.text().then(text => {
                                try {
                                    const errorData = JSON.parse(text);
                                    throw new Error(errorData.message || 'Erreur de suppression');
                                } catch (jsonError) {
                                    // If parsing fails, throw the original text
                                    throw new Error(text || 'Erreur de suppression non spécifiée');
                                }
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Show success toast
                        const successToast = document.getElementById('successToast');
                        if (successToast) {
                            const successMessage = document.getElementById('successToastMessage');
                            if (successMessage) {
                                successMessage.textContent = data.message || 'Infrastructure et fichiers supprimés avec succès';
                            }
                            new bootstrap.Toast(successToast).show();
                        } else {
                            alert(data.message || 'Infrastructure et fichiers supprimés avec succès');
                        }

                        // Hide the delete modal
                        const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                        if (deleteModal) {
                            deleteModal.hide();
                        }

                        // Reload the page or remove the row from the table
                        location.reload();
                    })
                    .catch(error => {
                        console.error('Erreur de suppression:', error);
                        
                        // Show error toast or alert
                        const errorToast = document.getElementById('errorToast');
                        if (errorToast) {
                            const errorMessage = document.getElementById('errorToastMessage');
                            if (errorMessage) {
                                errorMessage.textContent = `Erreur lors de la suppression de l'infrastructure: ${error.message || 'Erreur inconnue'}`;
                            }
                            new bootstrap.Toast(errorToast).show();
                        } else {
                            alert(`Erreur lors de la suppression de l'infrastructure: ${error.message || 'Erreur inconnue'}`);
                        }
                    })
                    .finally(() => {
                        // Re-enable button and hide spinner
                        confirmDeleteBtn.disabled = false;
                        deleteButtonText.classList.remove('d-none');
                        deleteSpinner.classList.add('d-none');
                    });
                }, 2000); // 2-second mandatory delay
            });
        }

        // Function to fetch and display infrastructure files
        function fetchInfrastructureFiles(infrastructureId) {
            const existingFilesContainer = document.getElementById('existingFilesContainer');
            existingFilesContainer.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
            `;

            fetch(`/departements/infrastructure/${infrastructureId}/files`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Impossible de récupérer les fichiers');
                }
                return response.json();
            })
            .then(filesData => {
                const existingFilesContainer = document.getElementById('existingFilesContainer');
                existingFilesContainer.innerHTML = '';

                if (filesData.files.length === 0) {
                    existingFilesContainer.innerHTML = `
                        <div class="no-files-placeholder">
                            <i class="fas fa-folder-open fa-3x opacity-50 mb-3"></i>
                            <p>Aucun fichier téléchargé</p>
                        </div>
                    `;
                    return;
                }

                const imageFiles = filesData.files.filter(file => file.type.startsWith('image'));
                const pdfFiles = filesData.files.filter(file => file.type === 'pdf');

                const tabContainer = createFileTabContainer(imageFiles, pdfFiles);
                existingFilesContainer.appendChild(tabContainer.container);

                const contentContainer = document.createElement('div');
                contentContainer.classList.add('file-content');

                const imageContent = createFileGrid(imageFiles);
                const pdfContent = createFileGrid(pdfFiles);

                contentContainer.appendChild(imageContent);
                existingFilesContainer.appendChild(contentContainer);

                setupTabSwitching(imageContent, pdfContent, tabContainer.imageTab, tabContainer.pdfTab, contentContainer);
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des fichiers:', error);
                const existingFilesContainer = document.getElementById('existingFilesContainer');
                existingFilesContainer.innerHTML = `
                    <div class="no-files-placeholder text-danger">
                        <i class="fas fa-exclamation-triangle fa-3x mb-3 opacity-50"></i>
                        <p>Impossible de charger les fichiers</p>
                        <small>${error.message}</small>
                    </div>
                `;
            });
        }

        function createFileTabContainer(imageFiles, pdfFiles) {
            // Create tabs container
            const tabContainer = document.createElement('div');
            tabContainer.classList.add('file-tabs-container');
            
            // Create tabs section
            const tabsSection = document.createElement('div');
            tabsSection.classList.add('file-tabs');
            
            // Create info section
            const infoSection = document.createElement('div');
            infoSection.classList.add('file-tabs-info');
            
            // Create image tab
            const imageTab = document.createElement('button');
            imageTab.classList.add('btn', 'btn-outline-primary', 'active');
            imageTab.id = 'imageTab';
            imageTab.innerHTML = `
                <i class="fas fa-file-image me-2"></i>
                Images (${imageFiles.length})
            `;
            
            // Create PDF tab
            const pdfTab = document.createElement('button');
            pdfTab.classList.add('btn', 'btn-outline-primary');
            pdfTab.id = 'pdfTab';
            pdfTab.innerHTML = `
                <i class="fas fa-file-pdf me-2"></i>
                PDFs (${pdfFiles.length})
            `;
            
            // Create info text
            infoSection.innerHTML = `
                <i class="fas fa-info-circle"></i>
                Affichage de tous les fichiers
            `;
            
            // Append tabs to container
            tabsSection.appendChild(imageTab);
            tabsSection.appendChild(pdfTab);
            
            tabContainer.appendChild(tabsSection);
            tabContainer.appendChild(infoSection);
            
            return {
                container: tabContainer,
                imageTab: imageTab,
                pdfTab: pdfTab
            };
        }

        function setupTabSwitching(imageContent, pdfContent, imageTab, pdfTab, contentContainer) {
            imageTab.addEventListener('click', () => {
                // Remove active class from both tabs
                imageTab.classList.add('active');
                pdfTab.classList.remove('active');
                
                // Switch content
                contentContainer.innerHTML = '';
                contentContainer.appendChild(imageContent);
            });

            pdfTab.addEventListener('click', () => {
                // Remove active class from both tabs
                pdfTab.classList.add('active');
                imageTab.classList.remove('active');
                
                // Switch content
                contentContainer.innerHTML = '';
                contentContainer.appendChild(pdfContent);
            });
        }

        function createFileGrid(files) {
            const grid = document.createElement('div');
            grid.classList.add('iphone-gallery-grid');

            // Adjust grid columns based on number of files
            const fileCount = files.length;
            if (fileCount <= 2) {
                grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
            } else if (fileCount <= 4) {
                grid.style.gridTemplateColumns = 'repeat(3, 1fr)';
            } else if (fileCount <= 6) {
                grid.style.gridTemplateColumns = 'repeat(4, 1fr)';
            } else {
                grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(100px, 1fr))';
            }

            files.forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.classList.add('gallery-item');
                
                if (file.type.startsWith('image')) {
                    fileItem.innerHTML = `
                        <div class="gallery-item-content">
                            <img src="${file.path}" alt="${file.name}" data-full-path="${file.path}">
                            <div class="gallery-item-overlay">
                                <div class="gallery-item-details">
                                    <span class="gallery-item-name text-truncate">${file.name}</span>
                                    <div class="gallery-item-actions">
                                        <button class="btn btn-sm btn-light view-image" data-index="${index}">
                                            <i class="fas fa-expand"></i>
                                        </button>
                                        <a href="${file.path}" class="btn btn-sm btn-light" download>
                                            <i class="fas fa-download"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    fileItem.innerHTML = `
                        <div class="gallery-item-content pdf-item">
                            <div class="pdf-icon">
                                <i class="fas fa-file-pdf"></i>
                            </div>
                            <div class="gallery-item-overlay">
                                <div class="gallery-item-details">
                                    <span class="gallery-item-name text-truncate">${file.name}</span>
                                    <div class="gallery-item-actions">
                                        <a href="${file.path}" class="btn btn-sm btn-light" download>
                                            <i class="fas fa-download"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                grid.appendChild(fileItem);
            });

            return grid;
        }

        // Infrastructure row click handler
        const infrastructureRows = document.querySelectorAll('.infrastructure-row');
        infrastructureRows.forEach(row => {
            row.addEventListener('click', function(event) {
                // Prevent triggering if action buttons were clicked
                if (event.target.closest('.btn-group')) return;

                // Get infrastructure ID from the clicked row
                const infrastructureId = this.getAttribute('data-id');
                
                // Fetch infrastructure details
                fetch(`/departements/infrastructure/${infrastructureId}/details`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Impossible de récupérer les détails');
                    }
                    return response.json();
                })
                .then(data => {
                    // Populate modal with infrastructure details
                    document.getElementById('detailNom').textContent = data.nom;
                    document.getElementById('detailType').textContent = data.type;
                    document.getElementById('detailLocalisation').textContent = data.localisation;
                    document.getElementById('detailCapacite').textContent = data.capacite;
                    document.getElementById('detailEtat').textContent = data.etat;

                    // Fetch and display existing files
                    fetchInfrastructureFiles(infrastructureId);

                    // Set infrastructure ID on modal
                    document.getElementById('infrastructureDetailsModal').setAttribute('data-infrastructure-id', infrastructureId);

                    // Show the modal
                    const infrastructureDetailsModal = new bootstrap.Modal(document.getElementById('infrastructureDetailsModal'));
                    infrastructureDetailsModal.show();
                })
                .catch(error => {
                    console.error('Erreur lors de la récupération des détails:', error);
                    alert('Impossible de charger les détails de l\'infrastructure');
                });
            });
        });

        // File upload handler
        const documentUpload = document.getElementById('documentUpload');
        const uploadedFilesList = document.getElementById('uploadedFilesList');
        
        documentUpload.addEventListener('change', function(event) {
            uploadedFilesList.innerHTML = ''; // Clear previous list
            
            Array.from(this.files).forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.classList.add('d-flex', 'justify-content-between', 'align-items-center', 'mb-2');
                fileItem.innerHTML = `
                    <span>
                        <i class="fas ${file.type.includes('pdf') ? 'fa-file-pdf' : 'fa-file-image'} me-2"></i>
                        ${file.name} (${(file.size / 1024).toFixed(2)} Ko)
                    </span>
                    <button type="button" class="btn btn-sm btn-danger remove-file" data-filename="${file.name}">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                uploadedFilesList.appendChild(fileItem);

                // Remove file functionality
                fileItem.querySelector('.remove-file').addEventListener('click', function() {
                    const fileName = this.getAttribute('data-filename');
                    const updatedFiles = Array.from(documentUpload.files).filter(f => f.name !== fileName);
                    
                    // Create a new FileList
                    const dataTransfer = new DataTransfer();
                    updatedFiles.forEach(file => dataTransfer.items.add(file));
                    
                    documentUpload.files = dataTransfer.files;
                    fileItem.remove();
                });
            });
        });

        // Add save infrastructure details handler
        const saveInfrastructureDetailsBtn = document.getElementById('saveInfrastructureDetailsBtn');
        if (saveInfrastructureDetailsBtn) {
            saveInfrastructureDetailsBtn.addEventListener('click', async function(event) {
                event.preventDefault();
                const originalBtnText = this.innerHTML;
                
                try {
                    // Show loading state
                    this.innerHTML = `
                        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Enregistrement...
                    `;
                    this.disabled = true;

                    // Get modal content for overlay
                    const modalContent = document.getElementById('infrastructureDetailsModal').querySelector('.modal-content');
                    if (!modalContent) {
                        throw new Error('Modal content not found');
                    }

                    // Create loading overlay
                    const loadingOverlay = document.createElement('div');
                    loadingOverlay.classList.add('loading-overlay', 'position-absolute', 'top-0', 'start-0', 'w-100', 'h-100', 'd-flex', 'justify-content-center', 'align-items-center', 'bg-light', 'bg-opacity-75');
                    loadingOverlay.innerHTML = `
                        <div class="text-center">
                            <div class="spinner-grow text-primary" role="status">
                                <span class="visually-hidden">Chargement...</span>
                            </div>
                        </div>
                    `;
                    modalContent.style.position = 'relative';
                    modalContent.appendChild(loadingOverlay);

                    // Get infrastructure ID
                    const infrastructureId = document.getElementById('infrastructureDetailsModal').getAttribute('data-infrastructure-id');
                    if (!infrastructureId) {
                        throw new Error('Aucune infrastructure sélectionnée');
                    }

                    // Get file input and prepare form data
                    const documentUpload = document.getElementById('documentUpload');
                    const files = documentUpload.files;

                    const formData = new FormData();
                    formData.append('infrastructure_id', infrastructureId);
                    
                    // Append files
                    for (let i = 0; i < files.length; i++) {
                        formData.append('files', files[i]);
                    }

                    // Use the correct route with infrastructure ID
                    const uploadResponse = await fetch(`/departements/infrastructure/${infrastructureId}/upload-files`, {
                        method: 'POST',
                        body: formData
                    });

                    if (!uploadResponse.ok) {
                        const errorData = await uploadResponse.json();
                        throw new Error(errorData.error || 'Erreur lors du téléchargement');
                    }

                    const uploadData = await uploadResponse.json();
                    
                    // Reset file input and list
                    documentUpload.value = '';
                    const uploadedFilesList = document.getElementById('uploadedFilesList');
                    if (uploadedFilesList) uploadedFilesList.innerHTML = '';

                    // Fetch updated file list
                    await fetchInfrastructureFiles(infrastructureId);

                    // Remove loading overlay
                    modalContent.querySelector('.loading-overlay').remove();

                    // Show success message
                    const successToastEl = document.getElementById('successToast');
                    if (successToastEl) {
                        const messageEl = successToastEl.querySelector('.toast-body');
                        if (messageEl) {
                            messageEl.textContent = uploadData.message || 'Fichiers téléchargés avec succès';
                        }
                        bootstrap.Toast.getOrCreateInstance(successToastEl).show();
                    }

                } catch (error) {
                    console.error('Erreur:', error);
                    
                    // Remove loading overlay
                    modalContent.querySelector('.loading-overlay').remove();

                    // Show error message
                    const errorToastEl = document.getElementById('errorToast');
                    if (errorToastEl) {
                        const messageEl = errorToastEl.querySelector('.toast-body');
                        if (messageEl) {
                            messageEl.textContent = error instanceof Error ? error.message : 'Erreur lors du téléchargement des fichiers';
                        }
                        bootstrap.Toast.getOrCreateInstance(errorToastEl).show();
                    }

                } finally {
                    // Remove loading state
                    saveInfrastructureDetailsBtn.innerHTML = originalBtnText;
                    saveInfrastructureDetailsBtn.disabled = false;
                }
            });
        }

        // Remove Connect to STEP button handler
        const connectStepBtn = document.getElementById('connectStepBtn');
        if (connectStepBtn) {
            connectStepBtn.removeEventListener('click', function() {
                const typeSelect = document.getElementById('type');
                
                // Ensure STEP is selected
                if (typeSelect.value !== 'STEP') {
                    // Show error toast
                    const errorToastEl = document.getElementById('errorToast');
                    if (errorToastEl) {
                        const messageEl = errorToastEl.querySelector('.toast-body');
                        if (messageEl) {
                            messageEl.textContent = 'Veuillez sélectionner "Station d\'épuration" avant de connecter';
                        }
                        bootstrap.Toast.getOrCreateInstance(errorToastEl).show();
                    }
                    return;
                }

                // Open modal or perform connection logic
                const connectStepModal = new bootstrap.Modal(document.getElementById('connectStepModal'), {
                    keyboard: false
                });
                connectStepModal.show();
            });
            connectStepBtn.remove(); // Remove the button from the DOM
        }

        // Remove STEP Connection Configuration Modal Handler
        const saveStepConnectionConfigBtn = document.getElementById('saveStepConnectionConfigBtn');
        const toggleStepPasswordBtn = document.getElementById('toggleStepPassword');

        if (toggleStepPasswordBtn) {
            toggleStepPasswordBtn.removeEventListener('click', function() {
                const stepPasswordInput = document.getElementById('stepPassword');
                const type = stepPasswordInput.type === 'password' ? 'text' : 'password';
                stepPasswordInput.type = type;
                this.querySelector('i').classList.toggle('fa-eye');
                this.querySelector('i').classList.toggle('fa-eye-slash');
            });
            toggleStepPasswordBtn.remove();
        }

        if (saveStepConnectionConfigBtn) {
            saveStepConnectionConfigBtn.removeEventListener('click', function(event) {
                // Remove entire STEP connection configuration logic
            });
            saveStepConnectionConfigBtn.remove();
        }

        // Existing fetchInfrastructureFiles function (from previous implementation)
        function fetchInfrastructureFiles(infrastructureId) {
            const existingFilesContainer = document.getElementById('existingFilesContainer');
            if (!existingFilesContainer) return Promise.resolve();

            existingFilesContainer.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
            `;

            return fetch(`/departements/infrastructure/${infrastructureId}/files`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Impossible de récupérer les fichiers');
                }
                return response.json();
            })
            .then(filesData => {
                const existingFilesContainer = document.getElementById('existingFilesContainer');
                existingFilesContainer.innerHTML = '';

                if (filesData.files.length === 0) {
                    existingFilesContainer.innerHTML = `
                        <div class="no-files-placeholder">
                            <i class="fas fa-folder-open fa-3x opacity-50 mb-3"></i>
                            <p>Aucun fichier téléchargé</p>
                        </div>
                    `;
                    return;
                }

                const imageFiles = filesData.files.filter(file => file.type.startsWith('image'));
                const pdfFiles = filesData.files.filter(file => file.type === 'pdf');

                const tabContainer = createFileTabContainer(imageFiles, pdfFiles);
                existingFilesContainer.appendChild(tabContainer.container);

                const contentContainer = document.createElement('div');
                contentContainer.classList.add('file-content');

                const imageContent = createFileGrid(imageFiles);
                const pdfContent = createFileGrid(pdfFiles);

                contentContainer.appendChild(imageContent);
                existingFilesContainer.appendChild(contentContainer);

                setupTabSwitching(imageContent, pdfContent, tabContainer.imageTab, tabContainer.pdfTab, contentContainer);
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des fichiers:', error);
                existingFilesContainer.innerHTML = `
                    <div class="no-files-placeholder text-danger">
                        <i class="fas fa-exclamation-triangle fa-3x mb-3 opacity-50"></i>
                        <p>Impossible de charger les fichiers</p>
                        <small>${error.message}</small>
                    </div>
                `;
            });
        }

        // Existing helper functions for file tab and grid creation
        function createFileTabContainer(imageFiles, pdfFiles) {
            const tabContainer = document.createElement('div');
            tabContainer.classList.add('file-tabs-container');
            
            const tabsSection = document.createElement('div');
            tabsSection.classList.add('file-tabs');
            
            const infoSection = document.createElement('div');
            infoSection.classList.add('file-tabs-info');
            
            const imageTab = document.createElement('button');
            imageTab.classList.add('btn', 'btn-outline-primary', 'active');
            imageTab.id = 'imageTab';
            imageTab.innerHTML = `
                <i class="fas fa-file-image me-2"></i>
                Images (${imageFiles.length})
            `;
            
            const pdfTab = document.createElement('button');
            pdfTab.classList.add('btn', 'btn-outline-primary');
            pdfTab.id = 'pdfTab';
            pdfTab.innerHTML = `
                <i class="fas fa-file-pdf me-2"></i>
                PDFs (${pdfFiles.length})
            `;
            
            infoSection.innerHTML = `
                <i class="fas fa-info-circle"></i>
                Affichage de tous les fichiers
            `;
            
            tabsSection.appendChild(imageTab);
            tabsSection.appendChild(pdfTab);
            
            tabContainer.appendChild(tabsSection);
            tabContainer.appendChild(infoSection);
            
            return {
                container: tabContainer,
                imageTab: imageTab,
                pdfTab: pdfTab
            };
        }

        function setupTabSwitching(imageContent, pdfContent, imageTab, pdfTab, contentContainer) {
            imageTab.addEventListener('click', () => {
                imageTab.classList.add('active');
                pdfTab.classList.remove('active');
                contentContainer.innerHTML = '';
                contentContainer.appendChild(imageContent);
            });

            pdfTab.addEventListener('click', () => {
                pdfTab.classList.add('active');
                imageTab.classList.remove('active');
                contentContainer.innerHTML = '';
                contentContainer.appendChild(pdfContent);
            });
        }

        function createFileGrid(files) {
            const grid = document.createElement('div');
            grid.classList.add('iphone-gallery-grid');

            const fileCount = files.length;
            if (fileCount <= 2) {
                grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
            } else if (fileCount <= 4) {
                grid.style.gridTemplateColumns = 'repeat(3, 1fr)';
            } else if (fileCount <= 6) {
                grid.style.gridTemplateColumns = 'repeat(4, 1fr)';
            } else {
                grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(100px, 1fr))';
            }

            files.forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.classList.add('gallery-item');
                
                if (file.type.startsWith('image')) {
                    fileItem.innerHTML = `
                        <div class="gallery-item-content">
                            <img src="${file.path}" alt="${file.name}" data-full-path="${file.path}">
                            <div class="gallery-item-overlay">
                                <div class="gallery-item-details">
                                    <span class="gallery-item-name text-truncate">${file.name}</span>
                                    <div class="gallery-item-actions">
                                        <button class="btn btn-sm btn-light view-image" data-index="${index}">
                                            <i class="fas fa-expand"></i>
                                        </button>
                                        <a href="${file.path}" class="btn btn-sm btn-light" download>
                                            <i class="fas fa-download"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    fileItem.innerHTML = `
                        <div class="gallery-item-content pdf-item">
                            <div class="pdf-icon">
                                <i class="fas fa-file-pdf"></i>
                            </div>
                            <div class="gallery-item-overlay">
                                <div class="gallery-item-details">
                                    <span class="gallery-item-name text-truncate">${file.name}</span>
                                    <div class="gallery-item-actions">
                                        <a href="${file.path}" class="btn btn-sm btn-light" download>
                                            <i class="fas fa-download"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                grid.appendChild(fileItem);
            });

            return grid;
        }

        // Add lightbox functionality for image viewing
        function setupImageLightbox() {
            const lightboxModal = document.getElementById('imageLightboxModal');
            const lightboxImage = document.getElementById('lightboxImage');
            const lightboxImageTitle = document.getElementById('lightboxImageTitle');
            const lightboxDownloadLink = document.getElementById('lightboxDownloadLink');

            // Delegate event listener for view-image buttons
            document.addEventListener('click', function(event) {
                const viewImageButton = event.target.closest('.view-image');
                if (viewImageButton) {
                    event.preventDefault();
                    const imageContainer = viewImageButton.closest('.gallery-item');
                    const imageElement = imageContainer.querySelector('img');
                    
                    if (imageElement) {
                        const imageSrc = imageElement.src;
                        const imageTitle = imageElement.alt || 'Image';

                        // Set lightbox image source and title
                        lightboxImage.src = imageSrc;
                        lightboxImageTitle.textContent = imageTitle;
                        
                        // Update download link
                        lightboxDownloadLink.href = imageSrc;
                        
                        // Show the lightbox modal
                        const lightboxModalInstance = new bootstrap.Modal(lightboxModal);
                        lightboxModalInstance.show();
                    }
                }
            });
        }

        setupImageLightbox();

        // Trigger status badge update after details are loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Check if details are already loaded
            const etatElement = document.getElementById('detailEtat');
            if (etatElement && etatElement.textContent.trim()) {
                updateStatusBadge();
            }
        });
    }

    // Trigger status badge update after details are loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Check if details are already loaded
        const etatElement = document.getElementById('detailEtat');
        if (etatElement && etatElement.textContent.trim()) {
            updateStatusBadge();
        }
    });
});

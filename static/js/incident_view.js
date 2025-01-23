// incident_view.js: Handles incident view page interactions

// Utility function to retrieve cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Utility function to parse markdown with improved handling
function parseMarkdown(text) {
    if (!text) return 'Aucune explication disponible.';
    
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>')  // Italic
        .replace(/### (.*)/g, '<h3>$1</h3>')   // H3 headers
        .replace(/## (.*)/g, '<h2>$1</h2>')    // H2 headers
        .replace(/# (.*)/g, '<h1>$1</h1>')     // H1 headers
        .replace(/- (.*)/g, '<li>$1</li>')     // List items
        .replace(/<\/li><li>/g, '</li>\n<li>') // Separate list items
        .replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>') // Wrap list items in ul
        .replace(/\n\n/g, '</p><p>')  // Paragraph breaks
        .replace(/^(.+)$/gm, '<p>$1</p>');  // Wrap each line in paragraph
}

// Comprehensive coordinate extraction and validation
function validateAndExtractCoordinates(coords) {
    console.group('Coordinate Validation');
    console.log('Input coordinates:', coords);
    console.log('Type of coordinates:', typeof coords);
    console.log('Is array:', Array.isArray(coords));
    
    if (!coords) {
        console.error('No coordinates provided');
        console.groupEnd();
        return null;
    }

    // Deep inspection of coordinate structure
    function inspectCoordinateStructure(arr, depth = 0) {
        if (!Array.isArray(arr)) {
            console.warn(`Not an array at depth ${depth}:`, arr);
            return false;
        }

        console.log(`Depth ${depth} - Array length:`, arr.length);
        console.log(`Depth ${depth} - First element type:`, typeof arr[0]);

        if (arr.length === 0) {
            console.warn(`Empty array at depth ${depth}`);
            return false;
        }

        // Extract coordinates from potential object structure
        function extractCoordinate(item) {
            // If it's already a coordinate pair
            if (Array.isArray(item) && item.length === 2 && 
                typeof item[0] === 'number' && typeof item[1] === 'number') {
                return item;
            }
            
            // If it's an object with lat/lng or coordinates
            if (typeof item === 'object') {
                if ('lat' in item && 'lng' in item) {
                    return [item.lat, item.lng];
                }
                if ('coordinates' in item && Array.isArray(item.coordinates) && item.coordinates.length === 2) {
                    return item.coordinates;
                }
            }
            
            return null;
        }

        // Try to extract coordinates
        const extractedCoords = arr.map(extractCoordinate).filter(coord => coord !== null);

        if (extractedCoords.length > 0) {
            console.log(`Valid coordinate array found at depth ${depth}:`, extractedCoords);
            return extractedCoords;
        }

        // Recursively inspect nested arrays
        for (let item of arr) {
            if (Array.isArray(item)) {
                const result = inspectCoordinateStructure(item, depth + 1);
                if (result) return result;
            }
        }

        console.warn(`No valid coordinates found at depth ${depth}`);
        return false;
    }

    const validCoords = inspectCoordinateStructure(coords);
    
    console.groupEnd();
    return validCoords || null;
}

// Function to initialize map with incident details
function initializeIncidentMap(mapElementId, defaultLat, defaultLng, incidentLat, incidentLng, drawnShapes = null) {
    const map = L.map(mapElementId).setView([defaultLat, defaultLng], 10);
    
    // Add base map layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Add marker for incident location if coordinates exist
    if (incidentLat && incidentLng) {
        L.marker([incidentLat, incidentLng])
            .addTo(map)
            .bindPopup('Localisation de l\'incident')
            .openPopup();
    }

    // Add drawn shapes if they exist
    function addDrawnShapesToMap(shapes) {
        console.group('Drawn Shapes Processing');
        console.log('Raw Drawn Shapes:', shapes);
        
        if (!Array.isArray(shapes)) {
            console.error('Drawn shapes is not an array:', shapes);
            return;
        }
        
        const allDrawnShapes = [];
        
        shapes.forEach((shape, index) => {
            console.group(`Shape ${index}`);
            console.log('Shape details:', shape);
            
            let drawnShape = null;
            try {
                const validCoords = validateAndExtractCoordinates(shape.coordinates);
                
                if (!validCoords) {
                    console.error(`Invalid coordinates for shape ${index}`);
                    console.groupEnd();
                    return;
                }

                if (shape.type === 'Polygon') {
                    const polygonCoords = validCoords.map(coord => {
                        return coord.length === 2 ? [coord[1], coord[0]] : coord;
                    });

                    drawnShape = L.polygon(polygonCoords, {
                        color: 'red',
                        fillColor: '#f03',
                        fillOpacity: 0.2
                    }).addTo(map);
                } else if (shape.type === 'Rectangle') {
                    const rectangleCoords = validCoords.map(coord => {
                        return coord.length === 2 ? [coord[1], coord[0]] : coord;
                    });

                    drawnShape = L.rectangle(rectangleCoords, {
                        color: 'blue',
                        fillColor: '#30f',
                        fillOpacity: 0.2
                    }).addTo(map);
                } else if (shape.type === 'Circle') {
                    const centerCoord = validCoords[0];
                    const circleCenter = centerCoord.length === 2 
                        ? [centerCoord[1], centerCoord[0]]  
                        : centerCoord;

                    drawnShape = L.circle(circleCenter, {
                        radius: shape.radius || 100,  
                        color: 'green',
                        fillColor: '#3f0',
                        fillOpacity: 0.2
                    }).addTo(map);
                } else {
                    console.warn('Unknown shape type:', shape.type);
                }
                
                if (drawnShape) {
                    drawnShape.bindPopup(`Type: ${shape.type}`);
                    allDrawnShapes.push(drawnShape);
                }
            } catch (error) {
                console.error(`Error processing shape ${index}:`, error);
            }
            
            console.groupEnd();
        });

        // Fit map to bounds of drawn shapes if any exist
        if (allDrawnShapes.length > 0) {
            const group = new L.featureGroup(allDrawnShapes);
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    // Add drawn shapes if provided
    if (drawnShapes) {
        addDrawnShapesToMap(drawnShapes);
    }

    console.groupEnd();
    map.invalidateSize();
    map.fitBounds(map.getBounds().pad(0.2));

    return map;
}

// Function to handle AI explanation card animation
function startAIExplanationAnimation(card) {
    card.classList.add('loading');
    
    const overlay = document.createElement('div');
    overlay.className = 'ai-explanation-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spark">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spark-icon">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
            </div>
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <p class="loading-text">Spark analyse vos données d'incident...</p>
        </div>
    `;
    card.appendChild(overlay);

    const content = card.querySelector('.card-body');
    if (content) {
        content.style.transform = 'scale(0.98)';
        content.style.transition = 'transform 0.5s ease';
    }
}

function stopAIExplanationAnimation(card) {
    const content = card.querySelector('.card-body');
    if (content) {
        content.style.transform = 'scale(1)';
    }

    const overlay = card.querySelector('.ai-explanation-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.3s ease';
        
        setTimeout(() => {
            card.classList.remove('loading');
            overlay.remove();
        }, 300);
    } else {
        card.classList.remove('loading');
    }
}

// Main initialization function for incident view page
document.addEventListener('DOMContentLoaded', function() {
    const mapModal = document.getElementById('mapModal');
    const aiExplanationBtn = document.getElementById('ai-explanation-btn');
    const aiExplanationResult = document.getElementById('ai-explanation-result');
    const deepAnalysisSPARKBtn = document.getElementById('deep-analysis-spark-btn');
    const incidentHeader = document.querySelector('.incident-header');
    
    // Get incident ID from URL
    const urlParts = window.location.pathname.split('/');
    const incidentId = urlParts[urlParts.length - 1];

    let incidentMap = null;

    // Map modal initialization
    if (mapModal) {
        mapModal.addEventListener('shown.bs.modal', function () {
            if (!incidentMap) {
                const defaultLat = window.incidentLat || 36.7538;
                const defaultLng = window.incidentLng || 3.0588;
                const drawnShapes = window.drawnShapes || null;

                incidentMap = initializeIncidentMap(
                    'incident-map', 
                    defaultLat, 
                    defaultLng, 
                    window.incidentLat, 
                    window.incidentLng, 
                    drawnShapes
                );
            }
        });

        mapModal.addEventListener('show.bs.modal', function () {
            setTimeout(() => {
                if (incidentMap) {
                    incidentMap.invalidateSize();
                }
            }, 200);
        });
    }

    // AI Explanation button handler
    if (aiExplanationBtn) {
        aiExplanationBtn.addEventListener('click', async function() {
            try {
                const natureCard = document.querySelector('.nature-cause-card');
                
                if (natureCard) {
                    startAIExplanationAnimation(natureCard);
                }

                aiExplanationBtn.disabled = true;

                const response = await fetch('/get_ai_explanation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        nature_cause: document.querySelector('.nature-cause-card .incident-description')?.textContent.trim() || '',
                        incident_id: incidentId
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (natureCard) {
                    stopAIExplanationAnimation(natureCard);
                }

                if (aiExplanationResult) {
                    aiExplanationResult.innerHTML = `
                        <div class="card ai-explanation-card" style="
                            background-image: url('/static/images/onabg/cardbg.png');
                            background-size: cover;
                            background-position: center;
                            background-repeat: no-repeat;
                            position: relative;
                            overflow: hidden;
                        ">
                            <div class="card-body-overlay" style="
                                position: absolute;
                                top: 0;
                                left: 0;
                                width: 100%;
                                height: 100%;
                                background: rgba(0, 0, 0, 0.3);
                                z-index: 1;
                            "></div>
                            <div class="card-body" style="
                                position: relative;
                                z-index: 2;
                                color: white;
                            ">
                                <h5 class="card-title" style="font-size: 1.25rem;">Analyse Spark</h5>
                                <p class="card-text" style="
                                    font-size: 3rem; 
                                    line-height: 1.2;
                                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                                ">
                                    ${parseMarkdown(data.explanation || 'Aucune explication disponible.')}
                                </p>
                            </div>
                        </div>
                    `;
                } else {
                    console.error('AI explanation result container not found');
                }
            } catch (error) {
                console.error('Error in AI explanation:', error);
                
                const natureCard = document.querySelector('.nature-cause-card');
                if (natureCard) {
                    stopAIExplanationAnimation(natureCard);
                }

                if (aiExplanationResult) {
                    aiExplanationResult.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Erreur:</strong> SparK n'as pas pu analyser vos donneés d'incidents !
                            Veuillez réessayer plus tard !
                            <details>
                                <summary>Détails de l'erreur</summary>
                                ${error.message}
                            </details>
                        </div>
                    `;
                }
            } finally {
                if (aiExplanationBtn) {
                    aiExplanationBtn.disabled = false;
                }
            }
        });
    } else {
        console.error('AI explanation button not found');
    }

    // Deep Analysis SPARK button handler
    if (deepAnalysisSPARKBtn) {
        deepAnalysisSPARKBtn.addEventListener('click', async function() {
            try {
                // Start loading animation
                if (incidentHeader) {
                    incidentHeader.classList.add('loading');
                }
                
                // Disable the button during processing
                this.disabled = true;
                this.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Analyse en cours...
                `;

                // Prepare the request payload
                const payload = {
                    incident_id: window.incidentId,
                    analysis_type: 'deep'
                };

                // Send request to backend for deep analysis
                const response = await fetch('/incidents/deep_analysis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrf_token')
                    },
                    body: JSON.stringify(payload)
                });

                // Enhanced error handling
                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('Deep Analysis Server Error:', errorData);
                    
                    // Create a user-friendly error message
                    const errorMessage = errorData.details 
                        ? `${errorData.error}\n\n${errorData.details}`
                        : errorData.error || 'Une erreur inattendue est survenue';
                    
                    // Show error in a modal
                    const errorModalHtml = `
                        <div class="modal fade" id="deepAnalysisErrorModal" tabindex="-1">
                            <div class="modal-dialog modal-dialog-centered">
                                <div class="modal-content">
                                    <div class="modal-header bg-danger text-white">
                                        <h5 class="modal-title">
                                            <i class="fas fa-exclamation-triangle me-2"></i>Erreur d'analyse
                                        </h5>
                                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body">
                                        <p class="text-danger">${errorMessage}</p>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

                    // Append modal to body and show it
                    document.body.insertAdjacentHTML('beforeend', errorModalHtml);
                    const deepAnalysisErrorModal = new bootstrap.Modal(document.getElementById('deepAnalysisErrorModal'));
                    deepAnalysisErrorModal.show();

                    throw new Error(errorMessage);
                }

                const result = await response.json();

                showDeepAnalysisModal(result);
            } catch (error) {
                console.error('Deep Analysis Error:', error);
                alert('Impossible de générer l\'analyse approfondie. Veuillez réessayer.');
            } finally {
                // Remove loading state
                if (incidentHeader) {
                    incidentHeader.classList.remove('loading');
                }
                
                // Restore button state
                this.disabled = false;
                this.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap text-warning me-2">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                    </svg>
                    Analyse approfondie avec SPARK
                `;
            }
        });
    }

    function showDeepAnalysisModal(result) {
        // Get incident data from the page
        const incidentData = {
            date: document.querySelector('[data-incident-date]')?.getAttribute('data-incident-date') || 'Non spécifié',
            location: document.querySelector('[data-incident-location]')?.getAttribute('data-incident-location') || 'Non spécifié',
            type: document.querySelector('[data-incident-type]')?.getAttribute('data-incident-type') || 'Non catégorisé',
            description: document.querySelector('[data-incident-description]')?.textContent?.trim() || 'Aucune description fournie'
        };

        // Create and show modal with deep analysis results
        const modalHtml = `
            <div class="modal fade" id="deepAnalysisModal" tabindex="-1">
                <div class="modal-dialog modal-lg modal-dialog-scrollable">
                    <div class="modal-content analysis-modal">
                        <div class="modal-header">
                            <div class="modal-title-wrapper">
                                <h5 class="modal-title">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap me-2">
                                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                                    </svg>
                                    Analyse approfondie SPARK
                                </h5>
                                <span class="modal-subtitle">Rapport d'analyse détaillé de l'incident</span>
                            </div>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body analysis-content">
                            <div class="incident-summary">
                                <div class="summary-header">
                                    <h3>Détails de l'incident</h3>
                                    <div class="incident-meta">
                                        <span class="meta-item">
                                            <i class="fas fa-calendar me-2"></i>
                                            ${incidentData.date}
                                        </span>
                                        <span class="meta-item">
                                            <i class="fas fa-map-marker-alt me-2"></i>
                                            ${incidentData.location}
                                        </span>
                                        <span class="meta-item">
                                            <i class="fas fa-tag me-2"></i>
                                            ${incidentData.type}
                                        </span>
                                    </div>
                                </div>
                                <div class="summary-content">
                                    <p class="incident-description">${incidentData.description}</p>
                                </div>
                            </div>
                            <div class="analysis-separator"></div>
                            ${parseMarkdown(result.deep_analysis)}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-2"></i>Fermer
                            </button>
                            <button type="button" class="btn btn-primary" onclick="window.print()">
                                <i class="fas fa-print me-2"></i>Imprimer
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append modal to body and show it
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const deepAnalysisModal = new bootstrap.Modal(document.getElementById('deepAnalysisModal'));
        deepAnalysisModal.show();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const mapModal = document.getElementById('mapModal');
    
    if (mapModal) {
        mapModal.addEventListener('shown.bs.modal', function() {
            // Check if we have drawn shapes and coordinates
            if (window.incidentLat && window.incidentLng && window.drawnShapes) {
                // Use the existing map initialization function
                initializeIncidentMap(
                    'incident-map', 
                    window.incidentLat, 
                    window.incidentLng, 
                    window.incidentLat, 
                    window.incidentLng, 
                    window.drawnShapes
                );
            }
        });
    }
});

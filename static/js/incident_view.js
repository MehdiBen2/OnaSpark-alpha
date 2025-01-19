// incident_view.js: Handles incident view page interactions

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
    const incidentNatureCause = document.getElementById('incident-nature-cause');
    const incidentId = window.incidentId; // Passed from server-side template

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
                        nature_cause: incidentNatureCause ? incidentNatureCause.textContent.trim() : '',
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
});

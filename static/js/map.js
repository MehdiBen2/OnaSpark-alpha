// Initialize map variables
let incidentMap = null;
let incidentMarker = null;
let drawnShapesLayer = null;

// Function to render drawn shapes
function renderDrawnShapes(shapes) {
    // Remove existing drawn shapes layer if it exists
    if (drawnShapesLayer) {
        incidentMap.removeLayer(drawnShapesLayer);
    }

    // Create a new feature group for drawn shapes
    drawnShapesLayer = new L.FeatureGroup();
    incidentMap.addLayer(drawnShapesLayer);

    if (!shapes || shapes.length === 0) return;

    shapes.forEach(shape => {
        let layer;
        switch(shape.type) {
            case 'Polygon':
                layer = L.polygon(shape.coordinates[0], {
                    color: '#2196f3',
                    fillColor: '#2196f3',
                    fillOpacity: 0.2
                });
                break;
            case 'Rectangle':
                layer = L.rectangle(shape.coordinates[0], {
                    color: '#2196f3',
                    fillColor: '#2196f3',
                    fillOpacity: 0.2
                });
                break;
            case 'Circle':
                // Assuming coordinates are [lon, lat, radius]
                layer = L.circle([shape.coordinates[1], shape.coordinates[0]], {
                    radius: shape.coordinates[2] || 500, // default radius if not provided
                    color: '#2196f3',
                    fillColor: '#2196f3',
                    fillOpacity: 0.2
                });
                break;
        }

        if (layer) {
            drawnShapesLayer.addLayer(layer);
        }
    });

    // Fit map to drawn shapes
    if (drawnShapesLayer.getLayers().length > 0) {
        incidentMap.fitBounds(drawnShapesLayer.getBounds());
    }
}

// Function to show location on map
function showLocationMap(wilaya, commune, localite) {
    // Show the map modal
    const mapModal = new bootstrap.Modal(document.getElementById('mapModal'));
    mapModal.show();

    // Initialize map if not already initialized
    if (!incidentMap) {
        incidentMap = L.map('incident-map').setView([36.7538, 3.0588], 13); // Default to Algeria's center
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: ' OpenStreetMap contributors'
        }).addTo(incidentMap);
    }

    // Combine location details for geocoding
    const locationQuery = `${wilaya}, ${commune}, ${localite}, Algeria`;

    // Clear existing marker
    if (incidentMarker) {
        incidentMap.removeLayer(incidentMarker);
    }

    // Use Nominatim for geocoding
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationQuery)}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                
                // Update map view and add marker
                incidentMap.setView([lat, lon], 13);
                incidentMarker = L.marker([lat, lon]).addTo(incidentMap);
                
                // Add popup with location info
                incidentMarker.bindPopup(`
                    <strong>${wilaya}</strong><br>
                    ${commune}<br>
                    ${localite}
                `).openPopup();

                // Render drawn shapes if they exist
                if (window.drawnShapes) {
                    renderDrawnShapes(window.drawnShapes);
                }
            } else {
                console.error('Location not found');
                // Show a default view of Algeria
                incidentMap.setView([36.7538, 3.0588], 6);

                // Render drawn shapes if they exist
                if (window.drawnShapes) {
                    renderDrawnShapes(window.drawnShapes);
                }
            }
        })
        .catch(error => {
            console.error('Error fetching location:', error);
            // Show a default view of Algeria
            incidentMap.setView([36.7538, 3.0588], 6);

            // Render drawn shapes if they exist
            if (window.drawnShapes) {
                renderDrawnShapes(window.drawnShapes);
            }
        });

    // Invalidate map size when modal is shown
    mapModal.shown.subscribe(() => {
        setTimeout(() => {
            incidentMap.invalidateSize();
        }, 10);
    });
}

// Expose renderDrawnShapes for potential external use
window.renderDrawnShapes = renderDrawnShapes;

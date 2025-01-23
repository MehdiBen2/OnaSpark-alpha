document.addEventListener('DOMContentLoaded', function() {
    // Check if Leaflet is available
    if (typeof L === 'undefined') {
        console.error('Leaflet library not loaded');
        return;
    }

    // Map initialization function
    function initializeLocationMap() {
        const mapContainer = document.getElementById('location-map');
        const latInput = document.getElementById('latitude');
        const lonInput = document.getElementById('longitude');
        const mapToggle = document.getElementById('enable-map-selection');
        const mapSection = document.getElementById('map-selection-section');
        const locateMeBtn = document.getElementById('locate-me-btn');
        const mapSelectionModeToggle = document.getElementById('map-selection-mode');
        const drawShapeBtn = document.getElementById('draw-shape-btn');
        const drawnShapesInput = document.getElementById('drawn-shapes');
        const drawnShapesList = document.getElementById('drawn-shapes-list');

        // Location input fields
        const wilayaInput = document.getElementById('wilaya');
        const communeInput = document.getElementById('commune');
        const localiteInput = document.getElementById('localite');

        

        // Coordinates to center the view of Algiers, Blida, Boumerdes, and Medea
        const defaultLat = 36.4000;  // Centered latitude to show all cities
        const defaultLon = 3.1500;   // Centered longitude to show all cities
        const defaultZoom = 9;       // Zoom level to show all cities

        // Ensure map container is fully rendered
        let map = null;
        let marker = null;
        let drawnItems = null;
        let drawControl = null;

        function createMap() {
            // Destroy existing map if it exists
            if (map) {
                map.remove();
            }

            // Create map with full container width
            map = L.map('location-map', {
                center: [defaultLat, defaultLon],
                zoom: defaultZoom,
                attributionControl: false,
                zoomControl: true
            });

            // Add OpenStreetMap tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: ' OpenStreetMap contributors'
            }).addTo(map);

            // Initialize the FeatureGroup to store editable layers
            drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);

            // Configure draw controls
            drawControl = new L.Control.Draw({
                edit: {
                    featureGroup: drawnItems,
                    remove: true
                },
                draw: {
                    polygon: {
                        allowIntersection: false,
                        drawError: {
                            color: '#e1e100',
                            timeout: 1000
                        },
                        shapeOptions: {
                            color: '#2196f3'
                        }
                    },
                    polyline: false,
                    rectangle: {
                        shapeOptions: {
                            color: '#2196f3'
                        }
                    },
                    circle: {
                        shapeOptions: {
                            color: '#2196f3'
                        }
                    },
                    marker: false
                }
            });

            // Add draw control to the map
            map.addControl(drawControl);

            // Event handler for when a shape is created
            map.on(L.Draw.Event.CREATED, function (e) {
                const layer = e.layer;
                drawnItems.addLayer(layer);
                updateDrawnShapesList();
            });

            // Event handler for when a shape is edited
            map.on(L.Draw.Event.EDITED, function () {
                updateDrawnShapesList();
            });

            // Event handler for when a shape is deleted
            map.on(L.Draw.Event.DELETED, function () {
                updateDrawnShapesList();
            });

            // Function to update the list of drawn shapes
            function updateDrawnShapesList() {
                // Clear existing list
                drawnShapesList.innerHTML = '';

                // Serialize and store drawn shapes
                const shapes = [];
                drawnItems.eachLayer(function(layer) {
                    const shapeType = layer instanceof L.Polygon ? 'Polygon' :
                                      layer instanceof L.Rectangle ? 'Rectangle' :
                                      layer instanceof L.Circle ? 'Circle' : 'Unknown';
                    
                    const shapeCoords = layer.toGeoJSON().geometry.coordinates;
                    
                    const shapeItem = document.createElement('div');
                    shapeItem.classList.add('shape-item');
                    shapeItem.innerHTML = `
                        <span>${shapeType}</span>
                        <button type="button" class="btn btn-sm btn-danger remove-shape">
                            <i class="fas fa-trash"></i>
                        </button>
                    `;

                    // Add remove event listener
                    const removeBtn = shapeItem.querySelector('.remove-shape');
                    removeBtn.addEventListener('click', function() {
                        drawnItems.removeLayer(layer);
                        updateDrawnShapesList();
                    });

                    drawnShapesList.appendChild(shapeItem);
                    
                    shapes.push({
                        type: shapeType,
                        coordinates: shapeCoords
                    });
                });

                // Update hidden input with serialized shapes
                drawnShapesInput.value = JSON.stringify(shapes);
            }

            // Draw shape button functionality
            if (drawShapeBtn) {
                drawShapeBtn.addEventListener('click', function() {
                    // Enable drawing mode
                    const polygonDrawer = new L.Draw.Polygon(map, drawControl.options.draw.polygon);
                    polygonDrawer.enable();
                });
            }

            // Map click event for manual selection
            map.on('click', function(e) {
                // Only allow selection if manual mode is enabled
                if (mapSelectionModeToggle && mapSelectionModeToggle.checked) {
                    // Remove previous marker if exists
                    if (marker) {
                        map.removeLayer(marker);
                    }

                    // Add new marker
                    marker = L.marker(e.latlng).addTo(map);

                    // Update hidden input fields
                    latInput.value = e.latlng.lat.toFixed(6);
                    lonInput.value = e.latlng.lng.toFixed(6);

                    // Reverse geocoding to get address details
                    reverseGeocode(e.latlng.lat, e.latlng.lng);
                }
            });

            // Ensure map is fully visible and sized correctly
            setTimeout(() => {
                map.invalidateSize();
            }, 200);

            return map;
        }

        // Reverse geocoding function to populate address fields
        function reverseGeocode(lat, lon) {
            const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const address = data.address;
                    
                    // Populate fields only if they are empty or in manual selection mode
                    if (mapSelectionModeToggle && mapSelectionModeToggle.checked) {
                        if (address.state) {
                            wilayaInput.value = address.state;
                        }
                        if (address.county) {
                            communeInput.value = address.county;
                        }
                        if (address.village || address.town) {
                            localiteInput.value = address.village || address.town;
                        }
                    }
                })
                .catch(error => {
                    console.error('Reverse geocoding error:', error);
                });
        }

        // Geocoding function to find location on map
        function geocodeLocation() {
            const wilaya = wilayaInput.value.trim();
            const commune = communeInput.value.trim();
            const localite = localiteInput.value.trim();

            // Construct search query
            let searchQuery = `${localite}, ${commune}, ${wilaya}, Algeria`;

            // Use Nominatim for geocoding
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=1`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data && data.length > 0) {
                        const location = data[0];
                        const lat = parseFloat(location.lat);
                        const lon = parseFloat(location.lon);

                        // Update map
                        if (map) {
                            // Remove existing marker
                            if (marker) {
                                map.removeLayer(marker);
                            }

                            // Center map and add marker
                            map.setView([lat, lon], 10);
                            marker = L.marker([lat, lon]).addTo(map);

                            // Update hidden inputs
                            latInput.value = lat.toFixed(6);
                            lonInput.value = lon.toFixed(6);

                            console.log('Location found:', searchQuery, lat, lon);
                        }
                    } else {
                        console.warn('Location not found:', searchQuery);
                        // Optionally reset map to default view
                        if (map) {
                            map.setView([defaultLat, defaultLon], defaultZoom);
                        }
                    }
                })
                .catch(error => {
                    console.error('Geocoding error:', error);
                });
        }

        // Add event listeners for geocoding
        [wilayaInput, communeInput, localiteInput].forEach(input => {
            input.addEventListener('change', function() {
                // Only geocode if map is enabled and not in manual selection mode
                if (mapToggle.checked && 
                    (!mapSelectionModeToggle || !mapSelectionModeToggle.checked)) {
                    geocodeLocation();
                }
            });
        });

        // Locate Me functionality
        function locateUser() {
            if (map) {
                map.locate({
                    setView: true,
                    maxZoom: 12,
                    timeout: 10000,
                    enableHighAccuracy: true
                });
            }
        }

        // Handle geolocation success
        if (map) {
            map.on('locationfound', function(e) {
                // Remove previous marker if exists
                if (marker) {
                    map.removeLayer(marker);
                }

                // Add marker at user's location
                marker = L.marker(e.latlng).addTo(map);

                // Update hidden input fields
                latInput.value = e.latlng.lat.toFixed(6);
                lonInput.value = e.latlng.lng.toFixed(6);

                // Reverse geocoding to get address details
                reverseGeocode(e.latlng.lat, e.latlng.lng);
            });

            // Handle geolocation error
            map.on('locationerror', function(e) {
                console.warn('Geolocation error:', e.message);
                alert('Impossible de récupérer votre localisation. Veuillez sélectionner manuellement.');
            });
        }

        // Attach locate me button event
        if (locateMeBtn) {
            locateMeBtn.addEventListener('click', locateUser);
        }

        // Map toggle event
        mapToggle.addEventListener('change', function() {
            if (this.checked) {
                // Show map section
                mapSection.style.display = 'block';
                
                // Ensure map is created and sized correctly
                setTimeout(() => {
                    createMap();
                    
                    // Try to geocode current location if fields are filled
                    if (wilayaInput.value.trim() || 
                        communeInput.value.trim() || 
                        localiteInput.value.trim()) {
                        geocodeLocation();
                    }
                }, 100);
            } else {
                // Hide map section and reset inputs
                mapSection.style.display = 'none';
                latInput.value = '';
                lonInput.value = '';
                drawnShapesInput.value = '';

                // Remove map if it exists
                if (map) {
                    map.remove();
                    map = null;
                }
            }
        });

        // Optional: Create map immediately if toggle is already checked
        if (mapToggle.checked) {
            setTimeout(() => {
                createMap();
            }, 100);
        }

        // Toggle manual selection mode with visual feedback
        if (mapSelectionModeToggle) {
            mapSelectionModeToggle.addEventListener('change', function() {
                const label = document.getElementById('map-selection-mode-label');
                const mapContainer = document.getElementById('location-map');
                
                if (this.checked) {
                    // Add active state styling
                    label.classList.add('btn-primary', 'text-white');
                    label.classList.remove('btn-outline-secondary');
                    label.innerHTML = '<i class="fas fa-hand-pointer"></i> Mode Sélection Activé';
                    
                    // Add visual cue to map
                    if (mapContainer) {
                        mapContainer.classList.add('map-selection-active');
                        mapContainer.style.cursor = 'crosshair';
                    }
                } else {
                    // Remove active state styling
                    label.classList.remove('btn-primary', 'text-white');
                    label.classList.add('btn-outline-secondary');
                    label.innerHTML = '<i class="fas fa-hand-pointer"></i> Sélection manuelle';
                    
                    // Remove visual cue from map
                    if (mapContainer) {
                        mapContainer.classList.remove('map-selection-active');
                        mapContainer.style.cursor = 'default';
                    }
                }
            });
        }

        // Add form submission validation
        const newIncidentForm = document.getElementById('newIncidentForm');
        if (newIncidentForm) {
            newIncidentForm.addEventListener('submit', function(event) {
                // Ensure drawn shapes are populated if any shapes exist
                if (drawnItems && drawnItems.getLayers().length > 0) {
                    updateDrawnShapesList();
                }
            });
        }
    }

    // Initialize the map functionality
    initializeLocationMap();
});

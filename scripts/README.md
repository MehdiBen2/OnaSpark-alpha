# Incident Population Script for Zone d'Alger

## Purpose
This script generates sample incidents for the Zone d'Alger, populating the database with realistic incident data across different units.

## Features
- Creates units for Alger zone
- Generates 10-15 incidents per unit
- Randomizes:
  - Incident types
  - Incident severities
  - Incident dates
- Ensures data integrity and relationships

## Incident Types
- Water Leak (FUITE_EAU)
- Pump Failure (PANNE_POMPE)
- Network Obstruction (OBSTRUCTION_RESEAU)
- Water Quality Issues (QUALITE_EAU)
- Bank Erosion (EROSION_BERGE)
- Other Incidents (AUTRE)

## Severities
- Low (FAIBLE)
- Medium (MOYEN)
- Critical (CRITIQUE)

## Prerequisites
- Activate your virtual environment
- Ensure all dependencies are installed
- Database must be initialized

## Usage
```bash
python scripts/populate_incidents_alger.py
```

## Caution
- This script will add data to your live database
- Use in development or testing environments
- Backup your database before running

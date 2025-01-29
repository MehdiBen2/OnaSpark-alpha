import os
import sys
import random
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import necessary models and database setup
from app import app, db
from models import Zone, Unit, Incident, User

def generate_random_date(start_date, end_date):
    """Generate a random datetime between start and end dates."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def create_incidents_for_alger():
    """Create sample incidents for Zone d'Alger."""
    # Ensure we're in application context
    with app.app_context():
        # Find or create Zone d'Alger
        alger_zone = Zone.query.filter_by(name='Zone d\'Alger').first()
        if not alger_zone:
            alger_zone = Zone(
                name='Zone d\'Alger', 
                code='ALGER_01',
                description='Région métropolitaine d\'Alger',
                email='alger.zone@ona.dz',
                phone='+213 (0)21 XX XX XX'
            )
            db.session.add(alger_zone)
            db.session.commit()

        # Define units for Alger zone
        units_data = [
            {
                'name': 'Unité de Distribution Hydrique Alger Centre',
                'code': 'UDHAC',
                'description': 'Unité responsable de la distribution d\'eau potable au centre d\'Alger',
                'email': 'distribution.centre@ona.dz',
                'phone': '+213 (0)21 XX XX XX'
            },
            {
                'name': 'Unité d\'Assainissement Alger Ouest',
                'code': 'UAAO',
                'description': 'Unité de gestion des eaux usées pour la partie ouest d\'Alger',
                'email': 'assainissement.ouest@ona.dz',
                'phone': '+213 (0)21 XX XX XX'
            },
            {
                'name': 'Unité de Maintenance Infrastructures Alger Est',
                'code': 'UMIAE',
                'description': 'Unité chargée de la maintenance des infrastructures hydrauliques à l\'est d\'Alger',
                'email': 'maintenance.est@ona.dz',
                'phone': '+213 (0)21 XX XX XX'
            }
        ]

        # Find or create a default admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', email='admin@example.com')
            db.session.add(admin_user)
            db.session.commit()

        # Create units
        units = []
        for unit_info in units_data:
            unit = Unit.query.filter_by(code=unit_info['code']).first()
            if not unit:
                unit = Unit(
                    name=unit_info['name'], 
                    code=unit_info['code'], 
                    description=unit_info['description'],
                    email=unit_info['email'],
                    phone=unit_info['phone'],
                    zone_id=alger_zone.id
                )
                db.session.add(unit)
            units.append(unit)
        db.session.commit()

        # Incident types with their probabilities
        incident_types = [
            ('Fuite d\'eau', 0.3),
            ('Panne de pompe', 0.2),
            ('Obstruction du réseau', 0.2),
            ('Problème de qualité d\'eau', 0.15),
            ('Érosion de berge', 0.1),
            ('Autre', 0.05)
        ]

        # Generate incidents for each unit
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()

        for unit in units:
            # Generate 10-15 incidents per unit
            num_incidents = random.randint(10, 15)
            
            for _ in range(num_incidents):
                # Randomly select incident type based on probability
                incident_type = random.choices(
                    [t[0] for t in incident_types], 
                    weights=[t[1] for t in incident_types]
                )[0]
                
                # Create incident
                incident = Incident(
                    title=f"Incident: {incident_type} - {unit.name}",
                    wilaya='Alger',
                    commune='Non spécifié',
                    localite=unit.name,
                    structure_type='Conduits',
                    nature_cause=f"Incident de type {incident_type}",
                    date_incident=generate_random_date(start_date, end_date),
                    impact='Impact à évaluer',
                    gravite=random.choice(['Faible', 'Moyen', 'Critique']),
                    status='Nouveau',
                    user_id=admin_user.id,
                    unit_id=unit.id
                )
                db.session.add(incident)
        
        # Commit all incidents
        db.session.commit()
        print(f"Generated incidents for Zone d'Alger successfully!")

def main():
    create_incidents_for_alger()

if __name__ == '__main__':
    main()

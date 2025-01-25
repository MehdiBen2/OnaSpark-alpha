from flask import render_template, Blueprint, request, jsonify
from flask_login import login_required
from models import db, Infrastructure

infrastructures = Blueprint('infrastructures', __name__, url_prefix='/departements')

@infrastructures.route('/infrastructures', methods=['GET', 'POST'])
@login_required
def list_infrastructures():
    if request.method == 'POST':
        # Handle infrastructure creation
        data = request.form
        new_infrastructure = Infrastructure(
            nom=data.get('nom'),
            type=data.get('type'),
            localisation=data.get('localisation'),
            capacite=data.get('capacite'),
            etat=data.get('etat', 'Opérationnel')
        )
        
        try:
            db.session.add(new_infrastructure)
            db.session.commit()
            return jsonify({'message': 'Infrastructure créée avec succès', 'id': new_infrastructure.id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    # GET method: list infrastructures
    infrastructures = Infrastructure.query.all()
    return render_template('departement/exploitation/infrastructures/infrastructures.html', infrastructures=infrastructures)

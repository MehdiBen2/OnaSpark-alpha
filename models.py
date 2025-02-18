from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from utils.permissions import UserRole
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, JSON

db = SQLAlchemy()

class Zone(db.Model):
    __tablename__ = 'zones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    units = db.relationship('Unit', backref='zone', lazy=True, cascade='all, delete-orphan')
    users = db.relationship('User', backref='assigned_zone', lazy=True, foreign_keys='User.zone_id')
    director = db.relationship('User', foreign_keys=[director_id], backref='directed_zone', lazy=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Zone {self.name}>'

class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True)
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    centers = db.relationship('Center', backref='unit', lazy='joined', cascade='all, delete-orphan')
    users = db.relationship('User', backref='assigned_unit', lazy=True, foreign_keys='User.unit_id')
    director = db.relationship('User', foreign_keys=[director_id], backref='directed_unit', lazy=True)
    incidents = db.relationship('Incident', backref='unit', lazy=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Unit {self.name}>'

class Center(db.Model):
    __tablename__ = 'centers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Foreign Keys
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='CASCADE'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Center {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    nickname = db.Column(db.String(80), index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default=UserRole.UTILISATEUR, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    last_login = db.Column(db.DateTime, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='SET NULL'), nullable=True, index=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Relationships
    incidents = db.relationship('Incident', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def disconnect_all_users(cls):
        """
        Invalidate all active user sessions by setting is_active to False.
        """
        from app import db
        
        # Update all users to be inactive
        cls.query.update({cls.is_active: False})
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    wilaya = db.Column(db.String(50), nullable=False, index=True)
    commune = db.Column(db.String(100), nullable=False, index=True)
    localite = db.Column(db.String(200), nullable=False, index=True)
    structure_type = db.Column(db.String(50), nullable=False, default='Conduits', index=True)
    nature_cause = db.Column(db.Text, nullable=False, index=True)
    date_incident = db.Column(db.DateTime, nullable=False, index=True)
    mesures_prises = db.Column(db.Text)
    impact = db.Column(db.Text, nullable=False)
    gravite = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='Nouveau', index=True)
    date_resolution = db.Column(db.DateTime, index=True)
    resolution_notes = db.Column(db.Text)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False, index=True)
    center_id = db.Column(db.Integer, db.ForeignKey('centers.id'), index=True)
    
    # New column for storing drawn shapes
    drawn_shapes = db.Column(JSON, nullable=True)
    
    # Optional: Latitude and Longitude can be derived from drawn shapes
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # New column for validation status
    is_valid = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    def __init__(self, *args, **kwargs):
        # If drawn_shapes are provided, attempt to extract representative coordinates
        drawn_shapes = kwargs.pop('drawn_shapes', None)
        
        # Call the parent class's __init__
        super().__init__(*args, **kwargs)
        
        # Process drawn shapes if provided
        if drawn_shapes:
            self.drawn_shapes = drawn_shapes
            
            # Extract representative coordinates (e.g., center of the first shape)
            if drawn_shapes and len(drawn_shapes) > 0:
                first_shape = drawn_shapes[0]
                
                # For polygon and rectangle, use the first coordinate set
                if first_shape['type'] in ['Polygon', 'Rectangle'] and first_shape['coordinates']:
                    # Assuming coordinates are in GeoJSON format
                    coords = first_shape['coordinates'][0]
                    if coords and len(coords) > 0:
                        self.latitude = coords[0][1]  # Latitude
                        self.longitude = coords[0][0]  # Longitude
                
                # For circle, use the center coordinates
                elif first_shape['type'] == 'Circle' and first_shape['coordinates']:
                    self.latitude = first_shape['coordinates'][1]
                    self.longitude = first_shape['coordinates'][0]
    
    def to_dict(self):
        """
        Convert incident to dictionary representation
        Includes drawn shapes if present
        """
        incident_dict = super().to_dict()
        
        # Add drawn shapes to dictionary
        if self.drawn_shapes:
            incident_dict['drawn_shapes'] = self.drawn_shapes
        
        return incident_dict
    
    def get_representative_location(self):
        """
        Get a representative location for the incident
        
        Returns:
            tuple: (latitude, longitude) or (None, None)
        """
        # Priority: 1. Explicit lat/lon 2. Drawn shapes 3. None
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        
        # If no explicit coordinates, try to extract from drawn shapes
        if self.drawn_shapes:
            first_shape = self.drawn_shapes[0]
            
            if first_shape['type'] in ['Polygon', 'Rectangle'] and first_shape['coordinates']:
                coords = first_shape['coordinates'][0]
                if coords and len(coords) > 0:
                    return (coords[0][1], coords[0][0])
            
            elif first_shape['type'] == 'Circle' and first_shape['coordinates']:
                return (first_shape['coordinates'][1], first_shape['coordinates'][0])
        
        return (None, None)

    def __repr__(self):
        return f'<Incident {self.id}>'

class Infrastructure(db.Model):
    __tablename__ = 'infrastructures'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False, index=True)
    type = db.Column(db.String(100), nullable=False, index=True)
    localisation = db.Column(db.String(200), nullable=False)
    capacite = db.Column(db.Float, nullable=False)
    etat = db.Column(db.String(50), nullable=False, default='Opérationnel', index=True)
    epuration_type = db.Column(db.String(100), nullable=True, index=True)
    
    # Relationship with files
    infrastructure_files = db.relationship('InfrastructureFile', back_populates='infrastructure', lazy='dynamic', cascade='all, delete-orphan')

    def get_associated_files(self):
        """
        Retrieve all files associated with this infrastructure.
        
        Returns:
            list: List of associated infrastructure files
        """
        return self.infrastructure_files.all()

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Infrastructure {self.nom}>'

class InfrastructureFile(db.Model):
    """
    Model representing files associated with infrastructures.
    Reflects an existing database table.
    """
    __tablename__ = 'infrastructures_files'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key
    infrastructure_id = db.Column(db.Integer, db.ForeignKey('infrastructures.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # File metadata columns
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    # Relationship
    infrastructure = db.relationship('Infrastructure', back_populates='infrastructure_files')
    
    def __repr__(self):
        return f'<InfrastructureFile {self.filename}>'
    
    def get_file_size_human_readable(self):
        """
        Convert file size to human-readable format.
        
        Returns:
            str: Formatted file size (e.g., '2.5 MB')
        """
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @classmethod
    def get_files_for_infrastructure(cls, infrastructure_id):
        """
        Retrieve all files associated with a specific infrastructure.
        
        Args:
            infrastructure_id (int): ID of the infrastructure
        
        Returns:
            list: List of associated infrastructure files
        """
        return cls.query.filter_by(infrastructure_id=infrastructure_id).all()

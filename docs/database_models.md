# OnaSpark Database Models and Relationships

## Overview
This document outlines the database structure and relationships between models in the OnaSpark application.

## Core Models

### 1. Zone Model
Primary organizational unit representing geographical/administrative areas.

**Fields:**
- `id`: Integer (Primary Key)
- `name`: String(100), unique, indexed
- `code`: String(10), unique, indexed
- `email`: String(120), unique, optional
- `phone`: String(20), optional
- `description`: Text
- `address`: String(200)
- `director_id`: Integer (Foreign Key to User)
- `created_at`: DateTime, indexed
- `updated_at`: DateTime, indexed

**Relationships:**
- `units`: One-to-Many with Unit
- `users`: One-to-Many with User (assigned users)
- `director`: One-to-One with User (zone director)

### 2. Unit Model
Operational units within zones.

**Fields:**
- `id`: Integer (Primary Key)
- `name`: String(100), indexed
- `code`: String(10), unique, indexed
- `email`: String(120), unique, optional
- `phone`: String(20), optional
- `description`: Text
- `address`: String(200)
- `zone_id`: Integer (Foreign Key to Zone), indexed
- `director_id`: Integer (Foreign Key to User)
- `created_at`: DateTime, indexed
- `updated_at`: DateTime, indexed

**Relationships:**
- `zone`: Many-to-One with Zone
- `users`: One-to-Many with User (assigned users)
- `director`: One-to-One with User (unit director)
- `incidents`: One-to-Many with Incident

### 3. User Model
System users with role-based access control.

**Fields:**
- `id`: Integer (Primary Key)
- `username`: String(80), unique, indexed
- `nickname`: String(80), indexed
- `email`: String(120), unique, indexed
- `password_hash`: String(128)
- `role`: String(20), indexed
- `is_active`: Boolean, indexed
- `last_login`: DateTime, indexed
- `unit_id`: Integer (Foreign Key to Unit), optional
- `zone_id`: Integer (Foreign Key to Zone), optional
- `department_id`: Integer (Foreign Key to Department), optional
- `created_at`: DateTime, indexed
- `updated_at`: DateTime, indexed

**Relationships:**
- `incidents`: One-to-Many with Incident (as author)
- `assigned_unit`: Many-to-One with Unit
- `assigned_zone`: Many-to-One with Zone

### 4. Incident Model
Incident tracking and management.

**Fields:**
- `id`: Integer (Primary Key)
- `title`: String(200), indexed
- `wilaya`: String(50), indexed
- `commune`: String(100), indexed
- `localite`: String(200), indexed
- `structure_type`: String(50), indexed
- `nature_cause`: Text, indexed
- `date_incident`: DateTime, indexed
- `mesures_prises`: Text
- `impact`: Text
- `gravite`: String(50), indexed
- `status`: String(20), indexed
- `date_resolution`: DateTime, indexed
- `resolution_notes`: Text
- `user_id`: Integer (Foreign Key to User), indexed
- `unit_id`: Integer (Foreign Key to Unit), indexed
- `drawn_shapes`: JSON
- `latitude`: Float, optional
- `longitude`: Float, optional
- `is_valid`: Boolean, indexed
- `created_at`: DateTime, indexed
- `updated_at`: DateTime, indexed

**Relationships:**
- `author`: Many-to-One with User
- `unit`: Many-to-One with Unit

### 5. Infrastructure Model
Water infrastructure management.

**Fields:**
- `id`: Integer (Primary Key)
- `nom`: String(200), indexed
- `type`: String(100), indexed
- `localisation`: String(200)
- `capacite`: Float
- `etat`: String(50), indexed
- `epuration_type`: String(100), indexed
- `created_at`: DateTime, indexed
- `updated_at`: DateTime, indexed

**Relationships:**
- `infrastructure_files`: One-to-Many with InfrastructureFile

### 6. InfrastructureFile Model
Files associated with infrastructure.

**Fields:**
- `id`: Integer (Primary Key)
- `infrastructure_id`: Integer (Foreign Key to Infrastructure)
- `filename`: String(255)
- `filepath`: String(500)
- `file_type`: String(50)
- `mime_type`: String(100)
- `file_size`: Integer
- `created_at`: DateTime, indexed
- `updated_at`: DateTime, indexed

**Relationships:**
- `infrastructure`: Many-to-One with Infrastructure

### 7. Department Model
Organizational departments within the company.

**Fields:**
- `id`: Integer (Primary Key)
- `name`: String(100), unique, indexed
- `created_at`: DateTime, indexed
- `updated_at`: DateTime, indexed

**Relationships:**
- `users`: One-to-Many with User (users can be assigned to this department)

## Key Relationships Summary

1. **Zone-Unit Hierarchy:**
   - Zones contain multiple Units (One-to-Many)
   - Each Unit belongs to exactly one Zone (Many-to-One)

2. **User Assignment:**
   - Users can be assigned to a Zone and/or Unit
   - Users can be directors of Zones or Units
   - Users can be assigned to one Department (optional)

3. **Department-User Assignment:**
   - Departments can have multiple Users
   - Each User can be assigned to one Department (optional)

4. **Incident Management:**
   - Incidents are linked to Units and Users
   - Each Incident has one author (User) and belongs to one Unit

5. **Infrastructure Management:**
   - Infrastructure items can have multiple associated files
   - Files are linked exclusively to one Infrastructure item

## Indexing Strategy
- Primary keys and foreign keys are indexed
- Frequently queried fields (names, codes, dates) are indexed
- Search fields (titles, status) are indexed
- Timestamp fields are indexed for efficient sorting and filtering

## Timestamps
All models include:
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp

These timestamps are automatically managed and indexed for efficient querying.

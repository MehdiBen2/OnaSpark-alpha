# ONA SPARK - Documentation Technique

## Vue d'ensemble du système
ONA SPARK est une application web de gestion des incidents pour l'Office National de l'Assainissement (ONA). Elle permet le suivi, la gestion et le reporting des incidents dans les différentes unités et zones de l'ONA.

## Architecture Technique

### Stack Technologique
- **Backend**: Flask (Python)
- **Base de données**: SQLAlchemy avec SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentification**: Flask-Login
- **Reporting**: ReportLab, OpenPyXL

### Structure du Projet
```
ona-spark/
├── app.py              # Point d'entrée de l'application
├── models.py           # Modèles de données
├── routes/            
│   ├── auth.py        # Authentification
│   ├── incidents.py   # Gestion des incidents
│   ├── profiles.py    # Gestion des profils
│   ├── users.py       # Gestion des utilisateurs
│   └── units.py       # Gestion des unités
├── static/            # Ressources statiques
├── templates/         # Templates HTML
├── utils/            # Utilitaires
└── functions/        # Fonctions métier
```

## Structure de la Base de Données

### Tables Principales

#### 1. Users (Utilisateurs)
- **Champs Principaux**:
  - `id`: Identifiant unique
  - `username`: Nom d'utilisateur (unique)
  - `nickname`: Surnom (optionnel)
  - `email`: Email (unique)
  - `password_hash`: Hash du mot de passe
  - `role`: Rôle de l'utilisateur
  - `is_active`: État du compte
  - `last_login`: Dernière connexion
- **Relations**:
  - `profile`: Profil utilisateur (one-to-one)
  - `incidents`: Incidents créés
  - `assigned_unit`: Unité assignée
  - `assigned_zone`: Zone assignée

#### 2. UserProfile (Profils)
- **Champs Principaux**:
  - `first_name`: Prénom
  - `last_name`: Nom
  - `date_of_birth`: Date de naissance
  - `professional_number`: Numéro professionnel
  - `job_function`: Fonction
  - `recruitment_date`: Date de recrutement
  - `phone`: Téléphone
  - `address`: Adresse

#### 3. Zones
- **Champs Principaux**:
  - `name`: Nom de la zone (unique)
  - `code`: Code unique
  - `description`: Description
  - `address`: Adresse
  - `director_id`: ID du directeur
- **Relations**:
  - `units`: Unités de la zone
  - `zone_users`: Utilisateurs assignés
  - `director`: Directeur de zone

#### 4. Units (Unités)
- **Champs Principaux**:
  - `name`: Nom de l'unité
  - `code`: Code unique
  - `zone_id`: Zone parente
  - `director_id`: ID du directeur
- **Relations**:
  - `centers`: Centres de l'unité
  - `unit_users`: Utilisateurs assignés
  - `incidents`: Incidents liés

#### 5. Incidents
- **Champs Principaux**:
  - `title`: Titre
  - `wilaya`: Wilaya concernée
  - `commune`: Commune
  - `localite`: Localité
  - `structure_type`: Type de structure
  - `nature_cause`: Nature et cause
  - `date_incident`: Date de l'incident
  - `gravite`: Niveau de gravité
  - `status`: État de l'incident
  - `date_resolution`: Date de résolution
- **Relations**:
  - `author`: Utilisateur créateur
  - `unit`: Unité concernée
  - `center`: Centre concerné (optionnel)

## Fonctionnalités et Routes

### 1. Authentification (`/auth`)
- Login/Logout
- Gestion des sessions
- Récupération de mot de passe

### 2. Gestion des Incidents (`/incidents`)
- Création et modification
- Suivi et mise à jour
- Filtrage et recherche
- Génération de rapports

### 3. Gestion des Utilisateurs (`/users`)
- CRUD utilisateurs
- Gestion des rôles
- Attribution aux unités/zones

### 4. Gestion des Profils (`/profiles`)
- Création/modification des profils
- Informations professionnelles
- Historique de carrière

### 5. Administration (`/database_admin`)
- Gestion des zones
- Gestion des unités
- Configuration système

## Sécurité

### Niveaux d'Accès
1. **Admin Système**
   - Accès complet
   - Configuration système
   - Gestion des utilisateurs

2. **Directeur de Zone**
   - Gestion de sa zone
   - Rapports de zone
   - Supervision des unités

3. **Directeur d'Unité**
   - Gestion de son unité
   - Rapports d'unité
   - Supervision des incidents

4. **Employeur**
   - Création d'incidents
   - Mise à jour des incidents
   - Accès limité aux rapports

### Mesures de Sécurité
- Hachage des mots de passe
- Sessions sécurisées
- Validation des entrées
- Protection CSRF
- Journalisation des actions

## Reporting et Analytics

### Types de Rapports
1. **Rapports d'Incidents**
   - Par période
   - Par zone/unité
   - Par gravité

2. **Rapports de Performance**
   - Temps de résolution
   - Taux de résolution
   - Incidents par type

3. **Rapports Administratifs**
   - État des unités
   - Activité des utilisateurs
   - Statistiques globales

### Format des Exports
- PDF (ReportLab)
- Excel (OpenPyXL)
- CSV

## Maintenance et Support

### Logs et Monitoring
- Logs d'application
- Logs d'erreurs
- Logs de sécurité

### Sauvegarde
- Sauvegarde quotidienne de la base
- Export périodique des données
- Plan de reprise d'activité

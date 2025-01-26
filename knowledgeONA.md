# ONA SPARK - Documentation Technique

## Vue d'ensemble du système
ONA SPARK est une application web de gestion avancée pour l'Office National de l'Assainissement (ONA), offrant des fonctionnalités étendues de suivi, de gestion et de reporting des incidents, infrastructures, et opérations.

## Architecture Technique

### Stack Technologique
- **Backend**: Flask (Python) avec extensions avancées
- **Base de données**: SQLAlchemy avec migrations
- **Frontend**: HTML5, CSS3, JavaScript moderne
- **Authentification**: Flask-Login avec gestion de rôles avancée
- **Reporting**: ReportLab, OpenPyXL
- **Outils supplémentaires**: 
  - Windsurf IDE
  - AI-assisted development
  - Comprehensive logging et monitoring

### Structure du Projet
```
ona-spark/
├── app.py              # Point d'entrée principal de l'application
├── models.py           # Modèles de données SQLAlchemy
├── extensions.py       # Configuration des extensions Flask
├── wsgi.py             # Configuration du serveur WSGI
├── routes/             # Routes modulaires par fonctionnalité
│   ├── auth.py         # Authentification et gestion des sessions
│   ├── incidents.py    # Gestion complète des incidents
│   ├── infrastructures.py  # Gestion des infrastructures
│   ├── profiles.py     # Gestion des profils utilisateurs
│   ├── users.py        # Gestion administrative des utilisateurs
│   ├── units.py        # Gestion des unités organisationnelles
│   ├── water_quality.py # Suivi de la qualité de l'eau
│   ├── departement.py   # Gestion des départements
│   ├── main_dashboard.py # Tableau de bord principal
│   ├── database_admin.py # Administration de la base de données
│   └── spark_agent_routes.py # Routes pour l'agent IA
├── static/             # Ressources statiques (CSS, JS, images)
├── templates/          # Templates HTML avec héritage
├── utils/              # Utilitaires et fonctions transverses
├── migrations/         # Migrations de base de données
├── config/             # Configurations de l'application
├── scripts/            # Scripts utilitaires
└── docs/               # Documentation technique
```

## Fonctionnalités Principales

### 1. Gestion des Incidents
- Création et suivi complet des incidents
- Workflow de résolution détaillé
- Rapports et analytics avancés

### 2. Gestion des Infrastructures
- Cartographie et suivi des infrastructures
- Gestion des états et maintenance
- Intégration avec le système d'incidents

### 3. Qualité de l'Eau
- Monitoring en temps réel
- Rapports de conformité
- Alertes et notifications

### 4. Gestion des Utilisateurs et Profils
- Système d'authentification robuste
- Gestion des rôles et permissions
- Profils détaillés avec historique

### 5. Tableau de Bord
- Vue d'ensemble dynamique
- Widgets personnalisables
- Indicateurs de performance clés

### 6. Agent IA Intégré
- Support et assistance intelligente
- Analyse prédictive
- Recommandations basées sur les données

## Modèle de Rôles et Hiérarchie Organisationnelle

### Hiérarchie des Rôles

OnaSpark implémente un système de gestion des rôles sophistiqué et hiérarchisé, conçu pour refléter la structure organisationnelle complexe de l'Office National de l'Assainissement.

#### Niveaux de Rôles

1. **Admin Système** (`ADMIN`)
   - Rôle le plus élevé dans la hiérarchie
   - Accès complet et illimité à tous les systèmes
   - Capacités :
     * Création, modification et suppression de tous les objets
     * Gestion complète des utilisateurs
     * Configuration système
     * Vue globale de toutes les zones, unités et incidents

2. **Employeur Direction Générale** (`EMPLOYEUR_DG`)
   - Vue et gestion globale de l'organisation
   - Capacités :
     * Supervision de toutes les zones
     * Création de rapports stratégiques
     * Gestion des politiques organisationnelles
     * Validation des incidents critiques

3. **Employeur Zone** (`EMPLOYEUR_ZONE`)
   - Responsable de la supervision d'une zone spécifique
   - Capacités :
     * Gestion des unités dans sa zone
     * Suivi des incidents zonaux
     * Création de rapports de zone
     * Escalade des incidents complexes

4. **Employeur Unité** (`EMPLOYEUR_UNITE`)
   - Responsable opérationnel d'une unité spécifique
   - Capacités :
     * Gestion des incidents de l'unité
     * Suivi des opérations quotidiennes
     * Validation des rapports d'incidents
     * Gestion des ressources de l'unité

5. **Utilisateur Standard** (`UTILISATEUR`)
   - Rôle avec accès le plus restreint
   - Capacités :
     * Création d'incidents
     * Consultation limitée
     * Interaction de base avec le système

### Modèle de Permissions Dynamique

Le système utilise un modèle de permissions granulaire qui permet un contrôle fin des accès :

```python
PERMISSIONS = {
    'ADMIN': {
        'can_create_users': True,
        'can_edit_users': True,
        'can_delete_users': True,
        'can_manage_incidents': True,
        'requires_unit_selection': False,
        'can_view_all_zones': True,
        # ... autres permissions
    },
    'EMPLOYEUR_DG': {
        # Permissions spécifiques pour la direction générale
    },
    # ... autres rôles
}
```

### Modèle de Sécurité Contextuel

- Chaque rôle est associé à un contexte organisationnel (Zone, Unité)
- Les permissions sont dynamiquement ajustées en fonction du contexte
- Système de délégation et de suppléance intégré

### Principes de Sécurité

1. **Moindre Privilège**: Chaque utilisateur dispose uniquement des permissions nécessaires à ses fonctions
2. **Séparation des Tâches**: Les rôles sont conçus pour éviter les conflits d'intérêts
3. **Traçabilité**: Toutes les actions sont journalisées avec le rôle et le contexte de l'utilisateur

### Évolutions et Flexibilité

- Le système permet l'ajout de nouveaux rôles sans modifier l'architecture existante
- Support de rôles temporaires et de missions spéciales
- Possibilité d'héritage et de composition des rôles

### Implémentation Technique

```python
class UserRole:
    ADMIN = 'Admin'
    EMPLOYEUR_DG = 'Employeur DG'
    EMPLOYEUR_ZONE = 'Employeur Zone'
    EMPLOYEUR_UNITE = 'Employeur Unité'
    UTILISATEUR = 'Utilisateur'

    # Descriptions et permissions détaillées
    ROLE_DESCRIPTIONS = { ... }
    PERMISSIONS = { ... }
```

### Considérations Avancées

- Authentification multi-facteurs recommandée pour les rôles à haute responsabilité
- Rotation périodique des accès critiques
- Audit de sécurité régulier des configurations de rôles

## Sécurité et Performances

### Mesures de Sécurité
- Authentification multi-facteurs
- Chiffrement des données sensibles
- Protection contre les injections SQL
- Journalisation des actions utilisateurs
- Gestion granulaire des permissions

### Optimisations
- Caching intelligent
- Requêtes de base de données optimisées
- Lazy loading des ressources
- Pagination des grands ensembles de données

## Déploiement et Maintenance

### Configuration
- Support `.env` pour la configuration
- Fichier `requirements.txt` pour la gestion des dépendances
- Configuration Procfile et render.yaml pour le déploiement cloud

### Monitoring
- Logs détaillés
- Métriques de performance
- Rapports d'erreurs automatisés

## Technologies et Bibliothèques Clés
- Flask
- SQLAlchemy
- Flask-Login
- ReportLab
- OpenPyXL
- Bootstrap
- jQuery
- DataTables
- Chart.js

## Évolutions Futures
- Intégration de machine learning
- Tableaux de bord prédictifs
- Amélioration continue de l'agent IA
- Support multilingue
- Synchronisation avec des systèmes externes

---

**Note**: Cette documentation est un document vivant, régulièrement mis à jour pour refléter l'évolution du projet et les meilleures pratiques de développement.

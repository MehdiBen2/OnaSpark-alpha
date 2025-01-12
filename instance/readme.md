# ONA SPARK - User Management Documentation

## Système de Rôles et Permissions

### Types de Rôles

1. **Admin**
   - Rôle administrateur standard avec accès complet
   - Peut assigner des rôles et des permissions aux utilisateurs
   - Peut choisir les zones et les unités pour les autres utilisateurs
   - Aucune restriction de zone ou d'unité

2. **Employeur DG**
   - Accès global à toutes les données
   - Peut voir toutes les zones et unités
   - Aucune restriction de zone ou d'unité requise

3. **Employeur Zone**
   - Accès limité à une zone spécifique
   - L'administrateur doit assigner l'utilisateur à une zone
   - Les données de zone sont récupérées depuis la base de données dbona.db
   - Ne peut pas accéder aux données d'autres zones

4. **Employeur Unité**
   - Accès limité à une unité spécifique dans une zone
   - L'administrateur doit assigner l'utilisateur à une zone puis à une unité
   - Les données sont récupérées depuis la base de données onadb.db
   - Restreint aux données de son unité uniquement

5. **Utilisateur**
   - Accès très restreint
   - Limité à une zone et une unité spécifiques
   - L'administrateur doit assigner à la fois la zone et l'unité

## Panneau de Création/Modification d'Utilisateur

### Champs du Formulaire

1. **Nom d'utilisateur (Obligatoire)**
   - Identifiant unique de l'utilisateur
   - Doit être unique dans le système
   - Minimum 3 caractères

2. **Nom d'affichage (Obligatoire)**
   - Nom affiché dans l'interface
   - Minimum 2 caractères

3. **Mot de passe**
   - Obligatoire pour la création
   - Optionnel lors de la modification
   - Minimum 6 caractères
   - Toggle pour afficher/masquer

4. **Rôle (Obligatoire)**
   - Détermine les permissions de l'utilisateur
   - Options disponibles selon le rôle de l'administrateur

5. **Zone (Conditionnel)**
   - Obligatoire pour : Employeur Zone, Employeur Unité, Utilisateur
   - Liste des zones disponibles
   - Source : dbona.db

6. **Unité (Conditionnel)**
   - Obligatoire pour : Employeur Unité, Utilisateur
   - Liste dynamique basée sur la zone sélectionnée
   - Source : onadb.db

### Affichage des Champs selon le Rôle

| Rôle           | Zone         | Unité        |
|----------------|--------------|--------------|
| Admin          | Masqué       | Masqué       |
| Employeur DG   | Masqué       | Masqué       |
| Employeur Zone | Obligatoire  | Masqué       |
| Employeur Unité| Obligatoire  | Obligatoire  |
| Utilisateur    | Obligatoire  | Obligatoire  |

### Validation et Sécurité

1. **Validation des Champs**
   - Tous les champs obligatoires doivent être remplis
   - Validation en temps réel des entrées
   - Messages d'erreur explicites

2. **Sécurité**
   - Vérification des permissions de l'administrateur
   - Validation des relations zone/unité
   - Protection contre les injections SQL

3. **Gestion des Erreurs**
   - Affichage des messages d'erreur clairs
   - Maintien des données en cas d'erreur
   - Log des erreurs pour le débogage

### Workflow de Création/Modification

1. **Création d'Utilisateur**
   - Remplir tous les champs obligatoires
   - Sélectionner le rôle approprié
   - Assigner zone/unité si nécessaire
   - Validation et création

2. **Modification d'Utilisateur**
   - Chargement des données existantes
   - Modification des champs nécessaires
   - Mot de passe optionnel
   - Validation et mise à jour

### API Endpoints

1. **Création d'Utilisateur**
   ```
   POST /admin/users/create
   Content-Type: application/json
   {
     "username": string,
     "nickname": string,
     "password": string,
     "role": string,
     "zone_id": number (optional),
     "unit_id": number (optional)
   }
   ```

2. **Modification d'Utilisateur**
   ```
   POST /admin/users/<user_id>/edit
   Content-Type: application/json
   {
     "username": string,
     "nickname": string,
     "password": string (optional),
     "role": string,
     "zone_id": number (optional),
     "unit_id": number (optional)
   }
   ```

3. **Récupération des Unités par Zone**
   ```
   GET /api/zones/<zone_id>/units
   Returns: Array of units
   ```

### Tests et Vérifications

1. **Tests Fonctionnels**
   - [ ] Création d'utilisateurs pour chaque rôle
   - [ ] Modification d'utilisateurs existants
   - [ ] Validation des champs obligatoires
   - [ ] Chargement dynamique des unités

2. **Tests de Sécurité**
   - [ ] Vérification des permissions
   - [ ] Protection contre les injections
   - [ ] Validation des données

3. **Tests d'Interface**
   - [ ] Affichage correct des champs
   - [ ] Messages d'erreur appropriés
   - [ ] Réactivité de l'interface

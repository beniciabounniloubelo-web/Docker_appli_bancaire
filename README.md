# BankApp — Application bancaire web

Application bancaire fictive déployée via Docker.  
**Contenu :** gestion de comptes · virements · historique des transactions · authentification  
**Stack :** Python · HTML · CSS · Docker

> Projet académique — BUT Informatique

# Structure du projet
L'application se compose alors en trois parties :

### Backend (API FastAPI) : 
Le backend sera soit FastAPI soit je ne sais quoi...
Il gèrera les opérations CRUD (Créer, Lire, Mettre à jour, Supprimer) des comptes des clients dans la base de données.

### Base de données (PostgreSQL) : 
Nous utiliserons PostgreSQL pour stocker les informations des clients qui se définissent par un user, son propre mot de passe, et un niveau de compte.

### Frontend (Python)

- nginx.conf : ligne 12
    Redirection vers le Backend (FastAPI)
    L'utilisateur appelle /backend/virement -> Nginx appelle http://backend:8000/virement

- Dockerfile
dépendanaces et liens vers les fichiers pour que le
```bash
sudo docker compose up
```
prenne en compte leur lien dans un premier 

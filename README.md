# Mini Projet de DEV4.2

## Intro

En grandes lignes, on va faire une application bancaire en web, sur un modèle à trois.

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
prenne en compte leur lien dans un premier temps, puis après ce sera dans le docker compose.
## Ressources

- Énoncé : [Sujet](https://grond.iut-fbleau.fr/menault/DEV_42_Docker/src/branch/main/mini-projet.txt)
- Documentation : [Docker](https://docs.docker.com/)

## Credits :

- [Arwa Benfraj](https://grond.iut-fbleau.fr/benfraj)
- [Benicia Bounni Loubelo](https://grond.iut-fbleau.fr/bounnilo)
- [Ibrahima BAH](https://grond.iut-fbleau.fr/bah)
- [Tarehi Zaabay](https://grond.iut-fbleau.fr/zaabay)
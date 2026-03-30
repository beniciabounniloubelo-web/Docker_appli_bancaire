from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os # pour lire .env de docker
import random # pour créer un IBAN

app = FastAPI()

def read_secret(secret_name):
    """Lit un secret Docker depuis /run/secrets/"""
    try:
        with open(f"/run/secrets/{secret_name}", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback sur variable d'environnement (dev local)
        return os.getenv(secret_name.upper())

# Connexion à la base de données
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),     
        port=5432,
        database=read_secret("db_name"),
        user=read_secret("db_user"),
        password=read_secret("db_password")
    )

def generer_iban():
    # Génère un IBAN français de 27 caractères généré
    chiffres = ''.join([str(random.randint(0, 9)) for _ in range(23)])
    return f"FR76{chiffres}"

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    nom: str
    email: str
    password: str
    age: int

# ─────────────────────────────────────────
# POST /register
# Créer un compte utilisateur avec vérification d'âge et bonus
# Body attendu : { "nom": "Jean", "email": "jean@test.com", "password": "123", "age": 18 }
# ─────────────────────────────────────────
@app.post("/register")
def register(user: UserRegister):
    if user.age < 16:
        raise HTTPException(status_code=400, detail="Il faut avoir au moins 16 ans.")
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit faire 8 caractères minimum.")
    
    # Calcul du bonus à l'inscription
    bonus1 = 15.00 if 16 <= user.age <= 25 else 10.00
    bonus2 = 5
    nouvel_iban = generer_iban()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO utilisateurs (nom, email, password, age, iban) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                       (user.nom, user.email, user.password, user.age, nouvel_iban))
        new_id = cursor.fetchone()[0]
        # Création du compte courant avec le solde de bienvenue (le bonus)
        cursor.execute("INSERT INTO comptes (user_id, solde, type) VALUES (%s, %s, 'courant')", (new_id, bonus1))
        cursor.execute("INSERT INTO comptes (user_id, solde, type) VALUES (%s, %s, 'epargne')", (new_id, bonus2))
        conn.commit()
        return {"message": f"Compte créé avec un bonus de bienvenue de {bonus1}€ et en épargne {bonus2}€ !", "user_id": new_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Erreur d'inscription (Email déjà utilisé ?)")
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────
# POST /login
# Vérifier email + mot de passe
# Body attendu : { "email": "arwa@test.com", "password": "1234" }
# ─────────────────────────────────────────
@app.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, iban FROM utilisateurs WHERE email = %s AND password = %s", (user.email, user.password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    return {"message": "Connexion réussie", "user_id": result[0], "nom": result[1], "iban": result[2]}

# ─────────────────────────────────────────
# GET /comptes/{numUtilisateur}
# Récupérer tous les comptes d'un utilisateur
# ─────────────────────────────────────────
@app.get("/comptes/{numUtilisateur}")
def get_comptes(numUtilisateur: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, solde, type FROM comptes WHERE user_id = %s", (numUtilisateur,))
    resultats = [{"id": row[0], "solde": row[1], "type": row[2]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    if not resultats:
        raise HTTPException(status_code=404, detail="Aucun compte trouvé")
    return {"comptes": resultats}

# ─────────────────────────────────────────
# POST /comptes/{numUtilisateur}
# Ouvrir un compte
# ─────────────────────────────────────────
@app.post("/comptes/ouvrir")
def ouvrir_nouveau_compte(data: dict):
    # data contient {"user_id": X, "type": "Livret A"}
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO comptes (user_id, solde, type) VALUES (%s, 0, %s)",
            (data["user_id"], data["type"])
        )
        conn.commit()
        return {"message": f"Compte {data['type']} ouvert avec succès !"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Erreur lors de l'ouverture")
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────
# GET /beneficiaires/{numUtilisateur}
# Récupérer la liste des bénéficiaires pour les listes déroulantes
# ─────────────────────────────────────────
@app.get("/beneficiaires/{numUtilisateur}")
def get_beneficiaires(numUtilisateur: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, iban FROM beneficiaires WHERE user_id = %s", (numUtilisateur,))
    resultats = [{"id": row[0], "nom": row[1], "iban": row[2]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"beneficiaires": resultats}

# ─────────────────────────────────────────
# POST /beneficiaires
# Ajouter un bénéficiaire via son EMAIL (Gère les homonymes)
# Body attendu : { "nom_choisi": "Mon Pote Jean", "email_ami": "jean@test.fr", "user_id": 1 }
# ─────────────────────────────────────────
@app.post("/beneficiaires")
def ajouter_beneficiaire(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Recherche IBAN via son e-mail
        cursor.execute("SELECT iban FROM utilisateurs WHERE email = %s", (data["email_ami"],))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Aucun client trouvé avec cet email.")
            
        iban_ami = result[0]

        # Ajout aux bénéficiaires
        cursor.execute("INSERT INTO beneficiaires (nom, iban, user_id) VALUES (%s, %s, %s)",
                       (data["nom_choisi"], iban_ami, data["user_id"]))
        conn.commit()
        return {"message": "Bénéficiaire ajouté avec succès !"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Erreur d'ajout (bénéficiaire introuvable ou déjà ajouté)")
    finally:
        cursor.close()
        conn.close()
# ─────────────────────────────────────────
# POST /virement
# Débiter un compte et créditer un autre via l'IBAN
# Body attendu : { "montant": 100, "compte_source": 1, "iban_dest": "FR76..." }
# ─────────────────────────────────────────
@app.post("/virement")
def faire_virement(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Trouver l'ID du compte destination grâce à l'IBAN
        cursor.execute("SELECT c.id FROM comptes c JOIN utilisateurs u ON c.user_id = u.id WHERE u.iban = %s", (data["iban_dest"],))
        dest_result = cursor.fetchone()
        if not dest_result:
            raise HTTPException(status_code=404, detail="IBAN destination inconnu dans notre banque")
        compte_dest_id = dest_result[0]

        # Mettre à jour les soldes (vérifié aussi par le CHECK en DB)
        cursor.execute("UPDATE comptes SET solde = solde - %s WHERE id = %s", (data["montant"], data["compte_source"]))
        cursor.execute("UPDATE comptes SET solde = solde + %s WHERE id = %s", (data["montant"], compte_dest_id))
        
        # Enregistrer le virement dans l'historique
        cursor.execute("INSERT INTO virements (source, destination, montant) VALUES (%s, %s, %s)", (data["compte_source"], compte_dest_id, data["montant"]))
        conn.commit()
        return {"message": "Virement effectué"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Solde insuffisant ou erreur")
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────
# GET /historique/{numUtilisateur}
# Récupérer l'historique des virements (Entrées / Sorties)
# ─────────────────────────────────────────
@app.get("/historique/{numUtilisateur}")
def get_historique(numUtilisateur: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT v.montant, v.date_virement, 
           CASE WHEN c_src.user_id = %s THEN 'Sortie' ELSE 'Entrée' END as type_mouvement
    FROM virements v
    JOIN comptes c_src ON v.source = c_src.id
    JOIN comptes c_dest ON v.destination = c_dest.id
    WHERE c_src.user_id = %s OR c_dest.user_id = %s
    ORDER BY v.date_virement DESC
    """
    cursor.execute(query, (numUtilisateur, numUtilisateur, numUtilisateur))
    hist = [{"montant": row[0], "date": row[1], "type": row[2]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"historique": hist}

# ─────────────────────────────────────────
# GET /admin/tous-les-comptes
# Vue globale pour le directeur de la banque
# ─────────────────────────────────────────
@app.get("/admin/tous-les-comptes")
def get_all_comptes():
    conn = get_db_connection()
    cursor = conn.cursor()
    # On fait une jointure pour avoir le nom du client et les infos de son compte
    query = """
    SELECT u.id, u.nom, u.email, c.type, c.solde 
    FROM utilisateurs u 
    JOIN comptes c ON u.id = c.user_id 
    ORDER BY u.id
    """
    cursor.execute(query)
    resultats = [{"user_id": row[0], "nom": row[1], "email": row[2], "type": row[3], "solde": row[4]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"comptes_globaux": resultats}


    # ─────────────────────────────────────────
# POST /virement-interne
# Virement entre deux comptes du MÊME utilisateur
# Body attendu : { "compte_source": 1, "compte_dest": 2, "montant": 50.0 }
# ─────────────────────────────────────────
@app.post("/virement-interne")
def virement_interne(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if data["compte_source"] == data["compte_dest"]:
            raise HTTPException(status_code=400, detail="Source et destination identiques")
 
        # Vérifier que les deux comptes appartiennent bien au même utilisateur
        cursor.execute("SELECT user_id FROM comptes WHERE id = %s", (data["compte_source"],))
        src = cursor.fetchone()
        cursor.execute("SELECT user_id FROM comptes WHERE id = %s", (data["compte_dest"],))
        dst = cursor.fetchone()
 
        if not src or not dst:
            raise HTTPException(status_code=404, detail="Compte introuvable")
        if src[0] != dst[0]:
            raise HTTPException(status_code=403, detail="Ces comptes n'appartiennent pas au même utilisateur")
 
        cursor.execute("UPDATE comptes SET solde = solde - %s WHERE id = %s", (data["montant"], data["compte_source"]))
        cursor.execute("UPDATE comptes SET solde = solde + %s WHERE id = %s", (data["montant"], data["compte_dest"]))
        cursor.execute("INSERT INTO virements (source, destination, montant) VALUES (%s, %s, %s)",
                       (data["compte_source"], data["compte_dest"], data["montant"]))
        conn.commit()
        return {"message": "Virement interne effectué"}
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Solde insuffisant ou erreur")
    finally:
        cursor.close()
        conn.close()
import psycopg2
import os
import time

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

def wait_for_db():
    while True:
        try:
            conn = get_db_connection()
            conn.close()
            print("DB prête !")
            break
        except Exception as e:
            print("En attente DB...", e)
            time.sleep(2)

# on appelle la fonction AVANT de commencer
wait_for_db()

def appliquer_interets():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE comptes
            SET solde = solde * 1.03
            WHERE type ILIKE 'epargne'
        """)
        # Lire rowcount AVANT le commit
        lignes = cursor.rowcount
        conn.commit()
        print(f"Lignes modifiées : {lignes}")
        
        # Vérification : afficher les soldes après mise à jour
        cursor.execute("SELECT id, solde FROM comptes WHERE type ILIKE 'epargne'")
        for row in cursor.fetchall():
            print(f"  Compte épargne id={row[0]} → solde={row[1]}")
            
        print("Intérêts appliqués aux comptes épargne.")
    except Exception as e:
        conn.rollback()
        print("Erreur lors de l'application des intérêts :", e)
    finally:
        cursor.close()
        conn.close()


# boucle infinie du service
while True:
    appliquer_interets()

    print("Prochaine mise à jour dans 24h")

    time.sleep(86400)  # 24h
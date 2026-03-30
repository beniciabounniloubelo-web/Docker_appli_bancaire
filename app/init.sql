CREATE TABLE utilisateurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    iban VARCHAR(34) UNIQUE NOT NULL
);

CREATE TABLE comptes (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES utilisateurs(id),
    solde NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    type VARCHAR(50) NOT NULL,
    CONSTRAINT solde_positif CHECK (solde >= 0)
);

CREATE TABLE virements (
    id SERIAL PRIMARY KEY,
    source INT REFERENCES comptes(id),
    destination INT REFERENCES comptes(id),
    montant NUMERIC(10, 2) NOT NULL,
    date_virement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE beneficiaires (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    iban VARCHAR(50) NOT NULL,
    user_id INT REFERENCES utilisateurs(id)
);

-- Données de test (Admin)
INSERT INTO utilisateurs (nom, email, password, age, iban) 
VALUES ('Admin', 'admin@banque.fr', 'admin123', 30, 'FR7600000000000000000000000');

INSERT INTO comptes (user_id, solde, type) 
VALUES (1, 1000.00, 'courant');

INSERT INTO comptes (user_id, solde, type) 
VALUES (1, 50.00, 'epargne');
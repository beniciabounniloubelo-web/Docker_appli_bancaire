// URL du backend via Nginx
const API_URL = "/backend";

let currentUserId = null; // Token JWT ou session (Ici on utilise l'ID utilisateur)
let currentUserIban = "";
let myChart = null; // Stocke le graphique Chart.js


// Validation du mot de passe (Rouge si < 8 caractères)
document.getElementById('reg-pass').addEventListener('input', function(e) {
    if(e.target.value.length < 8) {
        e.target.style.border = "3px inset #ff0000";
        e.target.style.backgroundColor = "#ffe6e6";
    } else {
        e.target.style.border = "3px inset #808080";
        e.target.style.backgroundColor = "#FFF";
    }
});

// Validation du montant de virement (Rouge si < 2€)
document.getElementById('montant').addEventListener('input', function(e) {
    const val = parseFloat(e.target.value);
    const msg = document.getElementById('msg-erreur-montant');
    
    if (val < 2) {
        e.target.style.border = "3px inset #ff0000";
        if(msg) {
            msg.innerText = "Soit convenable, 2€ minimum !";
            msg.style.display = "block";
        }
    } else {
        e.target.style.border = "3px inset #808080";
        if(msg) msg.style.display = "none";
    }
});

// --- Fonctions de navigation (SPA) ---
function showSection(id) {
    const sections = ['section-register', 'section-login', 'section-home', 'section-virements'];
    sections.forEach(s => {
        const el = document.getElementById(s);
        if (el) el.style.display = 'none';
    });
    document.getElementById(id).style.display = 'block';
}

function logout() {
    currentUserId = null;
    document.getElementById('nav-menu').style.display = 'none';
    showSection('section-register');
}

function masquerIban(iban) {
    if (!iban || iban.length < 10) return iban;
    return iban.substring(0, 4) + " **** **** **** " + iban.substring(iban.length - 4);
}

// Inscription en tant que client (id)
async function register() {
    const nom = document.getElementById('reg-nom').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-pass').value;
    const age = parseInt(document.getElementById('reg-age').value);

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nom, email, password, age })
        });

        const data = await response.json();
        if (response.ok) {
            alert(data.message); // Affiche le succès et le bonus
            showSection('section-login');
        } else {
            alert("Erreur: " + data.detail);
        }
    } catch (e) {
        console.error("Erreur register", e);
        alert("Erreur réseau");
    }
}

// Connexion
async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-pass').value;

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (response.ok) {
            const data = await response.json();
            currentUserId = data.user_id; 
            currentUserIban = data.iban;
            
            document.getElementById('user-display').innerText = data.nom;
            document.getElementById('iban-display').innerText = masquerIban(currentUserIban);
            
            document.getElementById('nav-menu').style.display = 'block';
            showSection('section-home');

            // ADMIN
            if (currentUserId === 1) {
                document.getElementById('admin-panel').style.display = 'block';
                loadAdminData(); // On charge la liste globale si c'est l'admin
            } else {
                document.getElementById('admin-panel').style.display = 'none';
            }
            

            loadComptes();
            loadBeneficiaires();
            loadHistoriqueEtGraphique();
            
            alert("Connexion réussie !");
        } else {
            alert("Erreur de connexion");
        }
    } catch (e) {
        console.error("Erreur login", e);
    }
}

// Ouvrir un compte
async function ouvrirCompte() {
    const type = document.getElementById('type-nouveau-compte').value;
    const response = await fetch(`${API_URL}/comptes/ouvrir`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: currentUserId, type: type })
    });
    if (response.ok) {
        alert("Nouveau compte ouvert !");
        loadComptes(); // Rafraîchit la liste
    }
}

// Charger les comptes
async function loadComptes() {
    if (!currentUserId) return;

    try {
        const response = await fetch(`${API_URL}/comptes/${currentUserId}`, {
            // headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            
            // Affichage dans le Dashboard
            const div = document.getElementById('comptes-list');
            div.innerHTML = data.comptes.map(c => `
                <div class="item">
                    <p>Compte ${c.type} : <strong style="color:green; font-size: 1.2em;">${c.solde}€</strong></p>
                </div>
            `).join('');

            // Remplissage de la liste déroulante pour les virements
            const selectSource = document.getElementById('source');
            selectSource.innerHTML = '<option value="">-- Compte à débiter --</option>' + 
                data.comptes.map(c => `<option value="${c.id}">Compte ${c.type} (${c.solde}€)</option>`).join('');

            // Remplissage des listes déroulantes pour les virements internes
            const optionsInternes = data.comptes.map(c => `<option value="${c.id}">Compte ${c.type} (${c.solde}€)</option>`).join('');
            document.getElementById('interne-source').innerHTML = '<option value="">-- Compte à débiter --</option>' + optionsInternes;
            document.getElementById('interne-dest').innerHTML = '<option value="">-- Compte à créditer --</option>' + optionsInternes;    
        }
    } catch (e) {
        console.error("Erreur chargement comptes", e);
    }
}

// Charger les bénéficiaires
async function loadBeneficiaires() {
    if (!currentUserId) return;

    try {
        const response = await fetch(`${API_URL}/beneficiaires/${currentUserId}`);
        if (response.ok) {
            const data = await response.json();
            const selectDest = document.getElementById('dest');
            selectDest.innerHTML = '<option value="">-- Bénéficiaire --</option>' + 
                data.beneficiaires.map(b => `<option value="${b.iban}">${b.nom} (${masquerIban(b.iban)})</option>`).join('');
        }
    } catch (e) {
        console.error("Erreur chargement bénéficiaires", e);
    }
}

// Ajouter un bénéficiaire
async function addBenef() {
    if (!currentUserId) return alert("Veuillez vous connecter d'abord");

    const nom = document.getElementById('benef-name').value;
    const emailAmi = document.getElementById('benef-email').value; // On récupère l'email

    if (!nom || !emailAmi) return alert("Veuillez remplir tous les champs");

    try {
        const response = await fetch(`${API_URL}/beneficiaires`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nom_choisi: nom, email_ami: emailAmi, user_id: currentUserId })
        });

        if (response.ok) {
            alert("Bénéficiaire ajouté avec succès !");
            document.getElementById('benef-name').value = '';
            document.getElementById('benef-email').value = '';
            loadBeneficiaires(); 
        } else {
            const err = await response.json();
            alert("Erreur : " + (err.detail || "Client introuvable"));
        }
    } catch (e) {
        console.error("Erreur addBenef", e);
    }
}

// Faire un virement
async function transfvir() {
    if (!currentUserId) return alert("Veuillez vous connecter d'abord");

    const source = document.getElementById('source').value;
    const destIban = document.getElementById('dest').value;
    const montant = document.getElementById('montant').value;

    try {
        const response = await fetch(`${API_URL}/virement`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                compte_source: parseInt(source), 
                iban_dest: destIban, 
                montant: parseFloat(montant) 
            })
        });

        if (response.ok) {
            alert("Virement réussi !");
            loadComptes(); // Rafraîchit les soldes
            loadHistoriqueEtGraphique(); // MAJ le graphique et l'historique
        } else {
            const err = await response.json();
            alert("Erreur : " + (err.detail || "Opération impossible"));
        }
    } catch (e) {
        console.error("Erreur virement", e);
        alert("Erreur réseau");
    }
}

// Recevoir des sous
async function recevoirArgent() {
    const montant = document.getElementById('depot-montant').value;
    const response = await fetch(`${API_URL}/virement`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            compte_source: 1, // L'argent vient de la banque (Admin)
            iban_dest: currentUserIban, 
            montant: parseFloat(montant) 
        })
    });
    if (response.ok) {
        alert("Argent reçu !");
        loadComptes();
        loadHistoriqueEtGraphique();
    }
}

// Charger l'historique et dessiner le graphique Chart.js
async function loadHistoriqueEtGraphique() {
    try {
        const response = await fetch(`${API_URL}/historique/${currentUserId}`);
        if (response.ok) {
            const data = await response.json();
            
            // bloc historique texte
            const divHist = document.getElementById('historique-list');
            divHist.innerHTML = data.historique.map(h => `
                <p style="border-bottom: 1px dotted #ccc; margin: 5px 0;">
                    ${h.date.substring(0, 10)} - 
                    <span style="color: ${h.type === 'Entrée' ? 'green' : 'red'}; font-weight: bold;">
                        ${h.type === 'Entrée' ? '+' : '-'}${h.montant}€
                    </span>
                </p>
            `).join('') || "<p>Aucune transaction pour le moment.</p>";

            // quelques calculs
            let totalEntrees = 0;
            let totalSorties = 0;
            data.historique.forEach(h => {
                if (h.type === 'Entrée') totalEntrees += parseFloat(h.montant);
                else totalSorties += parseFloat(h.montant);
            });

            // Graphique
            const ctx = document.getElementById('financeChart').getContext('2d');
            if (myChart) myChart.destroy(); // Remplacement
            
            myChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Entrées (€)', 'Sorties (€)'],
                    datasets: [{
                        data: [totalEntrees, totalSorties],
                        backgroundColor: ['#00ff00', '#ff0000'],
                        borderColor: '#000',
                        borderWidth: 2
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
    } catch (e) {
        console.error("Erreur historique", e);
    }
}

// Charger les données de tous les clients (Admin)
async function loadAdminData() {
    const response = await fetch(`${API_URL}/admin/tous-les-comptes`);
    if (response.ok) {
        const data = await response.json();
        const div = document.getElementById('admin-list');
        div.innerHTML = data.comptes_globaux.map(c => `
            <p style="border-bottom: 1px solid #ccc; margin: 2px;">
                <strong>${c.nom}</strong> (${c.email}) - Compte ${c.type} : <span style="color:green;">${c.solde}€</span>
            </p>
        `).join('');
    }
}

// Virement interne entre ses propres comptes
async function virementInterne() {
    if (!currentUserId) return alert("Veuillez vous connecter d'abord");
 
    const source = document.getElementById('interne-source').value;
    const dest   = document.getElementById('interne-dest').value;
    const montant = parseFloat(document.getElementById('interne-montant').value);
 
    if (!source || !dest) return alert("Sélectionnez les deux comptes");
    if (source === dest)  return alert("Les comptes source et destination doivent être différents");
    if (isNaN(montant) || montant < 1) return alert("Montant minimum : 1€");
 
    try {
        const response = await fetch(`${API_URL}/virement-interne`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ compte_source: parseInt(source), compte_dest: parseInt(dest), montant })
        });
 
        if (response.ok) {
            alert("Virement interne réussi !");
            loadComptes();
            loadHistoriqueEtGraphique();
        } else {
            const err = await response.json();
            alert("Erreur : " + (err.detail || "Opération impossible"));
        }
    } catch (e) {
        console.error("Erreur virementInterne", e);
        alert("Erreur réseau");
    }
}
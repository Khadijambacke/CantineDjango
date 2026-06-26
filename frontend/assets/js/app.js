// ============================================================
// CantinEntreprise - Module JavaScript Principal
// ============================================================
// Ce fichier centralise TOUTES les interactions avec l'API Django.
// Chaque page HTML importe ce fichier et appelle les fonctions dont elle a besoin.
//
// ROUTES API UTILISÉES :
//   POST /api/register/         -> Inscription (nom, prenom, email, telephone, poste, password)
//   POST /api/verify-otp/       -> Vérification OTP (email, otp_code)
//   POST /api/resend-otp/       -> Renvoyer le code OTP (email)
//   POST /api/login/            -> Connexion (email, password) -> retourne { jwt, user }
//   POST /api/logout/           -> Déconnexion
//   GET  /api/me/               -> Profil utilisateur connecté
//   GET  /api/plats/            -> Liste de tous les plats (catalogue)
//   POST /api/plats/            -> Créer un plat (gestionnaire/cuisinier)
//   GET  /api/menus/            -> Menus du jour et à venir
//   POST /api/menus/            -> Publier un menu du jour (gestionnaire)
//   GET  /api/menus/stats/      -> Stats de préparation par date (cuisinier)
//   GET  /api/reservations/     -> Mes réservations (employé)
//   POST /api/reservations/     -> Créer une réservation (employé)
//   DELETE /api/reservations/:id -> Annuler une réservation (employé)
//   GET  /api/notifications/    -> Mes notifications
//   PATCH /api/notifications/:id/read/ -> Marquer comme lue
// ============================================================

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// ── Requête générique ────────────────────────────────────────
async function fetchAPI(endpoint, method = 'GET', data = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('token');
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const config = { method, headers };
    if (data) config.body = JSON.stringify(data);

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const result = await response.json();

    if (!response.ok) {
        const err = new Error(result.error || result.message || 'Erreur serveur');
        err.status = response.status;
        err.body = result;
        throw err;
    }
    return result;
}

// ── Auth helpers ─────────────────────────────────────────────
function isAuthenticated() {
    return localStorage.getItem('token') !== null;
}

function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

function redirectUserByRole(role) {
    const map = {
        'gestionnaire': 'dashboard-gestionnaire.html',
        'administrateur': 'dashboard-admin.html',
        'cuisinier': 'dashboard-cuisinier.html',
        'employe': 'dashboard-employe.html'
    };
    window.location.href = map[role] || 'dashboard-employe.html';
}

function checkAuthGuard() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return false;
    }
    return true;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// ── UI helpers ───────────────────────────────────────────────
function showToast(message, type = 'success') {
    const existing = document.getElementById('toast-notification');
    if (existing) existing.remove();

    const colors = {
        success: 'bg-green-600',
        error: 'bg-red-600',
        info: 'bg-blue-600'
    };

    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = `fixed top-6 left-1/2 -translate-x-1/2 ${colors[type]} text-white px-6 py-3 rounded-xl shadow-lg text-sm font-bold z-[9999] transition-all`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function setLoading(btn, loading) {
    if (loading) {
        btn.dataset.original = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
        btn.disabled = true;
    } else {
        btn.innerHTML = btn.dataset.original || btn.innerHTML;
        btn.disabled = false;
    }
}

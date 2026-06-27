// gestionnaire.js
const API_URL = 'http://127.0.0.1:8000/api';

async function req(endpoint, method='GET', data=null) {
    const h = {'Content-Type':'application/json'};
    const tk = localStorage.getItem('token');
    if(tk) h['Authorization'] = `Bearer ${tk}`;
    const cfg = {method, headers:h};
    if(data) cfg.body = JSON.stringify(data);
    const r = await fetch(API_URL+endpoint, cfg);
    const j = await r.json();
    if(!r.ok) throw new Error(j.message||j.detail||'Erreur serveur');
    return j;
}

function logout(){localStorage.clear();window.location.href='index.html';}
function getUser(){const u=localStorage.getItem('user');return u?JSON.parse(u):null;}

const TABS = ['vue-globale','employes','commandes','facturation','notifications','avis'];
function showTab(tab) {
    TABS.forEach(t=>{
        const el=document.getElementById('tab-'+t);
        const btn=document.getElementById('nav-'+t);
        if(el) el.classList.toggle('hidden', t!==tab);
        if(btn){
            btn.classList.toggle('bg-brandLight', t===tab);
            btn.classList.toggle('text-brand', t===tab);
            btn.classList.toggle('text-textMuted', t!==tab);
        }
    });
}

document.addEventListener('DOMContentLoaded', async()=>{
    if(!localStorage.getItem('token')){window.location.href='index.html';return;}
    const user=getUser();
    if(user){
        document.querySelectorAll('.u-avatar').forEach(el=>el.textContent=(user.prenom||'G')[0]);
        document.querySelectorAll('.u-name').forEach(el=>el.textContent=user.prenom+' '+user.nom);
    }
    showTab('vue-globale');
    await Promise.all([loadDashboard(), loadNotifications()]);
    await Promise.all([loadEmployes(), loadCommandes(), loadEvaluations()]);
});

// ─── VUE GLOBALE ─────────────────────────────────────────────────────────────
let employesList = [];
async function loadDashboard() {
    try {
        const r = await req('/dashboard/gestionnaire/');
        const d = r.data;
        document.getElementById('kpiRevenu').textContent = parseFloat(d.kpis.revenu_mensuel).toLocaleString('fr-FR');
        document.getElementById('kpiRepas').textContent = d.kpis.repas_servis;
        document.getElementById('kpiTaux').textContent = d.kpis.taux_reservation+'%';
        document.getElementById('kpiFactures').textContent = d.kpis.factures_en_attente;
    } catch(e){ showToast(e.message,'error'); }
}

// ─── EMPLOYÉS ────────────────────────────────────────────────────────────────
async function loadEmployes() {
    try {
        const r = await req('/gestionnaire/employes/');
        employesList = r.data||[];
        renderEmployes(employesList);
    } catch(e){ showToast(e.message,'error'); }
}

function renderEmployes(list) {
    // Preview dans vue globale (top 5)
    const preview = document.getElementById('empPreview');
    if(preview) {
        preview.innerHTML = list.slice(0,5).map(e=>buildEmpRow(e, true)).join('');
    }
    // Tableau complet dans onglet Employés
    const full = document.getElementById('empFull');
    if(full) {
        if(list.length===0){
            full.innerHTML=`<tr><td colspan="5" class="p-8 text-center text-textMuted">Aucun utilisateur trouvé.</td></tr>`;
            return;
        }
        full.innerHTML = list.map(e=>buildEmpRow(e, false)).join('');
    }
}

function buildEmpRow(e, compact) {
    const init = (e.prenom||'X')[0];
    const isActive = e.is_verified;
    const mc = e.mode_paiement==='facture'?'bg-blue-50 text-blue-600':'bg-green-50 text-success';
    const ml = e.mode_paiement==='facture'?'Sur Salaire':'Solde';
    const depense = parseFloat(e.depenses_mensuelles||0);
    const roleColor = e.role==='cuisinier'?'bg-amber-100 text-amber-700':'bg-gray-100 text-gray-600';
    const roleLabel = e.role==='cuisinier'?'Cuisinier':'Employé';

    const actions = compact ? '' : `
        <td class="p-4 text-right">
            <div class="flex items-center justify-end space-x-2">
                <button onclick="toggleActive(${e.id}, ${isActive})" title="${isActive?'Désactiver':'Activer'}"
                    class="w-8 h-8 rounded-lg ${isActive?'bg-orange-50 text-orange-500 hover:bg-orange-100':'bg-green-50 text-green-500 hover:bg-green-100'} flex items-center justify-center transition">
                    <i class="fa-solid ${isActive?'fa-lock-open':'fa-lock'} text-xs"></i>
                </button>
                <button onclick="deleteUser(${e.id}, '${e.prenom} ${e.nom}')" title="Supprimer"
                    class="w-8 h-8 rounded-lg bg-red-50 text-red-400 hover:bg-red-100 flex items-center justify-center transition">
                    <i class="fa-solid fa-trash text-xs"></i>
                </button>
            </div>
        </td>`;

    return `<tr class="border-b border-gray-50 last:border-0 hover:bg-gray-50/50 transition ${!isActive?'opacity-50':''}">
        <td class="p-4">
            <div class="flex items-center">
                <div class="w-9 h-9 rounded-full ${mc} flex items-center justify-center font-bold text-sm mr-3 flex-shrink-0 relative">
                    ${init}
                    ${!isActive?`<span class="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full border border-white" title="Désactivé"></span>`:''}
                </div>
                <div class="min-w-0">
                    <p class="font-bold text-sm truncate">${e.prenom} ${e.nom}</p>
                    <p class="text-[10px] text-textMuted truncate">${e.email}</p>
                </div>
            </div>
        </td>
        <td class="p-4 text-xs text-textMuted">${e.poste||'-'}</td>
        <td class="p-4"><span class="text-[10px] font-bold px-2 py-1 rounded-full ${roleColor}">${roleLabel}</span></td>
        <td class="p-4 text-right font-extrabold ${depense>0?'text-brand':'text-textMuted'} text-sm">${depense.toLocaleString('fr-FR')} CFA</td>
        ${actions}
    </tr>`;
}

// Filtrer par rôle
function filterEmp(role) {
    document.querySelectorAll('.emp-filter-btn').forEach(b=>b.classList.remove('bg-brand','text-white'));
    document.querySelectorAll('.emp-filter-btn').forEach(b=>b.classList.add('bg-surface','text-textMuted'));
    event.target.classList.add('bg-brand','text-white');
    event.target.classList.remove('bg-surface','text-textMuted');
    const filtered = role==='tous' ? employesList : employesList.filter(e=>e.role===role);
    renderEmployes(filtered);
}

async function toggleActive(id, currentlyActive) {
    if(!confirm(currentlyActive?'Désactiver ce compte ? L\'utilisateur ne pourra plus se connecter.':'Réactiver ce compte ?')) return;
    try {
        await req(`/gestionnaire/employes/${id}/`, 'PATCH', {is_verified: !currentlyActive});
        showToast(currentlyActive?'Compte désactivé.':'Compte réactivé.', 'info');
        await loadEmployes();
    } catch(e){ showToast(e.message,'error'); }
}

async function deleteUser(id, name) {
    if(!confirm(`Supprimer définitivement le compte de ${name} ? Cette action est irréversible.`)) return;
    try {
        await req(`/gestionnaire/employes/${id}/`, 'DELETE');
        showToast(`Compte de ${name} supprimé.`, 'success');
        await loadEmployes();
    } catch(e){ showToast(e.message,'error'); }
}

// Modal Ajouter un compte
function openAddUser() {
    document.getElementById('modalAddUser').classList.remove('hidden');
    document.getElementById('addUserError').classList.add('hidden');
    document.getElementById('formAddUser').reset();
}
function closeAddUser() { document.getElementById('modalAddUser').classList.add('hidden'); }

async function submitAddUser(e) {
    e.preventDefault();
    const btn = document.getElementById('addUserBtn');
    const errEl = document.getElementById('addUserError');
    btn.disabled=true; btn.innerHTML='<i class="fa-solid fa-spinner fa-spin mr-2"></i>Création...';
    errEl.classList.add('hidden');

    const data = {
        nom: document.getElementById('fNom').value,
        prenom: document.getElementById('fPrenom').value,
        email: document.getElementById('fEmail').value,
        telephone: document.getElementById('fTel').value,
        poste: document.getElementById('fPoste').value,
        role: document.getElementById('fRole').value,
        password: document.getElementById('fPassword').value,
    };

    try {
        await req('/gestionnaire/employes/', 'POST', data);
        showToast('Compte créé avec succès !', 'success');
        closeAddUser();
        await loadEmployes();
    } catch(err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
        btn.disabled=false;
        btn.innerHTML='<i class="fa-solid fa-user-plus mr-2"></i>Créer le compte';
    }
}

// ─── COMMANDES DU JOUR ───────────────────────────────────────────────────────
async function loadCommandes(dateStr=null) {
    const url = dateStr ? `/gestionnaire/commandes/?date=${dateStr}` : '/gestionnaire/commandes/';
    try {
        const r = await req(url);
        const cmds = r.data||[];
        document.getElementById('cmdDate').textContent = r.date||'';
        renderCommandes(cmds);
    } catch(e){ showToast(e.message,'error'); }
}

function renderCommandes(cmds) {
    const el = document.getElementById('cmdList');
    if(!el) return;
    if(cmds.length===0){
        el.innerHTML=`<tr><td colspan="5" class="p-8 text-center text-textMuted"><i class="fa-solid fa-inbox text-3xl opacity-20 block mb-2"></i>Aucune commande pour cette date.</td></tr>`;
        return;
    }
    const sc={'en_attente':'bg-amber-100 text-amber-700','prepare':'bg-blue-100 text-blue-600','consomme':'bg-green-100 text-green-600','annule':'bg-red-100 text-red-500'};
    const sl={'en_attente':'En attente','prepare':'Prêt ✓','consomme':'Servi','annule':'Annulé'};
    el.innerHTML = cmds.map(c=>{
        const emp = c.employe_detail||{};
        const m = c.menu_jour_detail||{};
        const p = m.plat_detail||{};
        const d = new Date(c.date_reservation).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
        return `<tr class="border-b border-gray-50 last:border-0 hover:bg-gray-50/50 transition">
            <td class="p-4">
                <div class="flex items-center">
                    <div class="w-8 h-8 rounded-full bg-brandLight text-brand flex items-center justify-center font-bold text-xs mr-3">${(emp.prenom||'?')[0]}</div>
                    <div><p class="font-bold text-sm">${emp.prenom||''} ${emp.nom||''}</p><p class="text-[10px] text-textMuted">${emp.poste||''}</p></div>
                </div>
            </td>
            <td class="p-4">
                <p class="font-bold text-sm">${p.libelle||'Plat'}</p>
                <p class="text-[10px] text-textMuted">${c.type_service||'sur place'}</p>
            </td>
            <td class="p-4 font-bold text-sm">${parseFloat(m.prix||0).toLocaleString('fr-FR')} CFA</td>
            <td class="p-4 text-xs text-textMuted">${d}</td>
            <td class="p-4"><span class="px-2 py-1 ${sc[c.statut]||'bg-gray-100'} rounded-full text-[10px] font-bold">${sl[c.statut]||c.statut}</span></td>
        </tr>`;
    }).join('');
    // Stats rapides
    const total = cmds.length;
    const attente = cmds.filter(c=>c.statut==='en_attente').length;
    const prets = cmds.filter(c=>c.statut==='prepare').length;
    const consommes = cmds.filter(c=>c.statut==='consomme').length;
    const revenus = cmds.filter(c=>c.statut!=='annule').reduce((s,c)=>s+parseFloat(c.menu_jour_detail?.prix||0),0);
    document.getElementById('cmdTotal').textContent = total;
    document.getElementById('cmdAttente').textContent = attente;
    document.getElementById('cmdPrets').textContent = prets;
    document.getElementById('cmdConsommes').textContent = consommes;
    document.getElementById('cmdRevenus').textContent = revenus.toLocaleString('fr-FR')+' CFA';
}

// ─── FACTURATION ─────────────────────────────────────────────────────────────
async function loadFacturation() {
    if(employesList.length===0) await loadEmployes();
    const list = document.getElementById('factList');
    if(!list) return;
    const aFact = employesList.filter(e=>e.mode_paiement==='facture' && parseFloat(e.facture_mensuelle_salaire||0)>0);
    if(aFact.length===0){
        list.innerHTML=`<div class="py-8 text-center text-textMuted"><i class="fa-solid fa-check-circle text-3xl opacity-20 block mb-2"></i><p class="font-bold text-sm">Aucune facturation en attente.</p></div>`;
        return;
    }
    const total = aFact.reduce((s,e)=>s+parseFloat(e.facture_mensuelle_salaire||0),0);
    list.innerHTML=`<div class="flex justify-between items-center p-5 bg-brandLight rounded-2xl mb-4">
        <div><p class="text-xs font-bold text-brand uppercase tracking-wider">Total à recouvrer</p><p class="text-2xl font-extrabold">${total.toLocaleString('fr-FR')} CFA</p></div>
        <i class="fa-solid fa-file-invoice-dollar text-brand text-3xl opacity-40"></i>
    </div>
    ${aFact.map(e=>`<div class="flex justify-between items-center py-3 border-b border-gray-50 last:border-0">
        <div class="flex items-center">
            <div class="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs mr-3">${(e.prenom||'X')[0]}</div>
            <div><p class="font-bold text-sm">${e.prenom} ${e.nom}</p><p class="text-[10px] text-textMuted">${e.poste||''}</p></div>
        </div>
        <p class="font-extrabold text-brand">${parseFloat(e.facture_mensuelle_salaire).toLocaleString('fr-FR')} CFA</p>
    </div>`).join('')}`;
}

function downloadCSV() {
    const token=localStorage.getItem('token');
    fetch(API_URL+'/dashboard/gestionnaire/export/',{headers:{'Authorization':`Bearer ${token}`}})
    .then(r=>r.blob()).then(blob=>{
        const url=URL.createObjectURL(blob),a=document.createElement('a');
        a.href=url;a.download='facturation_cantine.csv';document.body.appendChild(a);a.click();a.remove();
        showToast('Export CSV téléchargé !','success');
    }).catch(e=>showToast(e.message,'error'));
}

// ─── AVIS ET NOTES ────────────────────────────────────────────────────────────
let evaluations = [];

function getImageUrl(url) {
    if(!url) return 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80';
    if(url.startsWith('http://') || url.startsWith('https://')) return url;
    if(url.startsWith('/media/')) return 'http://127.0.0.1:8000' + url;
    return 'http://127.0.0.1:8000/media/' + url;
}

async function loadEvaluations() {
    try {
        const res = await req('/cuisinier/evaluations/');
        evaluations = res.data || [];
        renderEvaluations();
    } catch(e) {
        console.error("Erreur chargement avis:", e);
    }
}

function renderEvaluations() {
    const container = document.getElementById('avisListGrid');
    if(!container) return;
    
    // Retirer la grille principale pour afficher des sections par plat
    container.className = "space-y-10";

    if(evaluations.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-textMuted bg-white rounded-3xl border border-gray-100">Aucun avis reçu pour le moment.</div>`;
        return;
    }

    // Grouper par plat
    const groups = {};
    evaluations.forEach(ev => {
        const platId = ev.plat || (ev.plat_detail ? ev.plat_detail.id : 0);
        if(!groups[platId]) {
            groups[platId] = {
                plat: ev.plat_detail || {libelle: 'Plat inconnu'},
                avis: [],
                totalNotes: 0
            };
        }
        groups[platId].avis.push(ev);
        groups[platId].totalNotes += ev.note;
    });

    container.innerHTML = Object.values(groups).map(g => {
        const avg = (g.totalNotes / g.avis.length).toFixed(1);
        const avgRounded = Math.round(avg);
        const img = getImageUrl(g.plat.image);
        
        // Calcul des barres de progression des notes (5 étoiles à 1 étoile)
        const ratingsBreakdown = [5, 4, 3, 2, 1].map(star => {
            const count = g.avis.filter(a => a.note === star).length;
            const pct = g.avis.length ? (count / g.avis.length) * 100 : 0;
            return `
            <div class="flex items-center gap-2 text-xs text-textMuted font-bold">
                <span class="w-2">${star}</span>
                <i class="fa-solid fa-star text-brand text-[10px]"></i>
                <div class="flex-1 h-2 bg-surface border border-gray-100 rounded-full overflow-hidden">
                    <div class="h-full bg-brand rounded-full" style="width: ${pct}%"></div>
                </div>
                <span class="w-4 text-right">${count}</span>
            </div>`;
        }).join('');

        const cardsHtml = g.avis.map(ev => {
            const stars = Array.from({length: 5}, (_, i) => 
                i < ev.note ? '<i class="fa-solid fa-star text-brand text-[11px]"></i>' : '<i class="fa-solid fa-star text-gray-200 text-[11px]"></i>'
            ).join('');
            
            const isDefaultComment = !ev.commentaire || ev.commentaire.trim() === '';
            const commentText = isDefaultComment ? '<span class="italic text-textMuted/70">Aucun commentaire laissé</span>' : ev.commentaire;

            return `
            <div class="border-b border-gray-100 pb-5 mb-5 last:border-0 last:pb-0 last:mb-0">
                <div class="flex items-center gap-1 mb-2">${stars}</div>
                <p class="text-sm font-bold text-textDark mb-3 leading-relaxed">${commentText}</p>
                <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center text-[11px] text-textMuted font-bold gap-2">
                    <div class="flex items-center gap-2">
                        <span>Par <span class="text-textDark">${ev.employe_detail?.prenom} ${ev.employe_detail?.nom}</span></span>
                        <span class="bg-brandLight text-brand px-2 py-0.5 rounded-lg flex items-center gap-1"><i class="fa-solid fa-circle-check"></i> Repas consommé</span>
                    </div>
                    <span>${new Date(ev.date_evaluation).toLocaleDateString()}</span>
                </div>
            </div>`;
        }).join('');

        return `
        <div class="bg-white rounded-[2rem] shadow-sm border border-gray-100 overflow-hidden mb-8">
            <!-- En-tête du plat -->
            <div class="p-5 border-b border-gray-100 flex items-center gap-4 bg-surface">
                <img src="${img}" class="w-16 h-16 rounded-2xl object-cover shadow-sm">
                <h3 class="font-extrabold text-xl text-textDark">${g.plat.libelle || 'Plat inconnu'}</h3>
            </div>
            
            <!-- Section Jumia Style -->
            <div class="flex flex-col lg:flex-row">
                <!-- Résumé des notes (Left side) -->
                <div class="p-6 lg:w-1/3 lg:border-r border-gray-100 flex flex-col items-center justify-center bg-white">
                    <h4 class="text-xs font-bold text-textMuted mb-2 uppercase tracking-widest">Avis sur ce plat</h4>
                    <div class="text-5xl font-extrabold text-brand mb-2 flex items-baseline gap-1">
                        ${avg} <span class="text-2xl text-textMuted font-normal">/ 5</span>
                    </div>
                    <div class="flex gap-1 text-brand text-lg mb-2">
                        ${Array.from({length:5}, (_,i) => i < avgRounded ? '<i class="fa-solid fa-star"></i>' : '<i class="fa-regular fa-star text-gray-200"></i>').join('')}
                    </div>
                    <p class="text-xs font-bold text-textMuted mb-6">${g.avis.length} avis au total</p>
                    
                    <!-- Barres de progression -->
                    <div class="w-full space-y-2 px-4">
                        ${ratingsBreakdown}
                    </div>
                </div>
                
                <!-- Liste des commentaires (Right side) -->
                <div class="flex-1 p-6 flex flex-col max-h-[400px] overflow-y-auto no-scrollbar bg-white">
                    ${cardsHtml}
                </div>
            </div>
        </div>
        `;
    }).join('');
}

// ─── NOTIFICATIONS ────────────────────────────────────────────────────────────
let notifs = [];
async function loadNotifications() {
    try {
        const r=await req('/notifications/');
        notifs=r.data||[];
        const unread=notifs.filter(n=>!n.is_read).length;
        const badge=document.getElementById('notifBadge');
        badge.textContent=unread;badge.classList.toggle('hidden',unread===0);
        renderNotifList();
    } catch(e){}
}
function renderNotifList() {
    const el=document.getElementById('notifList');if(!el) return;
    if(notifs.length===0){el.innerHTML=`<div class="py-10 text-center text-textMuted"><i class="fa-solid fa-bell-slash text-3xl opacity-20 block mb-2"></i><p class="font-bold text-sm">Aucune notification.</p></div>`;return;}
    el.innerHTML=notifs.map(n=>`<div class="p-4 border-b border-gray-50 last:border-0 ${!n.is_read?'bg-brandLight/30':''}">
        <div class="flex justify-between items-start">
            <div class="flex-1 min-w-0 mr-3">
                <p class="font-bold text-sm ${!n.is_read?'text-brand':'text-textDark'}">${n.titre}</p>
                <p class="text-xs text-textMuted mt-1">${n.message}</p>
                <p class="text-[10px] text-gray-300 mt-1">${new Date(n.created_at).toLocaleDateString('fr-FR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}</p>
            </div>
            ${!n.is_read?`<button onclick="markRead(${n.id})" class="w-6 h-6 bg-brand text-white rounded-full text-[10px] flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-check"></i></button>`:''}
        </div>
    </div>`).join('');
}
async function markRead(id){try{await req(`/notifications/${id}/read/`,'POST');await loadNotifications();}catch(e){}}

async function broadcastNotif() {
    const titre=document.getElementById('broadTitre').value.trim();
    const message=document.getElementById('broadMsg').value.trim();
    const cible=document.getElementById('broadCible').value;
    if(!titre||!message){showToast('Remplissez titre et message.','error');return;}
    const btn=document.getElementById('broadBtn');
    btn.disabled=true;btn.innerHTML='<i class="fa-solid fa-spinner fa-spin mr-2"></i>Envoi...';
    try{
        const r=await req('/notifications/broadcast/','POST',{titre,message,cible});
        showToast(r.message,'success');
        document.getElementById('broadTitre').value='';document.getElementById('broadMsg').value='';
    }catch(e){showToast(e.message,'error');}
    finally{btn.disabled=false;btn.innerHTML='<i class="fa-solid fa-paper-plane mr-2"></i>Envoyer la notification';}
}

function showToast(msg,type='success'){
    const c={success:'bg-success',error:'bg-red-500',info:'bg-blue-500'};
    const t=document.createElement('div');
    t.className=`fixed top-6 left-1/2 -translate-x-1/2 ${c[type]||'bg-gray-800'} text-white px-6 py-3 rounded-2xl shadow-xl text-sm font-bold z-[9999]`;
    t.textContent=msg;document.body.appendChild(t);
    setTimeout(()=>{t.style.opacity='0';t.style.transition='opacity .3s';setTimeout(()=>t.remove(),300);},3500);
}

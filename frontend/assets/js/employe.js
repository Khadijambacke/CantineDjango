// employe.js - Dashboard Employé complet
const API_URL = 'http://127.0.0.1:8000/api';
let panier = [];
let currentUser = null;
let menusAujourdhui = [];
const FRAIS_LIVRAISON = 500; // CFA

async function req(endpoint, method='GET', data=null) {
    const h = {'Content-Type':'application/json'};
    const tk = localStorage.getItem('token');
    if(tk) h['Authorization'] = `Bearer ${tk}`;
    const cfg = {method, headers:h};
    if(data) cfg.body = JSON.stringify(data);
    const r = await fetch(API_URL+endpoint, cfg);
    const j = await r.json();
    if(!r.ok) throw new Error(j.message||j.error||j.detail||'Erreur serveur');
    return j;
}

function logout(){localStorage.clear();window.location.href='index.html';}
function getUser(){const u=localStorage.getItem('user');return u?JSON.parse(u):null;}

const TABS = ['dashboard','commander','historique','notifications'];
function showTab(tab) {
    TABS.forEach(t=>{
        const el=document.getElementById('tab-'+t);
        const btn=document.getElementById('nav-'+t);
        if(el) el.classList.toggle('hidden',t!==tab);
        if(btn){
            btn.classList.toggle('bg-brandLight',t===tab);
            btn.classList.toggle('text-brand',t===tab);
            btn.classList.toggle('text-textMuted',t!==tab);
        }
    });
}

document.addEventListener('DOMContentLoaded', async()=>{
    if(!localStorage.getItem('token')){window.location.href='index.html';return;}
    currentUser=getUser();
    if(currentUser){
        const init=(currentUser.prenom||'E')[0].toUpperCase();
        document.querySelectorAll('.u-avatar').forEach(el=>el.textContent=init);
        document.querySelectorAll('.u-name').forEach(el=>el.textContent=currentUser.prenom+' '+currentUser.nom);
        document.getElementById('greetName').textContent=currentUser.prenom+' !';
    }
    showTab('dashboard');
    await Promise.all([loadProfil(),loadMenus(),loadHistorique(),loadNotifications()]);
    renderDashboard();
});

// ─── PROFIL / SOLDE ─────────────────────────────────────────────────────────
async function loadProfil() {
    try {
        const r=await req('/me/');
        const u=r.data||r.user||r;
        currentUser=u;
        localStorage.setItem('user',JSON.stringify(u));
        const solde=parseFloat(u.solde||0);
        const dep=parseFloat(u.depenses_mensuelles||0);
        document.getElementById('kpiSolde').textContent=solde.toLocaleString('fr-FR');
        document.getElementById('kpiDepenses').textContent=dep.toLocaleString('fr-FR');
        document.getElementById('sidebarSolde').textContent=solde.toLocaleString('fr-FR')+' CFA';
    } catch(e){}
}

// ─── RECHARGE SOLDE ──────────────────────────────────────────────────────────
function openRecharge(){
    document.getElementById('modalRecharge').classList.remove('hidden');
    document.getElementById('rechargeInput').value='';
    document.getElementById('rechargeError').classList.add('hidden');
}
function closeRecharge(){document.getElementById('modalRecharge').classList.add('hidden');}

async function submitRecharge(e){
    e.preventDefault();
    const montant=parseFloat(document.getElementById('rechargeInput').value);
    const btn=document.getElementById('rechargeBtn');
    const err=document.getElementById('rechargeError');
    if(!montant||montant<=0){err.textContent='Entrez un montant valide.';err.classList.remove('hidden');return;}
    btn.disabled=true;btn.innerHTML='<i class="fa-solid fa-spinner fa-spin mr-2"></i>En cours...';
    err.classList.add('hidden');
    try {
        const r=await req('/solde/recharger/','POST',{montant});
        showToast(r.message,'success');
        closeRecharge();
        await loadProfil();
    } catch(ex){
        err.textContent=ex.message;
        err.classList.remove('hidden');
    } finally{
        btn.disabled=false;
        btn.innerHTML='<i class="fa-solid fa-bolt mr-2"></i>Recharger maintenant';
    }
}

// ─── MENUS DU JOUR ───────────────────────────────────────────────────────────
async function loadMenus() {
    try {
        const r=await req('/menus/');
        const today=new Date().toISOString().split('T')[0];
        menusAujourdhui=(r.data||[]).filter(m=>m.date_menu===today);
        document.getElementById('kpiMenus').textContent=menusAujourdhui.length;
        renderMenus();
    } catch(e){
        const g=document.getElementById('menuGrid');
        if(g) g.innerHTML=`<p class="col-span-3 text-red-400 font-bold text-sm p-4">${e.message}</p>`;
    }
}

function renderMenus(){
    const g=document.getElementById('menuGrid');
    if(!g) return;
    document.getElementById('menuLoading').classList.add('hidden');
    g.classList.remove('hidden');
    if(menusAujourdhui.length===0){
        g.innerHTML=`<div class="col-span-3 py-12 text-center text-textMuted"><i class="fa-solid fa-calendar-xmark text-4xl opacity-20 block mb-3"></i><p class="font-bold">Aucun menu planifié pour aujourd'hui.</p></div>`;
        return;
    }
    const tl={'entree':'Entrée','plat':'Plat','dessert':'Dessert','boisson':'Boisson'};
    const tc={'entree':'bg-amber-100 text-amber-700','plat':'bg-brandLight text-brand','dessert':'bg-pink-100 text-pink-600','boisson':'bg-blue-100 text-blue-700'};
    g.innerHTML=menusAujourdhui.map(m=>{
        const p=m.plat_detail||{};
        const item=panier.find(x=>x.id===m.id);
        const qte=item?item.qty:0;
        const epuise=m.statut==='epuise';
        const img=p.image||'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80';
        return `<div class="bg-white rounded-3xl border ${qte>0?'border-brand shadow-md':'border-gray-100'} overflow-hidden flex flex-col transition-all ${epuise?'opacity-60':''}">
            <div class="relative h-40 overflow-hidden cursor-pointer" onclick="openMealDetails(${m.id})">
                <img src="${img}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-500" alt="${p.libelle}">
                ${epuise?`<div class="absolute inset-0 bg-black/40 flex items-center justify-center"><span class="bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">Épuisé</span></div>`:''}
                <span class="absolute top-3 left-3 ${tc[p.type_plat]||'bg-gray-100 text-gray-600'} text-[10px] font-bold px-2 py-1 rounded-full shadow-sm">${tl[p.type_plat]||'Plat'}</span>
                ${qte>0?`<span class="absolute top-3 right-3 w-6 h-6 bg-brand text-white text-xs font-extrabold rounded-full flex items-center justify-center shadow">${qte}</span>`:''}
            </div>
            <div class="p-4 flex-1 flex flex-col">
                <h4 class="font-bold text-textDark mb-1 text-sm cursor-pointer hover:text-brand transition" onclick="openMealDetails(${m.id})">${p.libelle||'Plat'}</h4>
                <p class="text-xs text-textMuted line-clamp-2 flex-1 mb-3 cursor-pointer" onclick="openMealDetails(${m.id})">${p.description||''}</p>
                <div class="flex items-center justify-between mt-auto">
                    <span class="font-extrabold">${parseFloat(m.prix)} <span class="text-xs text-brand">CFA</span></span>
                    ${!epuise?(qte===0
                        ?`<button onclick="addToCart(${m.id})" class="h-9 px-3 rounded-xl bg-brandLight text-brand hover:bg-brand hover:text-white transition flex items-center justify-center text-xs font-bold shadow-sm"><i class="fa-solid fa-plus mr-1"></i>Ajouter</button>`
                        :`<div class="flex items-center space-x-2 bg-gray-50 rounded-xl p-1 border border-gray-100 shadow-sm">
                            <button onclick="removeFromCart(${m.id})" class="w-7 h-7 rounded-lg bg-white hover:bg-red-50 hover:text-red-500 transition flex items-center justify-center shadow-sm"><i class="fa-solid fa-minus text-xs"></i></button>
                            <span class="font-extrabold text-sm w-4 text-center">${qte}</span>
                            <button onclick="addToCart(${m.id})" class="w-7 h-7 rounded-lg bg-brandLight text-brand hover:bg-brand hover:text-white transition flex items-center justify-center shadow-sm"><i class="fa-solid fa-plus text-xs"></i></button>
                          </div>`)
                        :`<span class="text-xs text-textMuted font-bold bg-gray-50 px-3 py-2 rounded-xl">Indisponible</span>`}
                </div>
            </div>
        </div>`;
    }).join('');
}

function addToCart(id){
    const m=menusAujourdhui.find(x=>x.id===id);
    if(!m) return;
    const i=panier.findIndex(x=>x.id===id);
    if(i>=0) panier[i].qty++;
    else panier.push({id,menu:m,qty:1});
    renderMenus(); updateCartUI();
}
function removeFromCart(id){
    const i=panier.findIndex(x=>x.id===id);
    if(i>=0){panier[i].qty--;if(panier[i].qty<=0) panier.splice(i,1);}
    renderMenus(); updateCartUI();
}
function updateCartUI(){
    const total=panier.reduce((s,x)=>s+parseFloat(x.menu.prix)*x.qty,0);
    const count=panier.reduce((s,x)=>s+x.qty,0);
    const badge=document.getElementById('cartBadge');
    if(badge){badge.textContent=count;badge.classList.toggle('hidden',count===0);}
    document.getElementById('cartEmpty').classList.toggle('hidden',panier.length>0);
    document.getElementById('cartFull').classList.toggle('hidden',panier.length===0);
    if(panier.length>0){
        document.getElementById('cartItems').innerHTML=panier.map(x=>`
            <div class="flex justify-between text-xs py-1.5 border-b border-gray-50 last:border-0">
                <span class="font-bold truncate mr-2">${x.menu.plat_detail?.libelle||'Plat'} ×${x.qty}</span>
                <span class="font-extrabold flex-shrink-0">${(parseFloat(x.menu.prix)*x.qty).toFixed(0)} CFA</span>
            </div>`).join('');
        document.getElementById('cartTotal').textContent=total.toFixed(0)+' CFA';
    }
}

// ─── MODAL COMMANDE (2 étapes) ───────────────────────────────────────────────
// Étape 1 : Mode de service | Étape 2 : Mode de paiement
let selectedService = 'sur_place';
let lieuLivraison = '';

function openPayment(){
    if(panier.length===0){showToast('Votre panier est vide !','error');return;}
    selectedService='sur_place';
    lieuLivraison='';
    const optInput = document.getElementById('optionsInput');
    if(optInput) optInput.value = '';
    showStep(1);
    updateOrderSummary();
    document.getElementById('modalOrder').classList.remove('hidden');
}
function closePayment(){document.getElementById('modalOrder').classList.add('hidden');}

function showStep(n){
    document.getElementById('step1').classList.toggle('hidden',n!==1);
    document.getElementById('step2').classList.toggle('hidden',n!==2);
    document.getElementById('stepIndicator').textContent=`Étape ${n}/2`;
}

function selectService(type){
    selectedService=type;
    document.querySelectorAll('.service-btn').forEach(b=>{
        b.classList.remove('border-brand','bg-brandLight/50');
        b.classList.add('border-gray-200');
    });
    document.getElementById('svc-'+type).classList.add('border-brand','bg-brandLight/50');
    document.getElementById('svc-'+type).classList.remove('border-gray-200');
    // Afficher champ lieu si livraison
    document.getElementById('lieuRow').classList.toggle('hidden', type!=='livraison');
    updateOrderSummary();
}

function updateOrderSummary(){
    const base=panier.reduce((s,x)=>s+parseFloat(x.menu.prix)*x.qty,0);
    const frais=selectedService==='livraison'?FRAIS_LIVRAISON:0;
    const total=base+frais;
    const el=document.getElementById('summaryTotal');
    if(el){
        el.innerHTML=`
            <div class="flex justify-between text-xs text-textMuted mb-1"><span>Sous-total repas</span><span>${base.toFixed(0)} CFA</span></div>
            ${frais>0?`<div class="flex justify-between text-xs text-textMuted mb-1"><span>Frais de livraison</span><span class="text-brand font-bold">+${frais} CFA</span></div>`:''}
            <div class="flex justify-between font-extrabold text-base border-t border-gray-100 pt-2 mt-1"><span>Total</span><span>${total.toFixed(0)} CFA</span></div>`;
    }
    // Step 2 : mettre à jour le total aussi
    const t2=document.getElementById('payTotal2');
    if(t2) t2.textContent=total.toFixed(0)+' CFA';
}

function goToStep2(){
    // Récupérer le lieu si livraison
    lieuLivraison=document.getElementById('lieuInput')?.value?.trim()||'';
    if(selectedService==='livraison'&&!lieuLivraison){
        showToast('Précisez votre lieu de livraison.','error');return;
    }
    // Mettre à jour le solde dispo
    const solde=parseFloat(currentUser?.solde||0);
    const frais=selectedService==='livraison'?FRAIS_LIVRAISON:0;
    const total=panier.reduce((s,x)=>s+parseFloat(x.menu.prix)*x.qty,0)+frais;
    document.getElementById('soldeDispo2').textContent=solde.toLocaleString('fr-FR')+' CFA';
    const btnSolde=document.getElementById('btnPaySolde');
    const insufficient=solde<total;
    btnSolde.disabled=insufficient;
    btnSolde.classList.toggle('opacity-40',insufficient);
    btnSolde.classList.toggle('cursor-not-allowed',insufficient);
    if(insufficient){
        document.getElementById('soldeInsuffMsg').classList.remove('hidden');
    } else {
        document.getElementById('soldeInsuffMsg').classList.add('hidden');
    }
    updateOrderSummary();
    showStep(2);
}

async function confirmOrder(mode){
    const btn=document.getElementById(mode==='solde'?'btnPaySolde':'btnPayFacture');
    btn.disabled=true;btn.innerHTML='<i class="fa-solid fa-spinner fa-spin mr-2"></i>Traitement...';
    try {
        const opts = document.getElementById('optionsInput')?.value?.trim() || '';
        for(const item of panier){
            for(let i=0;i<item.qty;i++){
                let finalOpts = opts;
                if(selectedService==='livraison') finalOpts = `Livraison: ${lieuLivraison}` + (opts? ` | ${opts}` : '');
                
                await req('/reservations/','POST',{
                    menu_jour:item.id,
                    type_service:selectedService,
                    lieu_livraison:lieuLivraison||'',
                    options_personnalisation: finalOpts
                });
            }
        }
        closePayment();
        panier=[];
        showToast('🎉 Commande confirmée ! Bon appétit.','success');
        updateCartUI();
        await Promise.all([loadProfil(),loadHistorique()]);
        renderDashboard();
        await loadMenus();
    } catch(e){
        showToast(e.message,'error');
        btn.disabled=false;
        btn.innerHTML=mode==='solde'
            ?'<i class="fa-solid fa-wallet mr-2"></i>Payer avec mon Solde'
            :'<i class="fa-solid fa-building-columns mr-2"></i>Facturer sur Salaire';
    }
}

// ─── HISTORIQUE ──────────────────────────────────────────────────────────────
let reservations=[];
async function loadHistorique(){
    try{
        const r=await req('/reservations/');
        reservations=r.data||[];
        document.getElementById('kpiReservations').textContent=reservations.filter(x=>x.statut!=='annule').length;
        renderHistorique();
    }catch(e){}
}
function renderHistorique(){
    const list=document.getElementById('histList');if(!list) return;
    const sc={'en_attente':'bg-amber-100 text-amber-700','prepare':'bg-blue-100 text-blue-600','consomme':'bg-green-100 text-green-600','annule':'bg-red-100 text-red-500'};
    const sl={'en_attente':'En attente','prepare':'En préparation','consomme':'Servi ✓','annule':'Annulé'};
    const ti={'sur_place':'Sur place','emporter':'À emporter','livraison':'Livraison'};
    if(reservations.length===0){
        list.innerHTML=`<div class="py-10 text-center text-textMuted"><i class="fa-solid fa-inbox text-3xl opacity-20 block mb-2"></i><p class="font-bold text-sm">Aucune réservation.</p></div>`;
        return;
    }
    list.innerHTML=reservations.slice(0,20).map(r=>{
        const m=r.menu_jour_detail||{};const p=m.plat_detail||{};
        const d=new Date(r.date_reservation).toLocaleDateString('fr-FR',{day:'2-digit',month:'short',year:'numeric'});
        const canCancel=r.statut==='en_attente';
        const svcLabel=ti[r.type_service]||r.type_service||'';
        const svcIcon={'sur_place':'fa-chair','emporter':'fa-bag-shopping','livraison':'fa-motorcycle'}[r.type_service]||'fa-utensils';
        return `<div class="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
            <div class="flex items-center min-w-0">
                <div class="w-10 h-10 bg-brandLight rounded-xl flex items-center justify-center flex-shrink-0 mr-3">
                    <i class="fa-solid ${svcIcon} text-brand text-sm"></i>
                </div>
                <div class="min-w-0 flex-1">
                    <p class="font-bold text-sm truncate">${p.libelle||'Plat'}</p>
                    <p class="text-[10px] text-textMuted line-clamp-1">${d} · ${parseFloat(m.prix||0)} CFA · <span class="font-bold">${svcLabel}</span>${r.lieu_livraison?` → ${r.lieu_livraison}`:''} ${r.options_personnalisation? ` | Opt: ${r.options_personnalisation}`:''}</p>
                </div>
            </div>
            <div class="flex items-center space-x-2 flex-shrink-0 ml-2">
                <span class="px-2 py-1 ${sc[r.statut]||'bg-gray-100'} rounded-full text-[10px] font-bold whitespace-nowrap hidden sm:inline-block">${sl[r.statut]||r.statut}</span>
                ${canCancel?`
                    <button onclick="modifyRes(${r.id})" class="px-3 h-8 rounded-xl bg-surface border border-gray-200 text-textMuted hover:bg-gray-50 hover:text-textDark hover:border-gray-300 transition flex items-center justify-center text-[10px] font-bold shadow-sm" title="Modifier la commande"><i class="fa-solid fa-pen mr-1"></i>Modifier</button>
                    <button onclick="askCancelRes(${r.id})" class="px-3 h-8 rounded-xl bg-red-50 text-red-500 hover:bg-red-500 hover:text-white transition flex items-center justify-center text-[10px] font-bold shadow-sm" title="Annuler cette réservation"><i class="fa-solid fa-xmark mr-1"></i>Annuler</button>
                `:`<span class="px-2 py-1 ${sc[r.statut]||'bg-gray-100'} rounded-full text-[10px] font-bold whitespace-nowrap sm:hidden">${sl[r.statut]||r.statut}</span>`}
            </div>
        </div>`;
    }).join('');
}
let currentCancelId = null;
function askCancelRes(id){
    currentCancelId = id;
    document.getElementById('modalCancel').classList.remove('hidden');
    document.getElementById('btnConfirmCancel').onclick = () => doCancel(id);
}
function closeCancel() { document.getElementById('modalCancel').classList.add('hidden'); currentCancelId=null; }

async function doCancel(id){
    const btn = document.getElementById('btnConfirmCancel');
    const oldText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>...';
    btn.disabled = true;
    try{
        await req(`/reservations/${id}/`,'DELETE');
        showToast('Réservation annulée avec succès.','info');
        closeCancel();
        await Promise.all([loadHistorique(),loadProfil()]);
        renderDashboard();
    }catch(e){
        showToast(e.message,'error');
    }finally{
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function modifyRes(id){
    const res = reservations.find(r => r.id === id);
    if(!res) return;
    
    // Annule la commande courante, et remet l'article dans le panier pour que l'utilisateur modifie ses options
    try {
        await req(`/reservations/${id}/`,'DELETE');
        
        // Ajouter au panier
        const m = res.menu_jour_detail;
        if(m) {
            const i=panier.findIndex(x=>x.id===m.id);
            if(i>=0) panier[i].qty++;
            else panier.push({id:m.id, menu:m, qty:1});
            updateCartUI();
        }
        
        showToast('Commande prête à être modifiée. Veuillez valider votre panier.','info');
        await Promise.all([loadHistorique(),loadProfil()]);
        renderDashboard();
        
        // Ouvrir le checkout
        if(res.options_personnalisation) {
            const optInput = document.getElementById('optionsInput');
            if(optInput) {
                // Remove the "Livraison: xxx | " part from old options if it exists
                let cleanedOpts = res.options_personnalisation;
                if(cleanedOpts.startsWith('Livraison:')) {
                    const parts = cleanedOpts.split('|');
                    if(parts.length > 1) {
                        cleanedOpts = parts.slice(1).join('|').trim();
                    } else {
                        cleanedOpts = '';
                    }
                }
                optInput.value = cleanedOpts;
            }
        }
        showTab('commander');
        openPayment();

    } catch(e) {
        showToast("Erreur lors de la préparation de la modification: " + e.message, 'error');
    }
}

// ─── MODAL DÉTAILS REPAS ──────────────────────────────────────────────────────
function openMealDetails(menuId){
    const m = menusAujourdhui.find(x => x.id === menuId);
    if(!m) return;
    const p = m.plat_detail || {};
    
    document.getElementById('mealImage').src = p.image || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&q=80';
    document.getElementById('mealTitle').textContent = p.libelle || 'Plat';
    document.getElementById('mealDesc').textContent = p.description || 'Aucune description fournie.';
    document.getElementById('mealPrice').textContent = parseFloat(m.prix) + ' CFA';
    
    const tl={'entree':'Entrée','plat':'Plat Principal','dessert':'Dessert','boisson':'Boisson'};
    document.getElementById('mealType').textContent = tl[p.type_plat] || 'Plat';
    
    const btn = document.getElementById('btnMealAddToCart');
    if(m.statut === 'epuise') {
        btn.disabled = true;
        btn.className = 'w-full h-12 bg-gray-200 text-textMuted rounded-2xl font-bold flex items-center justify-center cursor-not-allowed';
        btn.innerHTML = 'Épuisé';
        btn.onclick = null;
    } else {
        btn.disabled = false;
        btn.className = 'w-full h-12 bg-brand text-white rounded-2xl font-bold hover:-translate-y-0.5 transition shadow-lg shadow-brand/30 flex items-center justify-center';
        btn.innerHTML = '<i class="fa-solid fa-cart-plus mr-2"></i>Ajouter au panier';
        btn.onclick = () => {
            addToCart(m.id);
            closeMealDetails();
            showToast('Plat ajouté au panier !', 'success');
        };
    }
    
    document.getElementById('modalMealDetails').classList.remove('hidden');
}

function closeMealDetails(){
    document.getElementById('modalMealDetails').classList.add('hidden');
}

// ─── NOTIFICATIONS ────────────────────────────────────────────────────────────
let notifs=[];
async function loadNotifications(){
    try{
        const r=await req('/notifications/');
        notifs=r.data||[];
        const unread=notifs.filter(n=>!n.is_read).length;
        document.getElementById('kpiNotifs').textContent=unread;
        document.getElementById('notifBadge').textContent=unread;
        document.getElementById('notifBadge').classList.toggle('hidden',unread===0);
        renderNotifications();
    }catch(e){}
}
function renderNotifications(){
    const el=document.getElementById('notifList');if(!el) return;
    if(notifs.length===0){el.innerHTML=`<div class="py-10 text-center text-textMuted"><i class="fa-solid fa-bell-slash text-3xl opacity-20 block mb-2"></i><p class="font-bold text-sm">Aucune notification.</p></div>`;return;}
    el.innerHTML=notifs.map(n=>`<div class="p-4 border-b border-gray-50 last:border-0 ${!n.is_read?'bg-brandLight/40':''}">
        <div class="flex justify-between items-start">
            <div class="flex-1 min-w-0 mr-3">
                <div class="flex items-center mb-1">
                    <i class="fa-solid fa-bell text-brand text-xs mr-2 flex-shrink-0 ${!n.is_read?'':'opacity-30'}"></i>
                    <p class="font-bold text-sm ${!n.is_read?'text-brand':'text-textDark'}">${n.titre}</p>
                </div>
                <p class="text-xs text-textMuted ml-4">${n.message}</p>
                <p class="text-[10px] text-gray-300 ml-4 mt-1">${new Date(n.created_at).toLocaleDateString('fr-FR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}</p>
            </div>
            ${!n.is_read?`<button onclick="markRead(${n.id})" class="flex-shrink-0 w-6 h-6 bg-brand text-white rounded-full text-[10px] flex items-center justify-center hover:bg-orange-600 transition" title="Marquer comme lue"><i class="fa-solid fa-check"></i></button>`:'<i class="fa-solid fa-check-double text-gray-200 text-xs flex-shrink-0 mt-1"></i>'}
        </div>
    </div>`).join('');
}
async function markRead(id){try{await req(`/notifications/${id}/read/`,'POST');await loadNotifications();}catch(e){}}

// ─── DASHBOARD HOME ───────────────────────────────────────────────────────────
function renderDashboard(){
    const el=document.getElementById('recentRes');if(!el) return;
    const recent=reservations.slice(0,4);
    if(recent.length===0){el.innerHTML=`<p class="text-xs text-textMuted text-center py-4">Aucune réservation récente.</p>`;return;}
    const sl={'en_attente':'En attente','prepare':'En prép.','consomme':'Servi','annule':'Annulé'};
    const sc={'en_attente':'text-amber-600','prepare':'text-blue-600','consomme':'text-success','annule':'text-red-400'};
    const si={'sur_place':'fa-chair','emporter':'fa-bag-shopping','livraison':'fa-motorcycle'};
    el.innerHTML=recent.map(r=>{
        const p=(r.menu_jour_detail?.plat_detail)||{};
        const d=new Date(r.date_reservation).toLocaleDateString('fr-FR',{day:'2-digit',month:'short'});
        return `<div class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
            <div class="flex items-center min-w-0">
                <div class="w-8 h-8 rounded-lg bg-brandLight flex items-center justify-center mr-2 flex-shrink-0">
                    <i class="fa-solid ${si[r.type_service]||'fa-utensils'} text-brand text-xs"></i>
                </div>
                <div class="min-w-0"><p class="font-bold text-xs truncate">${p.libelle||'Plat'}</p><p class="text-[10px] text-textMuted">${d}</p></div>
            </div>
            <span class="text-[10px] font-bold ${sc[r.statut]||'text-gray-400'} flex-shrink-0 ml-2">${sl[r.statut]||r.statut}</span>
        </div>`;
    }).join('');
}

function showToast(msg,type='success'){
    const c={success:'bg-success',error:'bg-red-500',info:'bg-blue-500'};
    const t=document.createElement('div');
    t.className=`fixed top-6 left-1/2 -translate-x-1/2 ${c[type]||'bg-gray-800'} text-white px-6 py-3 rounded-2xl shadow-xl text-sm font-bold z-[9999]`;
    t.textContent=msg;document.body.appendChild(t);
    setTimeout(()=>{t.style.opacity='0';t.style.transition='opacity .3s';setTimeout(()=>t.remove(),300);},3500);
}

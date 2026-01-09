const API_BASE = '';
let token = localStorage.getItem('token');

async function api(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        logout();
        throw new Error('Session expired');
    }
    
    return response;
}

function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.classList.add('hidden'));
    
    if (tab === 'login') {
        document.getElementById('login-form').classList.remove('hidden');
        document.querySelector('.tab-btn:first-child').classList.add('active');
    } else {
        document.getElementById('register-form').classList.remove('hidden');
        document.querySelector('.tab-btn:last-child').classList.add('active');
    }
}

function showSection(section) {
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    
    document.getElementById(`${section}-section`).classList.remove('hidden');
    event.target.classList.add('active');
    
    loadSectionData(section);
}

function showModal(id) {
    document.getElementById(id).classList.remove('hidden');
    if (id === 'entity-modal') {
        populateCaseSelect();
    } else if (id === 'relationship-modal') {
        populateEntitySelects();
    }
}

function hideModal(id) {
    document.getElementById(id).classList.add('hidden');
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Login failed');
        }
        
        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        localStorage.setItem('username', username);
        errorEl.textContent = '';
        showDashboard();
    } catch (err) {
        errorEl.textContent = err.message;
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const errorEl = document.getElementById('register-error');
    const successEl = document.getElementById('register-success');
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Registration failed');
        }
        
        errorEl.textContent = '';
        successEl.textContent = 'Registration successful! You can now login.';
        document.getElementById('register-username').value = '';
        document.getElementById('register-password').value = '';
    } catch (err) {
        successEl.textContent = '';
        errorEl.textContent = err.message;
    }
}

function logout() {
    token = null;
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    document.getElementById('auth-section').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('user-info').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    document.getElementById('username-display').textContent = localStorage.getItem('username');
    loadCases();
}

async function loadSectionData(section) {
    switch (section) {
        case 'cases': await loadCases(); break;
        case 'entities': await loadEntities(); break;
        case 'relationships': await loadRelationships(); break;
        case 'apikeys': await loadApiKeys(); break;
    }
}

async function loadCases() {
    try {
        const response = await api('/cases/');
        const cases = await response.json();
        const list = document.getElementById('cases-list');
        
        if (cases.length === 0) {
            list.innerHTML = '<p style="color: #888;">No cases yet. Create your first case!</p>';
            return;
        }
        
        list.innerHTML = cases.map(c => `
            <div class="list-item">
                <h3>${escapeHtml(c.name)}</h3>
                <p>${escapeHtml(c.description || 'No description')}</p>
                <p class="meta">ID: ${c.id}</p>
                <div class="actions">
                    <button class="btn-delete" onclick="deleteCase(${c.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading cases:', err);
    }
}

async function loadEntities() {
    try {
        const response = await api('/entities/');
        const entities = await response.json();
        const list = document.getElementById('entities-list');
        
        if (entities.length === 0) {
            list.innerHTML = '<p style="color: #888;">No entities yet. Create your first entity!</p>';
            return;
        }
        
        const transformableKinds = ['ip', 'domain', 'url'];
        
        list.innerHTML = entities.map(e => {
            const canTransform = transformableKinds.includes((e.kind || '').toLowerCase());
            const transformBtn = canTransform 
                ? `<button class="btn-transform" onclick="runTransform(${e.id}, '${escapeHtml(e.name)}', '${escapeHtml(e.kind)}')">Run Transform</button>`
                : '';
            
            return `
                <div class="list-item" id="entity-${e.id}">
                    <h3>${escapeHtml(e.name)}</h3>
                    <p>Kind: <span class="kind-badge">${escapeHtml(e.kind || 'N/A')}</span></p>
                    <p>${escapeHtml(e.description || 'No description')}</p>
                    <p class="meta">Case ID: ${e.case_id} | Entity ID: ${e.id}</p>
                    <div class="actions">
                        ${transformBtn}
                        <button class="btn-delete" onclick="deleteEntity(${e.id})">Delete</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error('Error loading entities:', err);
    }
}

async function runTransform(entityId, entityName, entityKind) {
    const entityEl = document.getElementById(`entity-${entityId}`);
    const btn = entityEl.querySelector('.btn-transform');
    const originalText = btn.textContent;
    
    console.log(`Starting transform for entity ${entityId} (${entityName})`);
    btn.textContent = 'Running...';
    btn.disabled = true;
    
    try {
        const response = await api(`/entities/${entityId}/transforms/run`, {
            method: 'POST'
        });
        
        console.log(`Transform response status: ${response.status}`);
        
        if (!response.ok) {
            const data = await response.json();
            console.error('Transform error data:', data);
            throw new Error(data.detail || data.message || `Server returned ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Transform result:', result);
        
        if (result.message && !result.nodes?.length) {
            alert(result.message);
        } else {
            const nodeCount = result.nodes ? result.nodes.length : 0;
            const edgeCount = result.edges ? result.edges.length : 0;
            let msg = `Transform complete!\nCreated ${nodeCount} new entities and ${edgeCount} relationships.`;
            if (result.message) msg += `\n\nNote: ${result.message}`;
            alert(msg);
        }
        
        await Promise.all([loadEntities(), loadRelationships()]);
    } catch (err) {
        console.error('Transform execution failed:', err);
        alert('Transform error: ' + err.message);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function loadRelationships() {
    try {
        const response = await api('/relationships/');
        const rels = await response.json();
        const list = document.getElementById('relationships-list');
        
        if (rels.length === 0) {
            list.innerHTML = '<p style="color: #888;">No relationships yet. Create your first relationship!</p>';
            return;
        }
        
        list.innerHTML = rels.map(r => `
            <div class="list-item">
                <h3>Entity ${r.source_entity_id} → ${escapeHtml(r.relation)} → Entity ${r.target_entity_id}</h3>
                <p class="meta">Relationship ID: ${r.id}</p>
                <div class="actions">
                    <button class="btn-delete" onclick="deleteRelationship(${r.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading relationships:', err);
    }
}

async function loadApiKeys() {
    try {
        const response = await api('/apikeys/');
        const keys = await response.json();
        const list = document.getElementById('apikeys-list');
        
        if (keys.length === 0) {
            list.innerHTML = '<p style="color: #888;">No API keys yet. Create your first API key!</p>';
            return;
        }
        
        list.innerHTML = keys.map(k => `
            <div class="list-item">
                <h3>${escapeHtml(k.name)}</h3>
                <p>${escapeHtml(k.description || 'No description')}</p>
                <div class="key-value">${escapeHtml(k.key)}</div>
                <p class="meta">Status: <span class="${k.active ? 'status-active' : 'status-inactive'}">${k.active ? 'Active' : 'Inactive'}</span></p>
                <div class="actions">
                    <button class="btn-delete" onclick="deleteApiKey(${k.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading API keys:', err);
    }
}

async function createCase(e) {
    e.preventDefault();
    const name = document.getElementById('case-name').value;
    const description = document.getElementById('case-description').value;
    
    try {
        await api('/cases/', {
            method: 'POST',
            body: JSON.stringify({ name, description })
        });
        hideModal('case-modal');
        document.getElementById('case-name').value = '';
        document.getElementById('case-description').value = '';
        loadCases();
    } catch (err) {
        console.error('Error creating case:', err);
    }
}

async function createEntity(e) {
    e.preventDefault();
    const case_id = parseInt(document.getElementById('entity-case-id').value);
    const name = document.getElementById('entity-name').value;
    const kind = document.getElementById('entity-kind').value;
    const description = document.getElementById('entity-description').value;
    
    try {
        await api('/entities/', {
            method: 'POST',
            body: JSON.stringify({ case_id, name, kind, description })
        });
        hideModal('entity-modal');
        document.getElementById('entity-name').value = '';
        document.getElementById('entity-kind').value = '';
        document.getElementById('entity-description').value = '';
        loadEntities();
    } catch (err) {
        console.error('Error creating entity:', err);
    }
}

async function createRelationship(e) {
    e.preventDefault();
    const source_entity_id = parseInt(document.getElementById('rel-source').value);
    const target_entity_id = parseInt(document.getElementById('rel-target').value);
    const relation = document.getElementById('rel-relation').value;
    
    try {
        await api('/relationships/', {
            method: 'POST',
            body: JSON.stringify({ source_entity_id, target_entity_id, relation })
        });
        hideModal('relationship-modal');
        document.getElementById('rel-relation').value = '';
        loadRelationships();
    } catch (err) {
        console.error('Error creating relationship:', err);
    }
}

async function createApiKey(e) {
    e.preventDefault();
    const name = document.getElementById('apikey-name').value;
    const description = document.getElementById('apikey-description').value;
    
    try {
        await api('/apikeys/', {
            method: 'POST',
            body: JSON.stringify({ name, description })
        });
        hideModal('apikey-modal');
        document.getElementById('apikey-name').value = '';
        document.getElementById('apikey-description').value = '';
        loadApiKeys();
    } catch (err) {
        console.error('Error creating API key:', err);
    }
}

async function deleteCase(id) {
    if (!confirm('Delete this case? All related entities and relationships will also be deleted.')) return;
    try {
        await api(`/cases/${id}/`, { method: 'DELETE' });
        loadCases();
    } catch (err) {
        console.error('Error deleting case:', err);
    }
}

async function deleteEntity(id) {
    if (!confirm('Delete this entity? Related relationships will also be deleted.')) return;
    try {
        await api(`/entities/${id}/`, { method: 'DELETE' });
        loadEntities();
    } catch (err) {
        console.error('Error deleting entity:', err);
    }
}

async function deleteRelationship(id) {
    if (!confirm('Delete this relationship?')) return;
    try {
        await api(`/relationships/${id}/`, { method: 'DELETE' });
        loadRelationships();
    } catch (err) {
        console.error('Error deleting relationship:', err);
    }
}

async function deleteApiKey(id) {
    if (!confirm('Delete this API key?')) return;
    try {
        await api(`/apikeys/${id}/`, { method: 'DELETE' });
        loadApiKeys();
    } catch (err) {
        console.error('Error deleting API key:', err);
    }
}

async function populateCaseSelect() {
    try {
        const response = await api('/cases/');
        const cases = await response.json();
        const select = document.getElementById('entity-case-id');
        select.innerHTML = '<option value="">Select a case</option>' +
            cases.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
    } catch (err) {
        console.error('Error loading cases for select:', err);
    }
}

async function populateEntitySelects() {
    try {
        const response = await api('/entities/');
        const entities = await response.json();
        const options = '<option value="">Select entity</option>' +
            entities.map(e => `<option value="${e.id}">${escapeHtml(e.name)} (ID: ${e.id})</option>`).join('');
        document.getElementById('rel-source').innerHTML = options;
        document.getElementById('rel-target').innerHTML = options;
    } catch (err) {
        console.error('Error loading entities for select:', err);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

if (token) {
    showDashboard();
}

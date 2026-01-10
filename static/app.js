const API_BASE = '';
let token = localStorage.getItem('token');

let cachedCases = [];
let cachedEntities = [];
let cachedRelationships = [];

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
    } else if (id === 'import-modal') {
        populateImportCaseSelect();
    }
}

function populateImportCaseSelect() {
    const select = document.getElementById('import-case-id');
    select.innerHTML = '<option value="">Select a case...</option>' +
        cachedCases.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
}

async function handleImport(e) {
    e.preventDefault();
    const caseId = document.getElementById('import-case-id').value;
    const fileInput = document.getElementById('import-file');
    const statusEl = document.getElementById('import-status');
    const file = fileInput.files[0];
    
    if (!caseId || !file) {
        statusEl.innerHTML = '<span class="error">Please select a case and file</span>';
        return;
    }
    
    statusEl.innerHTML = '<span class="loading">Importing...</span>';
    
    const formData = new FormData();
    formData.append('case_id', caseId);
    formData.append('file', file);
    
    try {
        const response = await fetch('/import/entities', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Import failed');
        }
        
        let statusHtml = `<span class="success">${result.message}</span>`;
        if (result.errors && result.errors.length > 0) {
            statusHtml += '<div class="import-errors">' +
                result.errors.slice(0, 5).map(e => `<div>${escapeHtml(e)}</div>`).join('') +
                (result.errors.length > 5 ? `<div>...and ${result.errors.length - 5} more errors</div>` : '') +
                '</div>';
        }
        statusEl.innerHTML = statusHtml;
        
        fileInput.value = '';
        await loadEntities();
        
    } catch (err) {
        statusEl.innerHTML = `<span class="error">${escapeHtml(err.message)}</span>`;
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
    loadDashboardStats();
}

async function loadSectionData(section) {
    switch (section) {
        case 'dashboard': await loadDashboardStats(); break;
        case 'cases': await loadCases(); break;
        case 'entities': await loadEntities(); break;
        case 'relationships': await loadRelationships(); break;
        case 'graph': await loadGraph(); break;
        case 'timeline': await loadTimeline(); break;
        case 'apikeys': await loadApiKeys(); break;
    }
}

async function loadDashboardStats() {
    try {
        const [casesRes, entitiesRes, relsRes, keysRes, timelineRes] = await Promise.all([
            api('/cases/'),
            api('/entities/'),
            api('/relationships/'),
            api('/apikeys/'),
            api('/timeline/?limit=5')
        ]);
        
        const cases = await casesRes.json();
        const entities = await entitiesRes.json();
        const relationships = await relsRes.json();
        const apikeys = await keysRes.json();
        const timeline = await timelineRes.json();
        
        cachedCases = cases;
        cachedEntities = entities;
        cachedRelationships = relationships;
        
        document.getElementById('stat-cases').textContent = cases.length;
        document.getElementById('stat-entities').textContent = entities.length;
        document.getElementById('stat-relationships').textContent = relationships.length;
        document.getElementById('stat-apikeys').textContent = apikeys.length;
        
        renderEntityTypeChart(entities);
        renderRecentActivity(timeline);
        
    } catch (err) {
        console.error('Error loading dashboard stats:', err);
    }
}

function renderEntityTypeChart(entities) {
    const typeCounts = {};
    entities.forEach(e => {
        const kind = (e.kind || 'unknown').toLowerCase();
        typeCounts[kind] = (typeCounts[kind] || 0) + 1;
    });
    
    const container = document.getElementById('entity-type-chart');
    const total = entities.length || 1;
    
    if (Object.keys(typeCounts).length === 0) {
        container.innerHTML = '<p style="color: #666; text-align: center;">No entities yet</p>';
        return;
    }
    
    const colors = {
        ip: '#00ff88',
        domain: '#00bfff',
        url: '#ffa500',
        threat: '#ff3366',
        screenshot: '#9c27b0',
        person: '#00ced1',
        organization: '#cd853f',
        email: '#ffdd57',
        hash: '#a855f7'
    };
    
    container.innerHTML = Object.entries(typeCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([kind, count]) => {
            const pct = Math.round((count / total) * 100);
            const color = colors[kind] || '#666';
            return `
                <div class="chart-bar">
                    <div class="bar-label">
                        <span class="bar-kind" style="color: ${color}">${kind}</span>
                        <span class="bar-count">${count}</span>
                    </div>
                    <div class="bar-track">
                        <div class="bar-fill" style="width: ${pct}%; background: ${color}"></div>
                    </div>
                </div>
            `;
        }).join('');
}

function renderRecentActivity(activities) {
    const container = document.getElementById('recent-activity');
    
    if (activities.length === 0) {
        container.innerHTML = '<p style="color: #666;">No recent activity</p>';
        return;
    }
    
    const actionIcons = {
        created: '➕',
        deleted: '🗑️',
        updated: '✏️',
        transform: '🔄'
    };
    
    container.innerHTML = activities.map(a => {
        const icon = actionIcons[a.action] || '📋';
        const date = new Date(a.created_at);
        const timeAgo = getTimeAgo(date);
        
        return `
            <div class="recent-item">
                <span class="recent-icon">${icon}</span>
                <span class="recent-text">${escapeHtml(a.action)} ${escapeHtml(a.resource_type)}: ${escapeHtml(a.resource_name || 'N/A')}</span>
                <span class="recent-time">${timeAgo}</span>
            </div>
        `;
    }).join('');
}

async function loadCases() {
    try {
        const response = await api('/cases/');
        cachedCases = await response.json();
        renderCases(cachedCases);
        updateEntityCaseFilter();
    } catch (err) {
        console.error('Error loading cases:', err);
    }
}

function renderCases(cases) {
    const list = document.getElementById('cases-list');
    
    if (cases.length === 0) {
        list.innerHTML = '<p style="color: #888;">No cases found.</p>';
        return;
    }
    
    list.innerHTML = cases.map(c => `
        <div class="list-item">
            <h3>${escapeHtml(c.name)}</h3>
            <p>${escapeHtml(c.description || 'No description')}</p>
            <p class="meta">ID: ${c.id}</p>
            <div class="actions">
                <button class="btn-export" onclick="exportCase(${c.id}, 'json')">Export JSON</button>
                <button class="btn-export" onclick="exportCase(${c.id}, 'csv')">Export CSV</button>
                <button class="btn-delete" onclick="deleteCase(${c.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function exportCase(caseId, format) {
    try {
        const response = await fetch(`/export/case/${caseId}?format=${format}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const filename = response.headers.get('Content-Disposition')?.split('filename=')[1] || `case_${caseId}_export.${format}`;
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        
    } catch (err) {
        alert('Export failed: ' + err.message);
    }
}

function filterCases() {
    const search = document.getElementById('cases-search').value.toLowerCase();
    const filtered = cachedCases.filter(c => 
        c.name.toLowerCase().includes(search) ||
        (c.description || '').toLowerCase().includes(search)
    );
    renderCases(filtered);
}

function updateEntityCaseFilter() {
    const select = document.getElementById('entities-case-filter');
    if (!select) return;
    const currentValue = select.value;
    select.innerHTML = '<option value="">All Cases</option>' +
        cachedCases.map(c => `<option value="${c.id}"${c.id == currentValue ? ' selected' : ''}>${escapeHtml(c.name)}</option>`).join('');
}

async function loadEntities() {
    try {
        const response = await api('/entities/');
        cachedEntities = await response.json();
        renderEntities(cachedEntities);
    } catch (err) {
        console.error('Error loading entities:', err);
    }
}

function renderEntities(entities) {
    const list = document.getElementById('entities-list');
    
    if (entities.length === 0) {
        list.innerHTML = '<p style="color: #888;">No entities found.</p>';
        return;
    }
    
    const transformableKinds = ['ip', 'domain', 'url'];
    
    list.innerHTML = entities.map(e => {
        const canTransform = transformableKinds.includes((e.kind || '').toLowerCase());
        const transformBtn = canTransform 
            ? `<button class="btn-transform" onclick="runTransform(${e.id}, '${escapeHtml(e.name)}', '${escapeHtml(e.kind)}')">Run Transform</button>`
            : '';
        
        const caseName = cachedCases.find(c => c.id === e.case_id)?.name || `Case ${e.case_id}`;
        
        return `
            <div class="list-item" id="entity-${e.id}">
                <h3>${escapeHtml(e.name)}</h3>
                <p>Kind: <span class="kind-badge kind-${(e.kind || '').toLowerCase()}">${escapeHtml(e.kind || 'N/A')}</span></p>
                <p>${escapeHtml(e.description || 'No description')}</p>
                <p class="meta">Case: ${escapeHtml(caseName)} | ID: ${e.id}</p>
                <div class="actions">
                    <button class="btn-view" onclick="showEntityDetail(${e.id})">View Details</button>
                    ${transformBtn}
                    <button class="btn-delete" onclick="deleteEntity(${e.id})">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

function filterEntities() {
    const search = document.getElementById('entities-search').value.toLowerCase();
    const caseFilter = document.getElementById('entities-case-filter').value;
    const kindFilter = document.getElementById('entities-kind-filter').value.toLowerCase();
    
    const filtered = cachedEntities.filter(e => {
        const matchesSearch = e.name.toLowerCase().includes(search) ||
            (e.description || '').toLowerCase().includes(search);
        const matchesCase = !caseFilter || e.case_id == caseFilter;
        const matchesKind = !kindFilter || (e.kind || '').toLowerCase() === kindFilter;
        return matchesSearch && matchesCase && matchesKind;
    });
    
    renderEntities(filtered);
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
        cachedRelationships = await response.json();
        renderRelationships(cachedRelationships);
    } catch (err) {
        console.error('Error loading relationships:', err);
    }
}

function renderRelationships(rels) {
    const list = document.getElementById('relationships-list');
    
    if (rels.length === 0) {
        list.innerHTML = '<p style="color: #888;">No relationships found.</p>';
        return;
    }
    
    list.innerHTML = rels.map(r => {
        const sourceEntity = cachedEntities.find(e => e.id === r.source_entity_id);
        const targetEntity = cachedEntities.find(e => e.id === r.target_entity_id);
        const sourceName = sourceEntity ? sourceEntity.name : `Entity ${r.source_entity_id}`;
        const targetName = targetEntity ? targetEntity.name : `Entity ${r.target_entity_id}`;
        
        return `
            <div class="list-item">
                <h3>${escapeHtml(sourceName)} <span class="relation-arrow">→ ${escapeHtml(r.relation)} →</span> ${escapeHtml(targetName)}</h3>
                <p class="meta">ID: ${r.id}</p>
                <div class="actions">
                    <button class="btn-delete" onclick="deleteRelationship(${r.id})">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

function filterRelationships() {
    const search = document.getElementById('relationships-search').value.toLowerCase();
    
    const filtered = cachedRelationships.filter(r => {
        const sourceEntity = cachedEntities.find(e => e.id === r.source_entity_id);
        const targetEntity = cachedEntities.find(e => e.id === r.target_entity_id);
        const sourceName = sourceEntity?.name || '';
        const targetName = targetEntity?.name || '';
        
        return r.relation.toLowerCase().includes(search) ||
            sourceName.toLowerCase().includes(search) ||
            targetName.toLowerCase().includes(search);
    });
    
    renderRelationships(filtered);
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

async function loadTimeline() {
    try {
        const response = await api('/timeline/');
        const activities = await response.json();
        const list = document.getElementById('timeline-list');
        
        if (activities.length === 0) {
            list.innerHTML = '<p style="color: #888;">No activity yet. Start creating cases and entities!</p>';
            return;
        }
        
        const actionIcons = {
            created: '➕',
            deleted: '🗑️',
            updated: '✏️',
            transform: '🔄'
        };
        
        const resourceColors = {
            case: '#00ff88',
            entity: '#00bfff',
            relationship: '#ffa500',
            apikey: '#9c27b0'
        };
        
        list.innerHTML = activities.map(a => {
            const icon = actionIcons[a.action] || '📋';
            const color = resourceColors[a.resource_type] || '#888';
            const date = new Date(a.created_at);
            const timeAgo = getTimeAgo(date);
            
            return `
                <div class="timeline-item">
                    <div class="timeline-icon" style="background: ${color}20; color: ${color}">${icon}</div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="timeline-action">${escapeHtml(a.action)}</span>
                            <span class="timeline-resource" style="color: ${color}">${escapeHtml(a.resource_type)}</span>
                        </div>
                        <div class="timeline-name">${escapeHtml(a.resource_name || `ID: ${a.resource_id}`)}</div>
                        ${a.details ? `<div class="timeline-details">${escapeHtml(a.details)}</div>` : ''}
                        <div class="timeline-time" title="${date.toLocaleString()}">${timeAgo}</div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error('Error loading timeline:', err);
    }
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

let networkInstance = null;

const kindConfig = {
    ip: { color: '#00ff88', shape: 'hexagon', icon: '🌐' },
    domain: { color: '#00bfff', shape: 'diamond', icon: '🔗' },
    url: { color: '#ffa500', shape: 'square', icon: '🔗' },
    threat: { color: '#ff3366', shape: 'triangle', icon: '⚠️' },
    screenshot: { color: '#9c27b0', shape: 'image', icon: '📷' },
    person: { color: '#00ced1', shape: 'ellipse', icon: '👤' },
    organization: { color: '#8b4513', shape: 'box', icon: '🏢' },
    email: { color: '#ffdd57', shape: 'dot', icon: '✉️' },
    hash: { color: '#a855f7', shape: 'star', icon: '#️⃣' }
};

function renderLegend() {
    const legend = document.getElementById('graph-legend');
    if (!legend) return;
    
    legend.innerHTML = Object.entries(kindConfig).map(([kind, cfg]) => `
        <div class="legend-item">
            <span class="legend-color" style="background: ${cfg.color}; box-shadow: 0 0 8px ${cfg.color}80;"></span>
            <span class="legend-label">${kind.charAt(0).toUpperCase() + kind.slice(1)}</span>
        </div>
    `).join('');
}

async function loadGraph() {
    try {
        const [entitiesRes, relationshipsRes, casesRes] = await Promise.all([
            api('/entities/'),
            api('/relationships/'),
            api('/cases/')
        ]);
        
        const entities = await entitiesRes.json();
        const relationships = await relationshipsRes.json();
        const cases = await casesRes.json();
        
        const caseFilter = document.getElementById('graph-case-filter');
        const currentValue = caseFilter.value;
        caseFilter.innerHTML = '<option value="">All Cases</option>' +
            cases.map(c => `<option value="${c.id}"${c.id == currentValue ? ' selected' : ''}>${escapeHtml(c.name)}</option>`).join('');
        
        let filteredEntities = entities;
        let filteredRelationships = relationships;
        
        if (currentValue) {
            const caseId = parseInt(currentValue);
            filteredEntities = entities.filter(e => e.case_id === caseId);
            const entityIds = new Set(filteredEntities.map(e => e.id));
            filteredRelationships = relationships.filter(r => 
                entityIds.has(r.source_entity_id) && entityIds.has(r.target_entity_id)
            );
        }
        
        renderLegend();
        
        const nodes = new vis.DataSet(filteredEntities.map(e => {
            const kind = (e.kind || '').toLowerCase();
            const cfg = kindConfig[kind] || { color: '#666', shape: 'dot' };
            
            return {
                id: e.id,
                label: e.name,
                title: `<div style="background:#1a1a1a;padding:10px;border-radius:8px;border:1px solid ${cfg.color};max-width:250px;">
                    <strong style="color:${cfg.color}">${e.kind || 'Unknown'}</strong><br>
                    <span style="color:#e0e0e0">${e.name}</span><br>
                    <small style="color:#888">${e.description || 'No description'}</small>
                </div>`,
                color: {
                    background: cfg.color,
                    border: cfg.color,
                    highlight: { 
                        background: '#ffffff', 
                        border: cfg.color 
                    },
                    hover: {
                        background: cfg.color,
                        border: '#ffffff'
                    }
                },
                font: { 
                    color: '#ffffff', 
                    size: 14,
                    face: 'Inter, system-ui, sans-serif',
                    strokeWidth: 3,
                    strokeColor: '#000000'
                },
                shape: cfg.shape,
                size: 25,
                borderWidth: 3,
                borderWidthSelected: 5,
                shadow: {
                    enabled: true,
                    color: cfg.color + '60',
                    size: 15,
                    x: 0,
                    y: 0
                }
            };
        }));
        
        const edges = new vis.DataSet(filteredRelationships.map(r => ({
            id: r.id,
            from: r.source_entity_id,
            to: r.target_entity_id,
            label: r.relation,
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.8,
                    type: 'arrow'
                }
            },
            color: { 
                color: '#444444',
                highlight: '#00ff88',
                hover: '#00ff88',
                opacity: 0.8
            },
            font: { 
                color: '#888888', 
                size: 11,
                face: 'Inter, system-ui, sans-serif',
                strokeWidth: 2,
                strokeColor: '#000000',
                align: 'middle'
            },
            width: 2,
            hoverWidth: 3,
            selectionWidth: 4,
            smooth: {
                enabled: true,
                type: 'curvedCW',
                roundness: 0.15
            },
            shadow: {
                enabled: true,
                color: 'rgba(0,0,0,0.3)',
                size: 5
            }
        })));
        
        const container = document.getElementById('graph-container');
        
        if (networkInstance) {
            networkInstance.destroy();
        }
        
        if (filteredEntities.length === 0) {
            container.innerHTML = `
                <div class="graph-empty">
                    <div class="empty-icon">🔍</div>
                    <h3>No Entities Found</h3>
                    <p>Create some entities to see them visualized here</p>
                </div>
            `;
            return;
        }
        
        const options = {
            nodes: {
                borderWidth: 3,
                shadow: true,
                scaling: {
                    min: 20,
                    max: 40
                }
            },
            edges: {
                width: 2,
                shadow: true
            },
            physics: {
                enabled: true,
                stabilization: { 
                    enabled: true,
                    iterations: 150,
                    updateInterval: 25
                },
                barnesHut: {
                    gravitationalConstant: -4000,
                    centralGravity: 0.3,
                    springLength: 120,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.5
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 50,
                hideEdgesOnDrag: true,
                hideEdgesOnZoom: true,
                keyboard: {
                    enabled: true
                },
                navigationButtons: true,
                zoomView: true
            },
            layout: {
                improvedLayout: true,
                randomSeed: 42
            }
        };
        
        networkInstance = new vis.Network(container, { nodes, edges }, options);
        
        networkInstance.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const entity = filteredEntities.find(e => e.id === nodeId);
                if (entity) {
                    showEntityDetails(entity);
                }
            }
        });
        
        networkInstance.on('stabilizationProgress', function(params) {
            const progress = Math.round((params.iterations / params.total) * 100);
            container.style.opacity = 0.3 + (progress / 100) * 0.7;
        });
        
        networkInstance.on('stabilizationIterationsDone', function() {
            container.style.opacity = 1;
        });
        
    } catch (err) {
        console.error('Error loading graph:', err);
    }
}

function showEntityDetails(entity) {
    const kind = (entity.kind || '').toLowerCase();
    const cfg = kindConfig[kind] || { color: '#666' };
    
    const existingPopup = document.querySelector('.entity-popup');
    if (existingPopup) existingPopup.remove();
    
    const popup = document.createElement('div');
    popup.className = 'entity-popup';
    popup.innerHTML = `
        <div class="popup-header" style="border-color: ${cfg.color}">
            <span class="popup-type" style="color: ${cfg.color}">${entity.kind || 'Unknown'}</span>
            <button class="popup-close" onclick="this.closest('.entity-popup').remove()">×</button>
        </div>
        <div class="popup-body">
            <h3>${escapeHtml(entity.name)}</h3>
            <p>${escapeHtml(entity.description || 'No description')}</p>
            <div class="popup-meta">ID: ${entity.id} | Case: ${entity.case_id}</div>
        </div>
    `;
    document.getElementById('graph-section').appendChild(popup);
    
    setTimeout(() => popup.classList.add('visible'), 10);
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

async function showEntityDetail(entityId) {
    const entity = cachedEntities.find(e => e.id === entityId);
    if (!entity) return;
    
    const caseName = cachedCases.find(c => c.id === entity.case_id)?.name || `Case ${entity.case_id}`;
    
    const relatedRels = cachedRelationships.filter(
        r => r.source_id === entityId || r.target_id === entityId
    );
    
    const relatedEntities = relatedRels.map(r => {
        const otherId = r.source_id === entityId ? r.target_id : r.source_id;
        const otherEntity = cachedEntities.find(e => e.id === otherId);
        const direction = r.source_id === entityId ? 'outgoing' : 'incoming';
        return { relation: r.relation, entity: otherEntity, direction };
    }).filter(r => r.entity);
    
    let comments = [];
    try {
        const response = await api(`/comments/entity/${entityId}`);
        comments = await response.json();
    } catch (err) {
        console.error('Error loading comments:', err);
    }
    
    const kindColors = {
        ip: '#00ff88', domain: '#00bfff', url: '#ffa500', threat: '#ff3366',
        screenshot: '#9c27b0', person: '#00ced1', organization: '#cd853f',
        email: '#ffdd57', hash: '#a855f7'
    };
    const color = kindColors[(entity.kind || '').toLowerCase()] || '#888';
    
    let html = `
        <div class="entity-detail">
            <div class="entity-header" style="border-left: 4px solid ${color};">
                <h2>${escapeHtml(entity.name)}</h2>
                <span class="kind-badge kind-${(entity.kind || '').toLowerCase()}">${escapeHtml(entity.kind || 'Unknown')}</span>
            </div>
            <div class="detail-grid">
                <div class="detail-section">
                    <h4>Information</h4>
                    <div class="detail-row"><label>ID:</label><span>${entity.id}</span></div>
                    <div class="detail-row"><label>Case:</label><span>${escapeHtml(caseName)}</span></div>
                    <div class="detail-row"><label>Description:</label><span>${escapeHtml(entity.description || 'No description')}</span></div>
                </div>
                <div class="detail-section">
                    <h4>Related Entities (${relatedEntities.length})</h4>
                    <div class="related-list">
                        ${relatedEntities.length === 0 ? '<p class="no-data">No relationships found</p>' : 
                        relatedEntities.map(r => `
                            <div class="related-item ${r.direction}">
                                <span class="rel-arrow">${r.direction === 'outgoing' ? '→' : '←'}</span>
                                <span class="rel-type">${escapeHtml(r.relation)}</span>
                                <span class="rel-entity" onclick="showEntityDetail(${r.entity.id})">${escapeHtml(r.entity.name)}</span>
                                <span class="kind-badge kind-${(r.entity.kind || '').toLowerCase()}">${escapeHtml(r.entity.kind)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            <div class="comments-section">
                <h4>Notes & Comments (${comments.length})</h4>
                <div class="comment-form">
                    <textarea id="new-comment-text" placeholder="Add a note or comment..."></textarea>
                    <button onclick="addComment(${entity.id})">Add Comment</button>
                </div>
                <div class="comments-list" id="comments-list-${entity.id}">
                    ${comments.length === 0 ? '<p class="no-data">No comments yet</p>' :
                    comments.map(c => `
                        <div class="comment-item">
                            <div class="comment-text">${escapeHtml(c.text)}</div>
                            <div class="comment-meta">
                                <span>${getTimeAgo(new Date(c.created_at))}</span>
                                <button class="btn-small btn-delete" onclick="deleteComment(${c.id}, ${entity.id})">Delete</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="detail-actions">
                <button class="btn-transform" onclick="hideModal('entity-detail-modal'); runTransform(${entity.id}, '${escapeHtml(entity.name)}', '${escapeHtml(entity.kind)}')">Run Transform</button>
                <button class="btn-delete" onclick="hideModal('entity-detail-modal'); deleteEntity(${entity.id})">Delete Entity</button>
            </div>
        </div>
    `;
    
    document.getElementById('entity-detail-content').innerHTML = html;
    showModal('entity-detail-modal');
}

async function addComment(entityId) {
    const textEl = document.getElementById('new-comment-text');
    const text = textEl.value.trim();
    if (!text) return;
    
    try {
        await api('/comments/', {
            method: 'POST',
            body: JSON.stringify({ entity_id: entityId, text })
        });
        textEl.value = '';
        showEntityDetail(entityId);
    } catch (err) {
        console.error('Error adding comment:', err);
    }
}

async function deleteComment(commentId, entityId) {
    if (!confirm('Delete this comment?')) return;
    try {
        await api(`/comments/${commentId}`, { method: 'DELETE' });
        showEntityDetail(entityId);
    } catch (err) {
        console.error('Error deleting comment:', err);
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

document.addEventListener('keydown', function(e) {
    if (!token) return;
    
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
        return;
    }
    
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    const shortcuts = {
        'd': 'dashboard',
        'c': 'cases',
        'e': 'entities',
        'r': 'relationships',
        'g': 'graph',
        't': 'timeline',
        'k': 'apikeys'
    };
    
    if (shortcuts[e.key]) {
        e.preventDefault();
        const navBtns = document.querySelectorAll('.nav-btn');
        const sections = ['dashboard', 'cases', 'entities', 'relationships', 'graph', 'timeline', 'apikeys'];
        const idx = sections.indexOf(shortcuts[e.key]);
        if (navBtns[idx]) {
            navBtns.forEach(btn => btn.classList.remove('active'));
            navBtns[idx].classList.add('active');
        }
        document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
        document.getElementById(`${shortcuts[e.key]}-section`).classList.remove('hidden');
        loadSectionData(shortcuts[e.key]);
    }
    
    if (e.key === 'n' && e.ctrlKey) {
        e.preventDefault();
        const activeSection = document.querySelector('.section:not(.hidden)');
        if (activeSection) {
            const sectionId = activeSection.id;
            if (sectionId === 'cases-section') showModal('case-modal');
            else if (sectionId === 'entities-section') showModal('entity-modal');
            else if (sectionId === 'relationships-section') showModal('relationship-modal');
            else if (sectionId === 'apikeys-section') showModal('apikey-modal');
        }
    }
    
    if (e.key === '?' && e.shiftKey) {
        alert('Keyboard Shortcuts:\\n\\nd - Dashboard\\nc - Cases\\ne - Entities\\nr - Relationships\\ng - Graph\\nt - Timeline\\nk - API Keys\\nCtrl+N - New item\\nEsc - Close modal');
    }
});

if (token) {
    showDashboard();
}

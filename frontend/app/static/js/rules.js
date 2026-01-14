// Value options for dropdowns
const VALUE_OPTIONS = {
    'urgency': ['HIGH', 'MEDIUM', 'LOW'],
    'request_type': ['CONNECTION_ISSUE', 'PAYMENT_PROBLEM', 'SPEED_COMPLAINT', 'STREAMING_ISSUE'],
    'service': ['Superonline', 'TV+', 'Paycell']
};

document.addEventListener('DOMContentLoaded', function () {
    fetchVariables();
    updatePreview();

    // Delegate event listener for field selection changes in Rule Modal
    const ruleForm = document.getElementById('addRuleForm');
    if (ruleForm) {
        ruleForm.addEventListener('change', function (e) {
            if (e.target.classList.contains('field-select')) {
                handleFieldChange(e.target);
            }
            updatePreview();
        });

        ruleForm.addEventListener('input', updatePreview);
    }
});

function handleFieldChange(selectElement) {
    const field = selectElement.value;
    const row = selectElement.closest('.rule-part');
    const inputContainer = row.querySelector('.value-input-container');

    // Clear current input
    inputContainer.innerHTML = '';

    if (VALUE_OPTIONS[field]) {
        // Create dropdown for predefined values
        const select = document.createElement('select');
        select.className = 'form-select value-input';
        select.required = true;

        VALUE_OPTIONS[field].forEach(val => {
            const option = document.createElement('option');
            option.value = `'${val}'`; // Add quotes for string values
            option.text = val;
            select.appendChild(option);
        });
        inputContainer.appendChild(select);
    } else {
        // Standard text/number input for other fields (e.g., waiting_hours)
        const input = document.createElement('input');
        input.type = field === 'waiting_hours' ? 'number' : 'text';
        input.className = 'form-control value-input';
        input.placeholder = field === 'waiting_hours' ? 'Saat' : 'Değer';
        input.required = true;
        inputContainer.appendChild(input);
    }
}

function addGate(operator, label) {
    addCondition(operator, label);
}

function addParenthesis(type) {
    const container = document.getElementById('additionalConditions');
    const div = document.createElement('div');
    div.className = 'row g-2 align-items-center mb-2 mt-2 rule-part';

    div.innerHTML = `
        <div class="col-12 text-center">
             <input type="text" class="form-control text-center fw-bold bg-light fs-4 parent-input" value="${type}" readonly 
             style="width: 60px; display: inline-block;">
             <button type="button" class="btn btn-outline-danger btn-sm ms-2" onclick="this.closest('.rule-part').remove(); updatePreview();">
                <i class="bi bi-trash"></i>
            </button>
             <input type="hidden" class="logic-operator" value="${type}">
        </div>
    `;
    container.appendChild(div);
    updatePreview();
}

function addMathOp(op, label) {
    const container = document.getElementById('additionalConditions');
    const div = document.createElement('div');
    div.className = 'row g-2 align-items-center mb-2 mt-2 rule-part';

    div.innerHTML = `
        <div class="col-12 text-center mb-1 position-relative">
            <hr class="position-absolute w-100 top-50 start-0 translate-middle-y" style="z-index:-1; opacity:0.3">
            <span class="badge bg-warning text-dark px-3 py-2 rounded-pill shadow-sm border border-light" style="font-size: 0.9rem;">${label || op}</span>
            <input type="hidden" class="logic-operator" value="${op}">
            <button type="button" class="btn btn-outline-danger btn-sm ms-2 position-absolute end-0 top-50 translate-middle-y" onclick="this.closest('.rule-part').remove(); updatePreview();">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(div);
    updatePreview();
}

// --- Rule Builder Logic (Full Calculator Mode) ---

function addRuleToken(type, value) {
    const container = document.getElementById('ruleContainer');

    // Remove placeholder
    const placeholder = container.querySelector('.placeholder-text-rule');
    if (placeholder) placeholder.remove();

    const div = document.createElement('div');
    div.className = 'rule-token d-flex align-items-center bg-white border rounded shadow-sm px-2 py-1 position-relative';
    div.setAttribute('data-type', type);

    let content = '';

    if (type === 'parenthesis') {
        div.className += ' bg-warning-subtle border-warning';
        content = `<span class="fw-bold fs-5 px-2">${value}</span>
                   <input type="hidden" class="token-value" value="${value}">`;
    }
    else if (type === 'logic') {
        div.className += ' bg-dark text-white border-dark';
        content = `<span class="fw-bold fs-6 px-2 text-uppercase">${value}</span>
                   <input type="hidden" class="token-value" value="${value}">`;
    }
    else if (type === 'operator') {
        div.className += ' bg-info-subtle border-info text-info-emphasis';
        content = `<span class="fw-bold font-monospace px-1">${value}</span>
                   <input type="hidden" class="token-value" value="${value}">`;
    }
    else if (type === 'field') {
        // Dynamic Select for Field
        content = `
            <select class="form-select form-select-sm border-0 bg-transparent fw-bold field-select" style="width: auto; min-width: 120px;" onchange="updateRulePreview()">
                <option value="" disabled selected>Alan..</option>
            </select>`;

        // We need to populate this select
        setTimeout(() => {
            const select = div.querySelector('select');
            populateSelectWithFields(select);
        }, 0);
    }
    else if (type === 'value') {
        content = `<input type="text" class="form-control form-control-sm border-0 bg-transparent fw-bold text-primary" 
                   style="width: 80px;" placeholder="Değer" oninput="updateRulePreview()">`;
    }

    // Close button
    content += `<button type="button" class="btn-close ms-2" style="width: 0.5rem; height: 0.5rem;" onclick="this.closest('.rule-token').remove(); updateRulePreview();"></button>`;

    div.innerHTML = content;
    container.appendChild(div);
    updateRulePreview();
}

function populateSelectWithFields(select) {
    for (const [key, label] of Object.entries(AVAILABLE_FIELDS)) {
        const option = document.createElement('option');
        option.value = key;
        option.innerText = label;
        select.appendChild(option);
    }
}

function updateRulePreview() {
    const tokens = document.querySelectorAll('.rule-token');
    const preview = document.getElementById('rulePreviewText');

    if (tokens.length === 0) {
        preview.innerText = '...';
        return;
    }

    let str = '';
    tokens.forEach(t => {
        const type = t.getAttribute('data-type');

        if (type === 'field') {
            const sel = t.querySelector('select');
            const val = sel.options[sel.selectedIndex]?.text || '?';
            str += `[${val}] `;
        }
        else if (type === 'value') {
            const val = t.querySelector('input').value || '?';
            str += `'${val}' `;
        }
        else {
            str += t.querySelector('.token-value').value + ' ';
        }
    });
    preview.innerText = str;
}

async function saveRule() {
    const tokens = document.querySelectorAll('.rule-token');
    if (tokens.length === 0) {
        alert('Lütfen en az bir koşul ekleyiniz.');
        return;
    }

    let condition = '';
    tokens.forEach(t => {
        const type = t.getAttribute('data-type');

        if (type === 'field') {
            const sel = t.querySelector('select');
            if (sel.value) condition += `${sel.value} `;
        }
        else if (type === 'value') {
            const val = t.querySelector('input').value;
            // Try to handle numbers vs strings intelligently? 
            // For now assume string if not number? Or simple quote wrapping?
            // Python rule engine usually handles '50' as number if field is number. 
            // Let's just pass plain value. The user might type 'High'.
            // Ideally we should quote strings.
            if (!isNaN(val) && val !== '') condition += `${val} `;
            else condition += `'${val}' `;
        }
        else {
            condition += t.querySelector('.token-value').value + ' ';
        }
    });
    condition = condition.trim();

    const weight = document.querySelector('#addRuleForm input[name="weight"]').value;
    if (!weight) {
        alert('Lütfen ağırlık puanı giriniz.');
        return;
    }

    const data = {
        condition: condition,
        weight: parseInt(weight)
    };

    try {
        const response = await fetch(`${API_BASE}/rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Kural başarıyla kaydedildi!');
            window.location.reload();
        } else {
            const error = await response.json();
            alert('Hata: ' + (error.detail || 'Bilinmeyen hata'));
        }
    } catch (e) {
        console.error(e);
        alert('Bağlantı hatası!');
    }
}


// --- Variable Creator Logic (Calculator Mode) ---

function addToken(type, value) {
    const container = document.getElementById('formulaContainer');

    // Remove placeholder if exists
    const placeholder = container.querySelector('.placeholder-text');
    if (placeholder) placeholder.remove();

    const div = document.createElement('div');
    div.className = 'formula-token d-flex align-items-center bg-white border rounded shadow-sm px-2 py-1 position-relative';
    div.setAttribute('data-type', type);

    let content = '';

    if (type === 'parenthesis') {
        div.className += ' bg-warning-subtle border-warning';
        content = `<span class="fw-bold fs-5 px-2">${value}</span>
                   <input type="hidden" class="token-value" value="${value}">`;
    }
    else if (type === 'operator') {
        div.className += ' bg-dark text-white border-dark';
        content = `<span class="fw-bold fs-6 px-2">${value}</span>
                   <input type="hidden" class="token-value" value="${value}">`;
    }
    else if (type === 'field') {
        content = `
            <select class="form-select form-select-sm border-0 bg-transparent fw-bold" style="width: auto; min-width: 120px;" onchange="updateFormulaPreview()">
                <option value="" disabled selected>Alan Seç...</option>
                <option value="urgency_score">Aciliyet Puanı</option>
                <option value="waiting_hours">Bekleme Süresi</option>
                <option value="capacity_usage">Kapasite Kullanımı</option>
            </select>`;
    }
    else if (type === 'constant') {
        content = `<input type="number" class="form-control form-control-sm border-0 bg-transparent fw-bold text-primary" 
                   style="width: 80px;" placeholder="Sayı" oninput="updateFormulaPreview()">`;
    }

    // Close button for token
    content += `<button type="button" class="btn-close ms-2" style="width: 0.5rem; height: 0.5rem;" onclick="this.closest('.formula-token').remove(); updateFormulaPreview();"></button>`;

    div.innerHTML = content;
    container.appendChild(div);
    updateFormulaPreview();
}

function updateFormulaPreview() {
    const tokens = document.querySelectorAll('.formula-token');
    if (tokens.length === 0) {
        document.getElementById('formulaPreviewText').innerText = '...';
        return;
    }

    let formulaHtml = '';

    tokens.forEach(token => {
        const type = token.getAttribute('data-type');
        let val = '';

        if (type === 'parenthesis' || type === 'operator') {
            val = token.querySelector('.token-value').value;
            if (type === 'operator') val = `<span class="badge bg-secondary mx-1">${val}</span>`;
            else val = `<span class="text-danger fw-bold mx-1">${val}</span>`;
        }
        else if (type === 'field') {
            const select = token.querySelector('select');
            val = select.options[select.selectedIndex]?.text || '?';
            val = `<span class="text-primary fw-bold">[${val}]</span>`;
        }
        else if (type === 'constant') {
            const input = token.querySelector('input');
            val = input.value || '0';
            val = `<span class="text-dark fw-bold">${val}</span>`;
        }

        formulaHtml += val;
    });

    document.getElementById('formulaPreviewText').innerHTML = formulaHtml;
}

// Global listener not needed for 'change' delegation as we use inline onchange for simplicity in tokens
// But we keep the global one just in case we switch back or for consistency

async function saveVariable() {
    const form = document.getElementById('addVariableForm');
    const name = form.varName.value;
    const tokens = document.querySelectorAll('.formula-token');

    let formula = '';

    tokens.forEach(token => {
        const type = token.getAttribute('data-type');

        if (type === 'parenthesis' || type === 'operator') {
            formula += ` ${token.querySelector('.token-value').value} `;
        }
        else if (type === 'field') {
            const select = token.querySelector('select');
            if (select.value) {
                formula += ` ${select.value} `;
            }
        }
        else if (type === 'constant') {
            const input = token.querySelector('input');
            if (input.value) {
                formula += ` ${input.value} `;
            }
        }
    });

    // Cleanup formula
    formula = formula.trim().replace(/\s+/g, ' ');

    if (!name || !formula) {
        alert('Lütfen geçerli bir ad ve formül giriniz.');
        return;
    }

    try {
        const response = await fetch('/api/rules/variables', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                formula: formula,
                description: form.description.value
            })
        });

        if (response.ok) {
            alert('Değişken kaydedildi!');
            window.location.reload();
        } else {
            const err = await response.json();
            alert('Hata: ' + (err.detail || 'Kayıt başarısız'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Bir hata oluştu.');
    }
}

// Global Configuration
const API_BASE = 'http://localhost:8000'; // Direct backend access

// Global state for fields (Static + Dynamic)
let AVAILABLE_FIELDS = {
    'urgency_score': 'Aciliyet Puanı',
    'waiting_hours': 'Bekleme Süresi',
    'capacity_usage': 'Kapasite Kullanımı'
};

document.addEventListener('DOMContentLoaded', async () => {
    await fetchVariables(); // Load dynamic variables
    populateAllFieldSelects(); // Populate dropdowns
});

async function fetchVariables() {
    try {
        // Correct endpoint: http://localhost:8000/rules/variables
        const response = await fetch(`${API_BASE}/rules/variables`);
        if (response.ok) {
            const variables = await response.json();

            // Add dynamic variables to global list
            variables.forEach(v => {
                AVAILABLE_FIELDS[v.name] = v.name + ' (Değişken)';
            });

            // Re-populate if already rendered
            populateAllFieldSelects();
        }
    } catch (e) {
        console.error('Error fetching variables:', e);
    }
}

function populateAllFieldSelects() {
    const selects = document.querySelectorAll('.field-select, .var-field-select');
    selects.forEach(select => {
        const currentVal = select.value;
        select.innerHTML = '<option value="" disabled selected>Alan Seç...</option>';

        // Add Standard Fields
        for (const [key, label] of Object.entries(AVAILABLE_FIELDS)) {
            const option = document.createElement('option');
            option.value = key;
            option.innerText = label;
            select.appendChild(option);
        }
        if (currentVal && AVAILABLE_FIELDS[currentVal]) {
            select.value = currentVal;
        } else {
            select.value = '';
        }
    });
}

async function saveRule() {
    const condition = updatePreview();
    const weight = document.querySelector('input[name="weight"]').value;

    if (!condition || !weight) {
        alert('Lütfen kural ve ağırlık alanlarını doldurunuz.');
        return;
    }

    try {
        const response = await fetch('/api/rules', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                condition: condition,
                weight: parseInt(weight),
                is_active: true
            })
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const err = await response.json();
            alert('Hata: ' + (err.detail || 'Kayıt başarısız'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Bir hata oluştu.');
    }
}

async function deleteRule(ruleId) {
    if (!confirm('Bu kuralı silmek istediğinize emin misiniz?')) return;

    try {
        const response = await fetch(`${API_BASE}/rules/${ruleId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            window.location.reload();
        } else {
            alert('Silme işlemi başarısız');
        }
    } catch (e) {
        console.error(e);
        alert('Hata oluştu');
    }
}

function editRule(ruleId, weight, isActive) {
    // For now, simpler edit: just update weight/active status via prompt or simple modal
    // A full edit would require parsing the condition string back to UI which is complex.
    // We will implement a quick weight updater for now.
    const newWeight = prompt("Yeni ağırlık puanını giriniz:", weight);
    if (newWeight !== null) {
        updateRuleApi(ruleId, { weight: parseInt(newWeight) });
    }
}

async function updateRuleApi(ruleId, data) {
    try {
        const response = await fetch(`/api/rules/${ruleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            window.location.reload();
        } else {
            alert('Güncelleme başarısız.');
        }
    } catch (e) {
        alert('Hata oluştu.');
    }
}

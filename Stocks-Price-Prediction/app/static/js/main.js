// ==================== THEME MANAGEMENT ====================
const themeToggle = document.getElementById('themeToggle');
const htmlElement = document.documentElement;

// Load theme preference
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        updateThemeIcon();
    }
}

// Update theme icon
function updateThemeIcon() {
    if (themeToggle) {
        const isDark = document.body.classList.contains('dark-theme');
        themeToggle.innerHTML = isDark ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-stars"></i>';
    }
}

// Toggle theme
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateThemeIcon();
    });
}

// Load theme on page load
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
});

// ==================== CHATBOT MANAGEMENT ====================
let chatbotOpen = false;

function toggleChatbot() {
    const widget = document.getElementById('chatbot-widget');
    if (widget) {
        chatbotOpen = !chatbotOpen;
        widget.classList.toggle('active');
        if (chatbotOpen) {
            loadChatTips();
        }
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';
    
    try {
        const response = await fetch('{{ url_for("chat") }}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        if (response.ok) {
            addMessageToChat(data.response, 'bot');
        } else {
            addMessageToChat('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        addMessageToChat('Error: ' + error.message, 'bot');
    }
}

function addMessageToChat(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function loadChatTips() {
    try {
        const response = await fetch('{{ url_for("chat_tips") }}');
        const data = await response.json();
        
        if (data.tips && data.tips.length > 0) {
            const randomTip = data.tips[Math.floor(Math.random() * data.tips.length)];
            addMessageToChat(randomTip, 'bot');
        }
    } catch (error) {
        console.error('Error loading tips:', error);
    }
}

// Allow Enter key to send messages
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});

// ==================== UTILITIES ====================
function formatDate(date) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(date).toLocaleDateString(undefined, options);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '10000';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// ==================== API HELPERS ====================
async function fetchJSON(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

// ==================== CHART HELPERS ====================
function createLineChart(elementId, data, title) {
    const trace = {
        x: data.x,
        y: data.y,
        type: 'scatter',
        mode: 'lines+markers',
        name: data.name || 'Data',
        line: {
            color: data.color || 'rgb(31, 119, 180)',
            width: 2
        }
    };
    
    const layout = {
        title: title,
        xaxis: { title: data.xLabel || 'X Axis' },
        yaxis: { title: data.yLabel || 'Y Axis' },
        hovermode: 'x unified',
        responsive: true,
        margin: { l: 60, r: 40, t: 40, b: 60 }
    };
    
    Plotly.newPlot(elementId, [trace], layout, { responsive: true });
}

function createBarChart(elementId, data, title) {
    const trace = {
        x: data.categories,
        y: data.values,
        type: 'bar',
        marker: {
            color: data.color || 'rgb(31, 119, 180)'
        }
    };
    
    const layout = {
        title: title,
        xaxis: { title: data.xLabel || 'Categories' },
        yaxis: { title: data.yLabel || 'Values' },
        responsive: true,
        margin: { l: 60, r: 40, t: 40, b: 60 }
    };
    
    Plotly.newPlot(elementId, [trace], layout, { responsive: true });
}

function createMultiLineChart(elementId, datasets, title) {
    const traces = datasets.map(dataset => ({
        x: dataset.x,
        y: dataset.y,
        name: dataset.name,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: dataset.color }
    }));
    
    const layout = {
        title: title,
        xaxis: { title: 'X Axis' },
        yaxis: { title: 'Y Axis' },
        hovermode: 'x unified',
        responsive: true,
        margin: { l: 60, r: 40, t: 40, b: 60 }
    };
    
    Plotly.newPlot(elementId, traces, layout, { responsive: true });
}

// ==================== FORM VALIDATION ====================
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password && password.length >= 6;
}

// ==================== EXPORT HELPERS ====================
function downloadFile(data, filename, type = 'text/plain') {
    const blob = new Blob([data], { type });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    link.remove();
}

function exportChartAsImage(elementId, filename) {
    Plotly.downloadImage(elementId, {
        format: 'png',
        width: 1200,
        height: 600,
        filename: filename
    });
}

function exportChartAsPDF(elementId, filename) {
    Plotly.downloadImage(elementId, {
        format: 'svg',
        width: 1200,
        height: 600,
        filename: filename
    });
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
});

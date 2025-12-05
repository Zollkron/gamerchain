// PlayerGold Block Explorer - Real-time monitoring and visualization

class BlockExplorer {
    constructor() {
        this.apiUrl = 'http://localhost:5000/api';
        this.wsUrl = 'ws://localhost:5000/ws';
        this.ws = null;
        this.charts = {};
        this.tpsHistory = [];
        this.latencyHistory = [];
        this.maxHistoryPoints = 50;
        
        this.init();
    }

    async init() {
        this.setupWebSocket();
        this.setupCharts();
        this.setupEventListeners();
        await this.loadInitialData();
        this.startAutoRefresh();
    }

    setupWebSocket() {
        this.ws = new WebSocket(this.wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleRealtimeUpdate(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting...');
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }

    setupCharts() {
        // TPS Chart
        const tpsCtx = document.getElementById('tps-chart').getContext('2d');
        this.charts.tps = new Chart(tpsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'TPS (Transacciones por segundo)',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });

        // Node Distribution Chart
        const nodeCtx = document.getElementById('node-distribution-chart').getContext('2d');
        this.charts.nodeDistribution = new Chart(nodeCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    label: 'Distribución de Modelos IA',
                    data: [],
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#4facfe',
                        '#43e97b'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }

    setupEventListeners() {
        document.getElementById('search-btn').addEventListener('click', () => {
            this.performSearch();
        });
        
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.updateNetworkMetrics(),
                this.loadRecentBlocks(),
                this.loadRecentTransactions(),
                this.loadNodeDistribution()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    async updateNetworkMetrics() {
        try {
            const response = await fetch(`${this.apiUrl}/network/metrics`);
            const metrics = await response.json();
            
            document.getElementById('tps').textContent = metrics.tps.toFixed(2);
            document.getElementById('latency').textContent = `${metrics.latency}ms`;
            document.getElementById('active-nodes').textContent = metrics.active_nodes;
            document.getElementById('block-height').textContent = metrics.block_height;
            
            // Update TPS chart
            this.updateTPSChart(metrics.tps);
        } catch (error) {
            console.error('Error updating network metrics:', error);
        }
    }

    updateTPSChart(tps) {
        const now = new Date().toLocaleTimeString();
        
        this.tpsHistory.push({ time: now, value: tps });
        if (this.tpsHistory.length > this.maxHistoryPoints) {
            this.tpsHistory.shift();
        }
        
        this.charts.tps.data.labels = this.tpsHistory.map(h => h.time);
        this.charts.tps.data.datasets[0].data = this.tpsHistory.map(h => h.value);
        this.charts.tps.update('none');
    }

    async loadRecentBlocks() {
        try {
            const response = await fetch(`${this.apiUrl}/blocks/recent?limit=10`);
            const blocks = await response.json();
            
            const tbody = document.getElementById('blocks-tbody');
            tbody.innerHTML = blocks.map(block => `
                <tr>
                    <td>${block.index}</td>
                    <td class="hash-cell">${this.truncateHash(block.hash)}</td>
                    <td>${this.formatTimestamp(block.timestamp)}</td>
                    <td>${block.transactions.length}</td>
                    <td>${block.ai_validators.length}</td>
                    <td><button class="btn-view" onclick="explorer.viewBlock('${block.hash}')">Ver</button></td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Error loading recent blocks:', error);
        }
    }

    async loadRecentTransactions() {
        try {
            const response = await fetch(`${this.apiUrl}/transactions/recent?limit=10`);
            const transactions = await response.json();
            
            const tbody = document.getElementById('transactions-tbody');
            tbody.innerHTML = transactions.map(tx => `
                <tr>
                    <td class="hash-cell">${this.truncateHash(tx.hash)}</td>
                    <td class="hash-cell">${this.truncateHash(tx.from_address)}</td>
                    <td class="hash-cell">${this.truncateHash(tx.to_address)}</td>
                    <td>${tx.amount} $PRGLD</td>
                    <td>${tx.fee} $PRGLD</td>
                    <td><span class="status-badge status-${tx.status}">${tx.status}</span></td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Error loading recent transactions:', error);
        }
    }

    async loadNodeDistribution() {
        try {
            const response = await fetch(`${this.apiUrl}/nodes/distribution`);
            const data = await response.json();
            
            // Update chart
            this.charts.nodeDistribution.data.labels = data.models.map(m => m.name);
            this.charts.nodeDistribution.data.datasets[0].data = data.models.map(m => m.count);
            this.charts.nodeDistribution.update();
            
            // Update nodes list
            const nodesList = document.getElementById('nodes-list');
            nodesList.innerHTML = data.nodes.map(node => `
                <div class="node-card">
                    <h3>🤖 ${node.model_name}</h3>
                    <div class="node-info">
                        <span class="label">ID:</span>
                        <span class="value hash-cell">${this.truncateHash(node.node_id)}</span>
                    </div>
                    <div class="node-info">
                        <span class="label">Validaciones:</span>
                        <span class="value">${node.total_validations}</span>
                    </div>
                    <div class="node-info">
                        <span class="label">Última validación:</span>
                        <span class="value">${this.formatTimestamp(node.last_validation)}</span>
                    </div>
                    <div class="node-info">
                        <span class="label">Reputación:</span>
                        <span class="value">${node.reputation_score.toFixed(2)}</span>
                    </div>
                    <div class="reputation-bar">
                        <div class="reputation-fill" style="width: ${node.reputation_score}%"></div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading node distribution:', error);
        }
    }

    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'new_block':
                this.addNewBlock(data.block);
                break;
            case 'new_transaction':
                this.addNewTransaction(data.transaction);
                break;
            case 'metrics_update':
                this.updateMetricsDisplay(data.metrics);
                break;
            case 'node_update':
                this.updateNodeStatus(data.node);
                break;
        }
    }

    addNewBlock(block) {
        const tbody = document.getElementById('blocks-tbody');
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td>${block.index}</td>
            <td class="hash-cell">${this.truncateHash(block.hash)}</td>
            <td>${this.formatTimestamp(block.timestamp)}</td>
            <td>${block.transactions.length}</td>
            <td>${block.ai_validators.length}</td>
            <td><button class="btn-view" onclick="explorer.viewBlock('${block.hash}')">Ver</button></td>
        `;
        newRow.style.animation = 'fadeIn 0.5s';
        tbody.insertBefore(newRow, tbody.firstChild);
        
        // Remove last row if more than 10
        if (tbody.children.length > 10) {
            tbody.removeChild(tbody.lastChild);
        }
    }

    addNewTransaction(tx) {
        const tbody = document.getElementById('transactions-tbody');
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td class="hash-cell">${this.truncateHash(tx.hash)}</td>
            <td class="hash-cell">${this.truncateHash(tx.from_address)}</td>
            <td class="hash-cell">${this.truncateHash(tx.to_address)}</td>
            <td>${tx.amount} $PRGLD</td>
            <td>${tx.fee} $PRGLD</td>
            <td><span class="status-badge status-${tx.status}">${tx.status}</span></td>
        `;
        newRow.style.animation = 'fadeIn 0.5s';
        tbody.insertBefore(newRow, tbody.firstChild);
        
        if (tbody.children.length > 10) {
            tbody.removeChild(tbody.lastChild);
        }
    }

    updateMetricsDisplay(metrics) {
        document.getElementById('tps').textContent = metrics.tps.toFixed(2);
        document.getElementById('latency').textContent = `${metrics.latency}ms`;
        document.getElementById('active-nodes').textContent = metrics.active_nodes;
        document.getElementById('block-height').textContent = metrics.block_height;
        
        this.updateTPSChart(metrics.tps);
    }

    async performSearch() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) return;
        
        try {
            const response = await fetch(`${this.apiUrl}/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            
            const resultsDiv = document.getElementById('search-results');
            if (results.type === 'block') {
                resultsDiv.innerHTML = this.renderBlockDetails(results.data);
            } else if (results.type === 'transaction') {
                resultsDiv.innerHTML = this.renderTransactionDetails(results.data);
            } else if (results.type === 'address') {
                resultsDiv.innerHTML = this.renderAddressDetails(results.data);
            } else {
                resultsDiv.innerHTML = '<p>No se encontraron resultados</p>';
            }
        } catch (error) {
            console.error('Error performing search:', error);
            document.getElementById('search-results').innerHTML = '<p>Error en la búsqueda</p>';
        }
    }

    renderBlockDetails(block) {
        return `
            <h3>Detalles del Bloque #${block.index}</h3>
            <div class="detail-grid">
                <div><strong>Hash:</strong> ${block.hash}</div>
                <div><strong>Hash Anterior:</strong> ${block.previous_hash}</div>
                <div><strong>Timestamp:</strong> ${this.formatTimestamp(block.timestamp)}</div>
                <div><strong>Transacciones:</strong> ${block.transactions.length}</div>
                <div><strong>Validadores IA:</strong> ${block.ai_validators.join(', ')}</div>
                <div><strong>Merkle Root:</strong> ${block.merkle_root}</div>
            </div>
        `;
    }

    renderTransactionDetails(tx) {
        return `
            <h3>Detalles de la Transacción</h3>
            <div class="detail-grid">
                <div><strong>Hash:</strong> ${tx.hash}</div>
                <div><strong>De:</strong> ${tx.from_address}</div>
                <div><strong>Para:</strong> ${tx.to_address}</div>
                <div><strong>Cantidad:</strong> ${tx.amount} $PRGLD</div>
                <div><strong>Fee:</strong> ${tx.fee} $PRGLD</div>
                <div><strong>Estado:</strong> ${tx.status}</div>
                <div><strong>Timestamp:</strong> ${this.formatTimestamp(tx.timestamp)}</div>
            </div>
        `;
    }

    renderAddressDetails(address) {
        return `
            <h3>Detalles de la Dirección</h3>
            <div class="detail-grid">
                <div><strong>Dirección:</strong> ${address.address}</div>
                <div><strong>Balance:</strong> ${address.balance} $PRGLD</div>
                <div><strong>Transacciones:</strong> ${address.transaction_count}</div>
                <div><strong>Reputación:</strong> ${address.reputation}</div>
            </div>
        `;
    }

    async viewBlock(hash) {
        document.getElementById('search-input').value = hash;
        await this.performSearch();
        window.scrollTo({ top: document.querySelector('.search-section').offsetTop, behavior: 'smooth' });
    }

    startAutoRefresh() {
        // Refresh metrics every 5 seconds
        setInterval(() => {
            this.updateNetworkMetrics();
        }, 5000);
        
        // Refresh blocks and transactions every 10 seconds
        setInterval(() => {
            this.loadRecentBlocks();
            this.loadRecentTransactions();
        }, 10000);
        
        // Refresh node distribution every 30 seconds
        setInterval(() => {
            this.loadNodeDistribution();
        }, 30000);
    }

    truncateHash(hash) {
        if (!hash) return '';
        return `${hash.substring(0, 10)}...${hash.substring(hash.length - 8)}`;
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleString('es-ES');
    }
}

// Initialize explorer when page loads
let explorer;
document.addEventListener('DOMContentLoaded', () => {
    explorer = new BlockExplorer();
});

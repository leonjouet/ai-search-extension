// Popup script for Vinted Fashion Recommender Extension

class FashionSearchPopup {
    constructor() {
        this.backendUrl = 'http://localhost:8000';
        this.maxResults = 5;
        this.isSearching = false;
        
        this.initializeElements();
        this.loadSettings();
        this.checkBackendConnection();
        this.setupEventListeners();
    }
    
    initializeElements() {
        this.searchInput = document.getElementById('searchInput');
        this.searchButton = document.getElementById('searchButton');
        this.loading = document.getElementById('loading');
        this.error = document.getElementById('error');
        this.results = document.getElementById('results');
        this.resultsList = document.getElementById('resultsList');
        this.resultsCount = document.getElementById('resultsCount');
        this.clearResults = document.getElementById('clearResults');
        this.backendUrlInput = document.getElementById('backendUrl');
        this.maxResultsInput = document.getElementById('maxResults');
        this.status = document.getElementById('status');
    }
    
    async loadSettings() {
        try {
            const settings = await chrome.storage.local.get(['backendUrl', 'maxResults']);
            this.backendUrl = settings.backendUrl || 'http://localhost:8000';
            this.maxResults = settings.maxResults || 5;
            
            this.backendUrlInput.value = this.backendUrl;
            this.maxResultsInput.value = this.maxResults;
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    async saveSettings() {
        try {
            await chrome.storage.local.set({
                backendUrl: this.backendUrl,
                maxResults: this.maxResults
            });
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }
    
    setupEventListeners() {
        this.searchButton.addEventListener('click', () => this.performSearch());
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        this.clearResults.addEventListener('click', () => this.clearResults());
        
        this.backendUrlInput.addEventListener('change', (e) => {
            this.backendUrl = e.target.value;
            this.saveSettings();
            this.checkBackendConnection();
        });
        
        this.maxResultsInput.addEventListener('change', (e) => {
            this.maxResults = parseInt(e.target.value);
            this.saveSettings();
        });
    }
    
    async checkBackendConnection() {
        try {
            this.status.textContent = 'Checking connection...';
            this.status.className = 'status';
            
            const response = await fetch(`${this.backendUrl}/api/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.status.textContent = `Connected (${data.total_items} items)`;
                this.status.className = 'status connected';
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.status.textContent = 'Backend not available';
            this.status.className = 'status disconnected';
            console.error('Backend connection failed:', error);
        }
    }
    
    async performSearch() {
        const query = this.searchInput.value.trim();
        
        if (!query) {
            this.showError('Please enter a search query');
            return;
        }
        
        if (this.isSearching) {
            return;
        }
        
        this.isSearching = true;
        this.hideError();
        this.showLoading();
        this.hideResults();
        
        try {
            const response = await fetch(`${this.backendUrl}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    top_k: this.maxResults
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.displayResults(data.results, query);
            
        } catch (error) {
            this.showError(`Search failed: ${error.message}`);
            console.error('Search error:', error);
        } finally {
            this.isSearching = false;
            this.hideLoading();
        }
    }
    
    displayResults(results, query) {
        if (results.length === 0) {
            this.showError('No similar items found. Try a different search term.');
            return;
        }
        
        this.resultsList.innerHTML = '';
        
        results.forEach((result, index) => {
            const resultElement = this.createResultElement(result, index);
            this.resultsList.appendChild(resultElement);
        });
        
        this.resultsCount.textContent = `${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"`;
        this.showResults();
    }
    
    createResultElement(result, index) {
        const div = document.createElement('div');
        div.className = 'result-item';
        div.innerHTML = `
            <div class="result-title">${this.escapeHtml(result.title)}</div>
            <div class="result-price">${result.price ? `${result.price} ${result.currency}` : 'Price not available'}</div>
            <div class="result-similarity">Similarity: ${(result.similarity * 100).toFixed(1)}%</div>
        `;
        
        div.addEventListener('click', () => {
            this.openResult(result);
        });
        
        return div;
    }
    
    openResult(result) {
        // Open the result URL in a new tab
        chrome.tabs.create({ url: result.url });
    }
    
    showLoading() {
        this.loading.style.display = 'block';
        this.searchButton.disabled = true;
        this.searchButton.textContent = 'Searching...';
    }
    
    hideLoading() {
        this.loading.style.display = 'none';
        this.searchButton.disabled = false;
        this.searchButton.textContent = 'Search';
    }
    
    showResults() {
        this.results.style.display = 'block';
    }
    
    hideResults() {
        this.results.style.display = 'none';
    }
    
    showError(message) {
        this.error.textContent = message;
        this.error.style.display = 'block';
    }
    
    hideError() {
        this.error.style.display = 'none';
    }
    
    clearResults() {
        this.hideResults();
        this.hideError();
        this.searchInput.value = '';
        this.resultsList.innerHTML = '';
        this.resultsCount.textContent = '0 results';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FashionSearchPopup();
});

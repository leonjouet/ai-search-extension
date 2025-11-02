// Content script for Vinted Fashion Recommender Extension

class VintedFashionSearch {
    constructor() {
        this.isInitialized = false;
        this.searchOverlay = null;
        this.floatingButton = null;
        this.backendUrl = 'http://localhost:8000';
        
        this.init();
    }
    
    async init() {
        if (this.isInitialized) return;
        
        // Load settings
        await this.loadSettings();
        
        // Create floating search button
        this.createFloatingButton();
        
        // Create search overlay
        this.createSearchOverlay();
        
        this.isInitialized = true;
    }
    
    async loadSettings() {
        try {
            const settings = await chrome.storage.local.get(['backendUrl']);
            this.backendUrl = settings.backendUrl || 'http://localhost:8000';
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    createFloatingButton() {
        // Remove existing button if any
        const existingButton = document.getElementById('vinted-fashion-search-btn');
        if (existingButton) {
            existingButton.remove();
        }
        
        this.floatingButton = document.createElement('div');
        this.floatingButton.id = 'vinted-fashion-search-btn';
        this.floatingButton.innerHTML = `
            <div class="fashion-search-icon">🔍</div>
            <div class="fashion-search-tooltip">AI Fashion Search</div>
        `;
        
        this.floatingButton.addEventListener('click', () => {
            this.toggleSearchOverlay();
        });
        
        document.body.appendChild(this.floatingButton);
    }
    
    createSearchOverlay() {
        // Remove existing overlay if any
        const existingOverlay = document.getElementById('vinted-fashion-search-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        this.searchOverlay = document.createElement('div');
        this.searchOverlay.id = 'vinted-fashion-search-overlay';
        this.searchOverlay.innerHTML = `
            <div class="fashion-search-modal">
                <div class="fashion-search-header">
                    <h3>🔍 AI Fashion Search</h3>
                    <button class="fashion-search-close">&times;</button>
                </div>
                <div class="fashion-search-content">
                    <div class="fashion-search-input-container">
                        <input type="text" id="fashion-search-input" placeholder="Describe what you're looking for..." />
                        <button id="fashion-search-submit">Search</button>
                    </div>
                    <div id="fashion-search-loading" class="fashion-search-loading">
                        <div class="fashion-search-spinner"></div>
                        <div>Searching...</div>
                    </div>
                    <div id="fashion-search-results" class="fashion-search-results"></div>
                    <div id="fashion-search-error" class="fashion-search-error"></div>
                </div>
            </div>
        `;
        
        // Add event listeners
        this.setupOverlayEventListeners();
        
        document.body.appendChild(this.searchOverlay);
    }
    
    setupOverlayEventListeners() {
        const closeBtn = this.searchOverlay.querySelector('.fashion-search-close');
        const searchInput = this.searchOverlay.querySelector('#fashion-search-input');
        const searchSubmit = this.searchOverlay.querySelector('#fashion-search-submit');
        
        closeBtn.addEventListener('click', () => {
            this.hideSearchOverlay();
        });
        
        searchSubmit.addEventListener('click', () => {
            this.performSearch();
        });
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Close on overlay click (but not on modal click)
        this.searchOverlay.addEventListener('click', (e) => {
            if (e.target === this.searchOverlay) {
                this.hideSearchOverlay();
            }
        });
    }
    
    toggleSearchOverlay() {
        if (this.searchOverlay.style.display === 'block') {
            this.hideSearchOverlay();
        } else {
            this.showSearchOverlay();
        }
    }
    
    showSearchOverlay() {
        this.searchOverlay.style.display = 'block';
        const searchInput = this.searchOverlay.querySelector('#fashion-search-input');
        searchInput.focus();
    }
    
    hideSearchOverlay() {
        this.searchOverlay.style.display = 'none';
        this.clearResults();
    }
    
    async performSearch() {
        const searchInput = this.searchOverlay.querySelector('#fashion-search-input');
        const query = searchInput.value.trim();
        
        if (!query) {
            this.showError('Please enter a search query');
            return;
        }
        
        this.showLoading();
        this.hideError();
        this.clearResults();
        
        try {
            const response = await fetch(`${this.backendUrl}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 5
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.displayResults(data.results);
            
        } catch (error) {
            this.showError(`Search failed: ${error.message}`);
            console.error('Search error:', error);
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(results) {
        if (results.length === 0) {
            this.showError('No similar items found. Try a different search term.');
            return;
        }
        
        const resultsContainer = this.searchOverlay.querySelector('#fashion-search-results');
        resultsContainer.innerHTML = '';
        
        results.forEach((result, index) => {
            const resultElement = this.createResultElement(result, index);
            resultsContainer.appendChild(resultElement);
        });
        
        resultsContainer.style.display = 'block';
    }
    
    createResultElement(result, index) {
        const div = document.createElement('div');
        div.className = 'fashion-search-result-item';
        div.innerHTML = `
            <div class="fashion-search-result-image">
                <img src="${result.image_url}" alt="${this.escapeHtml(result.title)}" onerror="this.style.display='none'" />
            </div>
            <div class="fashion-search-result-info">
                <div class="fashion-search-result-title">${this.escapeHtml(result.title)}</div>
                <div class="fashion-search-result-price">${result.price ? `${result.price} ${result.currency}` : 'Price not available'}</div>
                <div class="fashion-search-result-similarity">Similarity: ${(result.similarity * 100).toFixed(1)}%</div>
            </div>
        `;
        
        div.addEventListener('click', () => {
            window.open(result.url, '_blank');
        });
        
        return div;
    }
    
    showLoading() {
        const loading = this.searchOverlay.querySelector('#fashion-search-loading');
        loading.style.display = 'block';
    }
    
    hideLoading() {
        const loading = this.searchOverlay.querySelector('#fashion-search-loading');
        loading.style.display = 'none';
    }
    
    showError(message) {
        const error = this.searchOverlay.querySelector('#fashion-search-error');
        error.textContent = message;
        error.style.display = 'block';
    }
    
    hideError() {
        const error = this.searchOverlay.querySelector('#fashion-search-error');
        error.style.display = 'none';
    }
    
    clearResults() {
        const results = this.searchOverlay.querySelector('#fashion-search-results');
        results.innerHTML = '';
        results.style.display = 'none';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new VintedFashionSearch();
    });
} else {
    new VintedFashionSearch();
}

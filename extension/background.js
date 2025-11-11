// Background service worker for Vinted Fashion Recommender Extension
// const API_BASE_URL = 'http://localhost:8000';

// Alternative production URL (uncomment when deploying)
const API_BASE_URL = 'http://35.180.91.139:8000';
class FashionSearchBackground {
    constructor() {
        this.backendUrl = API_BASE_URL;
        this.isBackendHealthy = false;
        this.lastHealthCheck = 0;
        this.healthCheckInterval = 30000; // 30 seconds
        
        this.init();
    }
    
    async init() {
        // Load settings
        await this.loadSettings();
        
        // Check backend health
        await this.checkBackendHealth();
        
        // Set up periodic health checks
        setInterval(() => {
            this.checkBackendHealth();
        }, this.healthCheckInterval);
        
        // Set up message listeners
        this.setupMessageListeners();
    }
    
    async loadSettings() {
        try {
            const settings = await chrome.storage.local.get(['backendUrl', 'apiKey']);
            this.backendUrl = settings.backendUrl || API_BASE_URL;
            this.cachedApiKey = settings.apiKey || 'dev-secret-key';
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    async saveSettings() {
        try {
            await chrome.storage.local.set({
                backendUrl: this.backendUrl
            });
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }
    
    setupMessageListeners() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep message channel open for async response
        });
    }
    
    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'search':
                    const searchResults = await this.performSearch(request.query, request.topK);
                    sendResponse({ success: true, data: searchResults });
                    break;
                    
                case 'checkHealth':
                    const healthStatus = await this.checkBackendHealth();
                    sendResponse({ success: true, data: healthStatus });
                    break;
                    
                case 'updateSettings':
                    this.backendUrl = request.backendUrl;
                    await this.saveSettings();
                    await this.checkBackendHealth();
                    sendResponse({ success: true });
                    break;
                    
                case 'getStats':
                    const stats = await this.getBackendStats();
                    sendResponse({ success: true, data: stats });
                    break;
                    
                default:
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Error handling message:', error);
            sendResponse({ success: false, error: error.message });
        }
    }
    
    async performSearch(query, topK = 5) {
        try {
            const response = await fetch(`${this.backendUrl}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': this.getApiKey()
                },
                body: JSON.stringify({
                    query: query,
                    top_k: topK
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error('Search error:', error);
            throw error;
        }
    }
    
    async checkBackendHealth() {
        try {
            const response = await fetch(`${this.backendUrl}/api/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': this.getApiKey()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.isBackendHealthy = data.status === 'healthy';
                this.lastHealthCheck = Date.now();
                
                // Update badge
                this.updateBadge(data.total_items || 0);
                
                return {
                    healthy: this.isBackendHealthy,
                    totalItems: data.total_items || 0,
                    timestamp: data.timestamp
                };
            } else {
                this.isBackendHealthy = false;
                this.updateBadge(0);
                return {
                    healthy: false,
                    error: `HTTP ${response.status}`
                };
            }
            
        } catch (error) {
            console.error('Health check failed:', error);
            this.isBackendHealthy = false;
            this.updateBadge(0);
            return {
                healthy: false,
                error: error.message
            };
        }
    }
    
    async getBackendStats() {
        try {
            const response = await fetch(`${this.backendUrl}/api/stats`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': this.getApiKey()
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error('Stats error:', error);
            throw error;
        }
    }
    
    updateBadge(itemCount) {
        try {
            if (this.isBackendHealthy && itemCount > 0) {
                chrome.action.setBadgeText({ text: itemCount.toString() });
                chrome.action.setBadgeBackgroundColor({ color: '#4ade80' });
            } else {
                chrome.action.setBadgeText({ text: '!' });
                chrome.action.setBadgeBackgroundColor({ color: '#ff6b6b' });
            }
        } catch (error) {
            console.error('Error updating badge:', error);
        }
    }
    
    // Handle extension installation/update
    async handleInstall() {
        console.log('Vinted Fashion Recommender Extension installed/updated');
        
        // Set default settings
        await chrome.storage.local.set({
            backendUrl: API_BASE_URL,
            maxResults: 5
        });
        
        // Check backend health
        await this.checkBackendHealth();
    }
}

// Simple API key accessor; could be expanded to load from chrome.storage
FashionSearchBackground.prototype.getApiKey = function() {
    return this.cachedApiKey || 'dev-secret-key';
};

// Initialize background service
const backgroundService = new FashionSearchBackground();

// Handle extension events
chrome.runtime.onInstalled.addListener(() => {
    backgroundService.handleInstall();
});

chrome.runtime.onStartup.addListener(() => {
    backgroundService.init();
});

// Handle tab updates to inject content script on Vinted pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && tab.url.includes('vinted.fr')) {
        // Content script will be automatically injected based on manifest.json
        console.log('Vinted page loaded, content script ready');
    }
});

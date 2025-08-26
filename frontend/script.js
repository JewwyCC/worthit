// Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const searchQuery = document.getElementById('searchQuery');
const playstyleSelect = document.getElementById('playstyle');
const budgetInput = document.getElementById('budget');
const footTypeSelect = document.getElementById('footType');
const injuryConcernsInput = document.getElementById('injuryConcerns');
const searchBtn = document.getElementById('searchBtn');
const toggleAdvancedBtn = document.getElementById('toggleAdvanced');
const advancedOptions = document.getElementById('advancedOptions');
const newSearchBtn = document.getElementById('newSearchBtn');
const retryBtn = document.getElementById('retryBtn');

// Section elements
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Result elements
const confidenceScore = document.getElementById('confidenceScore');
const processingTime = document.getElementById('processingTime');
const searchUsed = document.getElementById('searchUsed');
const reasoningContent = document.getElementById('reasoningContent');
const recommendationsGrid = document.getElementById('recommendationsGrid');
const sourcesList = document.getElementById('sourcesList');
const errorMessage = document.getElementById('errorMessage');
const footerStats = document.getElementById('footerStats');

// State
let currentQuery = null;
let loadingSteps = ['1', '2', '3', '4'];
let currentStep = 0;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    bindEventListeners();
    loadSystemStats();
});

function initializeApp() {
    // Set focus to search query
    searchQuery.focus();
    
    // Add example queries for inspiration
    const examples = [
        "Best basketball shoes for guards under $150 with good cushioning",
        "Shoes for a 6'5\" center with ankle support and wide feet",
        "Lightweight shoes for quick guards with knee injury concerns",
        "Budget-friendly shoes under $100 for outdoor courts",
        "Premium shoes for forwards who play both indoor and outdoor"
    ];
    
    searchQuery.placeholder = examples[Math.floor(Math.random() * examples.length)];
}

function bindEventListeners() {
    // Search functionality
    searchBtn.addEventListener('click', handleSearch);
    searchQuery.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    });
    
    // Advanced options toggle
    toggleAdvancedBtn.addEventListener('click', toggleAdvancedOptions);
    
    // Navigation
    newSearchBtn.addEventListener('click', resetToSearch);
    retryBtn.addEventListener('click', handleRetry);
    
    // Auto-resize textarea
    searchQuery.addEventListener('input', autoResizeTextarea);
}

function autoResizeTextarea() {
    searchQuery.style.height = 'auto';
    searchQuery.style.height = searchQuery.scrollHeight + 'px';
}

function toggleAdvancedOptions() {
    const isVisible = advancedOptions.classList.contains('show');
    
    if (isVisible) {
        advancedOptions.classList.remove('show');
        toggleAdvancedBtn.innerHTML = '<i class="fas fa-sliders-h"></i> Advanced Options';
    } else {
        advancedOptions.classList.add('show');
        toggleAdvancedBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Advanced';
    }
}

async function handleSearch() {
    const query = searchQuery.value.trim();
    
    if (!query) {
        showError('Please enter a search query');
        return;
    }
    
    // Prepare request data
    const requestData = {
        query: query
    };
    
    // Add optional fields if provided
    if (playstyleSelect.value) {
        requestData.playstyle = playstyleSelect.value;
    }
    
    if (budgetInput.value) {
        requestData.budget = parseFloat(budgetInput.value);
    }
    
    if (footTypeSelect.value) {
        requestData.foot_type = footTypeSelect.value;
    }
    
    if (injuryConcernsInput.value) {
        requestData.injury_concerns = injuryConcernsInput.value
            .split(',')
            .map(concern => concern.trim())
            .filter(concern => concern.length > 0);
    }
    
    currentQuery = requestData;
    
    try {
        showLoadingSection();
        startLoadingProgress();
        
        const response = await fetch(`${API_BASE_URL}/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        stopLoadingProgress();
        showResults(data);
        
    } catch (error) {
        stopLoadingProgress();
        showError(`Failed to get recommendations: ${error.message}`);
    }
}

function showLoadingSection() {
    // Hide other sections
    document.querySelector('.search-section').style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Show loading
    loadingSection.style.display = 'block';
    loadingSection.classList.add('fade-in');
}

function startLoadingProgress() {
    currentStep = 0;
    
    // Reset all steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Start progress animation
    const progressInterval = setInterval(() => {
        if (currentStep < loadingSteps.length) {
            const stepElement = document.querySelector(`[data-step="${loadingSteps[currentStep]}"]`);
            if (stepElement) {
                stepElement.classList.add('active');
            }
            currentStep++;
        } else {
            clearInterval(progressInterval);
        }
    }, 800);
    
    // Store interval for cleanup
    window.loadingInterval = progressInterval;
}

function stopLoadingProgress() {
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
    }
    
    // Complete all steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.add('active');
    });
}

function showResults(data) {
    // Hide other sections
    loadingSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Populate results
    populateResultsMeta(data);
    populateReasoning(data.reasoning);
    populateRecommendations(data.recommendations);
    populateSources(data.sources);
    
    // Show results
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function populateResultsMeta(data) {
    confidenceScore.textContent = `Confidence: ${Math.round(data.confidence_score * 100)}%`;
    processingTime.textContent = `Processing: ${data.processing_time.toFixed(2)}s`;
    searchUsed.textContent = data.search_used ? 'Web Search: Used' : 'Web Search: Not Used';
    
    // Color code confidence
    const confidence = data.confidence_score * 100;
    if (confidence >= 80) {
        confidenceScore.style.background = 'var(--success-green)';
    } else if (confidence >= 60) {
        confidenceScore.style.background = 'var(--accent-yellow)';
        confidenceScore.style.color = 'var(--dark-gray)';
    } else {
        confidenceScore.style.background = 'var(--error-red)';
    }
}

function populateReasoning(reasoning) {
    reasoningContent.textContent = reasoning;
}

function populateRecommendations(recommendations) {
    recommendationsGrid.innerHTML = '';
    
    if (!recommendations || recommendations.length === 0) {
        recommendationsGrid.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No recommendations found</h3>
                <p>Try adjusting your search criteria or check back later.</p>
            </div>
        `;
        return;
    }
    
    recommendations.forEach((rec, index) => {
        const card = createRecommendationCard(rec, index);
        recommendationsGrid.appendChild(card);
    });
}

function createRecommendationCard(rec, index) {
    const card = document.createElement('div');
    card.className = 'recommendation-card fade-in';
    card.style.animationDelay = `${index * 0.1}s`;
    
    const prosHtml = rec.pros && rec.pros.length > 0 
        ? rec.pros.map(pro => `<li>${pro}</li>`).join('')
        : '<li>No specific pros listed</li>';
    
    const consHtml = rec.cons && rec.cons.length > 0 
        ? rec.cons.map(con => `<li>${con}</li>`).join('')
        : '<li>No specific cons listed</li>';
    
    const playstyleText = rec.playstyle && rec.playstyle.length > 0 
        ? rec.playstyle.join(', ')
        : 'All Styles';
    
    const priceText = rec.price_range && rec.price_range.length === 2 
        ? `$${rec.price_range[0]} - $${rec.price_range[1]}`
        : 'Price not available';
    
    const featuresText = rec.features && rec.features.length > 0 
        ? rec.features.slice(0, 3).join(', ')
        : 'No features listed';
    
    card.innerHTML = `
        <div class="card-header">
            <div class="shoe-title">
                <h3>${rec.shoe_model || 'Unknown Model'}</h3>
                <span class="source">${rec.source || 'Unknown Source'}</span>
            </div>
            ${rec.score ? `<div class="score-badge">${rec.score}/10</div>` : ''}
        </div>
        
        <div class="card-content">
            ${rec.title ? `<p class="review-title">${rec.title}</p>` : ''}
            
            <div class="pros-cons">
                <div class="pros">
                    <h4><i class="fas fa-thumbs-up"></i> Pros</h4>
                    <ul>${prosHtml}</ul>
                </div>
                <div class="cons">
                    <h4><i class="fas fa-thumbs-down"></i> Cons</h4>
                    <ul>${consHtml}</ul>
                </div>
            </div>
            
            <div class="card-details">
                <div class="detail-item">
                    <div class="label">Best For</div>
                    <div class="value">${playstyleText}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Price Range</div>
                    <div class="value">${priceText}</div>
                </div>
                <div class="detail-item">
                    <div class="label">Key Features</div>
                    <div class="value">${featuresText}</div>
                </div>
            </div>
        </div>
        
        <div class="card-footer">
            ${rec.url ? `
                <a href="${rec.url}" target="_blank" rel="noopener noreferrer" class="view-source">
                    <i class="fas fa-external-link-alt"></i> View Source
                </a>
            ` : '<span></span>'}
        </div>
    `;
    
    return card;
}

function populateSources(sources) {
    sourcesList.innerHTML = '';
    
    if (!sources || sources.length === 0) {
        sourcesList.innerHTML = '<p>No sources available</p>';
        return;
    }
    
    sources.forEach((source, index) => {
        const sourceElement = document.createElement('a');
        sourceElement.href = source;
        sourceElement.target = '_blank';
        sourceElement.rel = 'noopener noreferrer';
        sourceElement.className = 'source-link fade-in';
        sourceElement.style.animationDelay = `${index * 0.1}s`;
        
        sourceElement.innerHTML = `
            <i class="fas fa-link"></i>
            <span>${formatUrl(source)}</span>
            <i class="fas fa-external-link-alt"></i>
        `;
        
        sourcesList.appendChild(sourceElement);
    });
}

function formatUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.hostname + (urlObj.pathname !== '/' ? urlObj.pathname : '');
    } catch {
        return url;
    }
}

function showError(message) {
    // Hide other sections
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    
    // Show error
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    errorSection.classList.add('fade-in');
}

function resetToSearch() {
    // Show search section
    document.querySelector('.search-section').style.display = 'block';
    
    // Hide other sections
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Focus search input
    searchQuery.focus();
}

function handleRetry() {
    if (currentQuery) {
        resetToSearch();
        // Auto-trigger search with the last query
        setTimeout(() => {
            handleSearch();
        }, 300);
    } else {
        resetToSearch();
    }
}

async function loadSystemStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        
        if (response.ok) {
            const stats = await response.json();
            const totalDocs = stats.vector_db?.total_documents || 0;
            const cacheSize = stats.web_search?.cache_size || 0;
            const knownModels = stats.router?.known_models || 0;
            
            footerStats.innerHTML = `
                📚 ${totalDocs.toLocaleString()} documents • 
                🔍 ${cacheSize} cached searches • 
                👟 ${knownModels} known models
            `;
        } else {
            footerStats.textContent = 'System stats unavailable';
        }
    } catch (error) {
        footerStats.textContent = 'System stats unavailable';
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add some keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to search
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (loadingSection.style.display === 'none' && errorSection.style.display === 'none') {
            handleSearch();
        }
    }
    
    // Escape to go back to search
    if (e.key === 'Escape') {
        if (resultsSection.style.display === 'block' || errorSection.style.display === 'block') {
            resetToSearch();
        }
    }
});

// Handle offline/online status
window.addEventListener('online', function() {
    if (errorSection.style.display === 'block') {
        showError('Connection restored. You can try your search again.');
    }
});

window.addEventListener('offline', function() {
    showError('Connection lost. Please check your internet connection and try again.');
});

// Add loading state to search button
function setSearchButtonLoading(loading) {
    if (loading) {
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
    } else {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fas fa-magic"></i> Get Recommendations';
    }
}

// Enhanced error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showError('An unexpected error occurred. Please refresh the page and try again.');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showError('An unexpected error occurred. Please refresh the page and try again.');
});

// Performance monitoring
const performanceObserver = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
            console.log(`Page load time: ${entry.loadEventEnd - entry.loadEventStart}ms`);
        }
    }
});

if ('PerformanceObserver' in window) {
    performanceObserver.observe({ entryTypes: ['navigation'] });
} 
// RAG-YouTube Frontend Application

const API_BASE = '/api';

// DOM Elements
const questionForm = document.getElementById('question-form');
const questionInput = document.getElementById('question-input');
const submitBtn = document.getElementById('submit-btn');
const streamCheckbox = document.getElementById('stream-checkbox');
const numSourcesSelect = document.getElementById('num-sources');
const resultsSection = document.getElementById('results-section');
const answerContent = document.getElementById('answer-content');
const sourcesList = document.getElementById('sources-list');
const processingTime = document.getElementById('processing-time');
const examplesSection = document.getElementById('examples-section');
const statsContainer = document.getElementById('stats-docs');
const darkModeToggle = document.getElementById('dark-mode-toggle');
const requireCaptionsCheckbox = document.getElementById('require-captions-checkbox');
const captionCoverage = document.getElementById('caption-coverage');
const categoryFilter = document.getElementById('category-filter');
const categoryCount = document.getElementById('category-count');
const qualityFilter = document.getElementById('quality-filter');
const qualityCount = document.getElementById('quality-count');
const dateFrom = document.getElementById('date-from');
const dateTo = document.getElementById('date-to');
const dateRangeInfo = document.getElementById('date-range-info');
const clearFiltersBtn = document.getElementById('clear-filters-btn');

// State
let isProcessing = false;
let currentEventSource = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadFilterOptions();
    setupEventListeners();
    initDarkMode();
});

// Load system stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        statsContainer.textContent = `${stats.total_documents.toLocaleString()} documents indexed | Model: ${stats.model}`;
    } catch (error) {
        statsContainer.textContent = 'Unable to load stats';
    }
}

// Load filter options
async function loadFilterOptions() {
    try {
        const response = await fetch(`${API_BASE}/filters/options`);
        const filterData = await response.json();
        
        // Update caption coverage display
        const coverage = filterData.caption_coverage;
        captionCoverage.textContent = `(${coverage.with_captions}/${filterData.total_documents} videos)`;
        
        // Update category counts
        updateFilterCounts(categoryFilter, categoryCount, filterData.categories);
        
        // Update quality counts
        updateFilterCounts(qualityFilter, qualityCount, filterData.quality_levels);
        
        // Update date range info
        if (filterData.date_range.earliest && filterData.date_range.latest) {
            dateRangeInfo.textContent = `(${formatDate(filterData.date_range.earliest)} - ${formatDate(filterData.date_range.latest)})`;
        }
        
    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}

// Helper function to update filter counts
function updateFilterCounts(selectElement, countElement, countData) {
    const selectedValue = selectElement.value;
    if (selectedValue && countData[selectedValue] !== undefined) {
        countElement.textContent = `(${countData[selectedValue]} videos)`;
    } else {
        // Show total for "All" option
        const total = Object.values(countData).reduce((sum, count) => sum + count, 0);
        countElement.textContent = `(${total} total)`;
    }
}

// Helper function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Setup event listeners
function setupEventListeners() {
    questionForm.addEventListener('submit', handleSubmit);
    darkModeToggle.addEventListener('click', toggleDarkMode);
    
    // Example questions
    document.querySelectorAll('.example-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            questionInput.value = e.target.textContent;
            questionInput.focus();
        });
    });
    
    // Filter change listeners
    requireCaptionsCheckbox.addEventListener('change', updateFilterDisplay);
    categoryFilter.addEventListener('change', updateFilterDisplay);
    qualityFilter.addEventListener('change', updateFilterDisplay);
    dateFrom.addEventListener('change', updateFilterDisplay);
    dateTo.addEventListener('change', updateFilterDisplay);
    
    // Clear filters button
    clearFiltersBtn.addEventListener('click', clearAllFilters);
}

// Update filter display and show/hide clear button
function updateFilterDisplay() {
    // Update counts when filters change
    loadFilterOptions();
    
    // Show/hide clear filters button
    const hasActiveFilters = requireCaptionsCheckbox.checked || 
                           categoryFilter.value || 
                           qualityFilter.value || 
                           dateFrom.value || 
                           dateTo.value;
    
    clearFiltersBtn.style.display = hasActiveFilters ? 'block' : 'none';
}

// Clear all filters
function clearAllFilters() {
    requireCaptionsCheckbox.checked = false;
    categoryFilter.value = '';
    qualityFilter.value = '';
    dateFrom.value = '';
    dateTo.value = '';
    updateFilterDisplay();
}

// Build filters object from UI state
function buildFilters() {
    const filters = {};
    
    if (requireCaptionsCheckbox.checked) {
        filters.require_captions = true;
    }
    
    if (categoryFilter.value) {
        filters.categories = [categoryFilter.value];
    }
    
    if (qualityFilter.value) {
        filters.quality_levels = [qualityFilter.value];
    }
    
    if (dateFrom.value) {
        filters.date_from = dateFrom.value;
    }
    
    if (dateTo.value) {
        filters.date_to = dateTo.value;
    }
    
    return Object.keys(filters).length > 0 ? filters : null;
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    if (isProcessing) return;
    
    const question = questionInput.value.trim();
    if (!question) return;
    
    const useStreaming = streamCheckbox.checked;
    const numSources = parseInt(numSourcesSelect.value);
    
    // Update UI
    setProcessing(true);
    showResults();
    clearResults();
    
    try {
        if (useStreaming) {
            await askQuestionStream(question, numSources);
        } else {
            await askQuestion(question, numSources);
        }
    } catch (error) {
        showError(error.message);
    } finally {
        setProcessing(false);
    }
}

// Regular question (non-streaming)
async function askQuestion(question, numSources) {
    const startTime = Date.now();
    
    // Build filters object
    const filters = buildFilters();
    
    const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: question,
            num_sources: numSources,
            search_type: 'similarity',
            temperature: 0.7,
            stream: false,
            filters: filters
        })
    });
    
    if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Display answer with markdown rendering
    answerContent.innerHTML = marked.parse(data.answer);
    
    // Display sources
    displaySources(data.sources);
    
    // Display processing time
    const elapsed = (Date.now() - startTime) / 1000;
    processingTime.textContent = `Processed in ${elapsed.toFixed(2)} seconds`;
}

// Streaming question
async function askQuestionStream(question, numSources) {
    const startTime = Date.now();
    
    // Close existing connection if any
    if (currentEventSource) {
        currentEventSource.close();
    }
    
    // Build filters object
    const filters = buildFilters();
    
    // Create EventSource for streaming
    const body = JSON.stringify({
        question: question,
        num_sources: numSources,
        search_type: 'similarity',
        temperature: 0.7,
        stream: true,
        filters: Object.keys(filters).length > 0 ? filters : null
    });
    
    const response = await fetch(`${API_BASE}/ask/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: body
    });
    
    if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let sources = [];
    let answerText = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete events
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    
                    switch (data.type) {
                        case 'source':
                            const sourceData = JSON.parse(data.content);
                            sources.push(sourceData);
                            break;
                            
                        case 'token':
                            answerText += data.content;
                            answerContent.innerHTML = marked.parse(answerText);
                            break;
                            
                        case 'done':
                            // Display sources
                            displaySources(sources);
                            
                            // Display processing time
                            const elapsed = (Date.now() - startTime) / 1000;
                            processingTime.textContent = `Processed in ${elapsed.toFixed(2)} seconds`;
                            break;
                            
                        case 'error':
                            throw new Error(data.content);
                    }
                } catch (error) {
                    console.error('Error parsing stream data:', error);
                }
            }
        }
    }
}

// Display sources
function displaySources(sources) {
    sourcesList.innerHTML = '';
    
    sources.forEach((source, index) => {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'source-item';
        
        const title = source.metadata?.title || `Source ${index + 1}`;
        const url = source.metadata?.url || '#';
        const score = (source.score * 100).toFixed(1);
        
        sourceDiv.innerHTML = `
            <div class="source-header">
                <a href="${url}" target="_blank" class="source-title">${title}</a>
                <span class="source-score">${score}% match</span>
            </div>
            <div class="source-content">${source.content}</div>
        `;
        
        sourcesList.appendChild(sourceDiv);
    });
}

// UI Helper Functions
function setProcessing(processing) {
    isProcessing = processing;
    submitBtn.disabled = processing;
    
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    
    if (processing) {
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline';
        answerContent.classList.add('loading');
    } else {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        answerContent.classList.remove('loading');
    }
}

function showResults() {
    resultsSection.style.display = 'block';
    examplesSection.style.display = 'none';
}

function clearResults() {
    answerContent.innerHTML = '<em>Thinking...</em>';
    sourcesList.innerHTML = '';
    processingTime.textContent = '';
}

function showError(message) {
    answerContent.textContent = `Error: ${message}`;
    answerContent.style.color = 'var(--error-color)';
    setTimeout(() => {
        answerContent.style.color = '';
    }, 3000);
}

// Dark Mode Functions
function initDarkMode() {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (prefersDark) {
        setTheme('dark');
    } else {
        setTheme('light');
    }
}

function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update toggle icon
    const toggleIcon = darkModeToggle.querySelector('.toggle-icon');
    if (theme === 'dark') {
        toggleIcon.textContent = '☀️';
        darkModeToggle.setAttribute('title', 'Switch to light mode');
    } else {
        toggleIcon.textContent = '🌙';
        darkModeToggle.setAttribute('title', 'Switch to dark mode');
    }
}
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

// State
let isProcessing = false;
let currentEventSource = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    setupEventListeners();
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

// Setup event listeners
function setupEventListeners() {
    questionForm.addEventListener('submit', handleSubmit);
    
    // Example questions
    document.querySelectorAll('.example-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            questionInput.value = e.target.textContent;
            questionInput.focus();
        });
    });
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
            stream: false
        })
    });
    
    if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Display answer
    answerContent.textContent = data.answer;
    
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
    
    // Create EventSource for streaming
    const body = JSON.stringify({
        question: question,
        num_sources: numSources,
        search_type: 'similarity',
        temperature: 0.7,
        stream: true
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
                            answerContent.textContent = answerText;
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
    answerContent.textContent = 'Thinking...';
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
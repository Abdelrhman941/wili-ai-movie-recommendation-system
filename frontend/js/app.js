// Protect this page
protectPage();

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    const username = localStorage.getItem('username');
    document.getElementById('usernameDisplay').textContent = username || 'User';
    
    // Setup form handlers
    document.getElementById('wiliForm').addEventListener('submit', handleWiliCheck);
    document.getElementById('recommendationsForm').addEventListener('submit', handleRecommendations);
});

// Switch between tabs
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    if (tabName === 'wili') {
        document.getElementById('wiliTab').classList.add('active');
        document.querySelectorAll('.tab')[0].classList.add('active');
    } else {
        document.getElementById('recommendationsTab').classList.add('active');
        document.querySelectorAll('.tab')[1].classList.add('active');
    }
}

// Handle Wili check (Use Case A)
async function handleWiliCheck(e) {
    e.preventDefault();
    
    const movieTitle = document.getElementById('movieTitle').value;
    showLoading(true);
    clearResult('wiliResult');
    
    try {
        const response = await fetch(`${API_URL}/wili/check`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ movie_title: movieTitle })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to check movie');
        }
        
        displayWiliResult(data);
        
    } catch (error) {
        showAlert(error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Display Wili result
function displayWiliResult(data) {
    const resultDiv = document.getElementById('wiliResult');
    
    const likelihoodColor = data.likelihood >= 70 ? '#4caf50' : 
                           data.likelihood >= 50 ? '#ff9800' : '#f44336';
    
    const recommendation = data.likelihood >= 70 ? '👍 You\'ll likely love this!' :
                          data.likelihood >= 50 ? '🤔 You might like this' : 
                          '👎 Probably not your style';
    
    // ✅ FIXED: Extract year from release_date (handles both integers and strings)
    let year = 'N/A';
    if (data.movie_info.release_date) {
        // If it's a number, just use it directly
        if (typeof data.movie_info.release_date === 'number') {
            year = data.movie_info.release_date;
        } 
        // If it's a string, try to extract the year
        else if (typeof data.movie_info.release_date === 'string') {
            // Check if it's just a year (e.g., "1950")
            if (/^\d{4}$/.test(data.movie_info.release_date)) {
                year = data.movie_info.release_date;
            } 
            // Otherwise try to extract from date string (e.g., "1950-01-01")
            else {
                year = data.movie_info.release_date.split('-')[0];
            }
        }
    }
    
    resultDiv.innerHTML = `
        <div class="result-card">
            <h3>${data.movie_title}</h3>
            <div class="score" style="color: ${likelihoodColor}">
                ${data.likelihood}% Match
            </div>
            <p style="font-size: 1.2em; margin: 15px 0;">
                ${recommendation}
            </p>
            <div class="movie-info">
                <div class="movie-info-item">
                    <strong>Genre:</strong> ${data.movie_info.genre || 'N/A'}
                </div>
                <div class="movie-info-item">
                    <strong>Rating:</strong> ${data.movie_info.rating || 'N/A'}/10
                </div>
                <div class="movie-info-item">
                    <strong>Year:</strong> ${year}
                </div>
                <div class="movie-info-item">
                    <strong>Runtime:</strong> ${data.movie_info.runtime_min || 'N/A'} min
                </div>
            </div>
        </div>
    `;
}

// Handle recommendations (Use Case B)
async function handleRecommendations(e) {
    e.preventDefault();
    
    const prompt = document.getElementById('prompt').value;
    const minRating = document.getElementById('minRating').value;
    const minYear = document.getElementById('minYear').value;
    const genre = document.getElementById('genre').value;
    
    showLoading(true);
    clearResult('recommendationsResult');
    
    try {
        const body = { prompt };
        if (minRating) body.min_rating = parseFloat(minRating);
        if (minYear) body.min_release_date = minYear;
        if (genre) body.genre = genre;
        
        const response = await fetch(`${API_URL}/recommendations`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to get recommendations');
        }
        
        displayRecommendations(data.recommendations);
        
    } catch (error) {
        showAlert(error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Display recommendations
function displayRecommendations(recommendations) {
    const resultDiv = document.getElementById('recommendationsResult');
    
    if (!recommendations || recommendations.length === 0) {
        resultDiv.innerHTML = '<p>No recommendations found. Try adjusting your filters.</p>';
        return;
    }
    
    let html = '<h3 style="margin-top: 30px; margin-bottom: 20px;">Top Recommendations:</h3>';
    
    recommendations.forEach((rec, index) => {
        // ✅ FIXED: Extract year from release_date (handles both integers and strings)
        let year = 'N/A';
        if (rec.movie_info.release_date) {
            // If it's a number, just use it directly
            if (typeof rec.movie_info.release_date === 'number') {
                year = rec.movie_info.release_date;
            } 
            // If it's a string, try to extract the year
            else if (typeof rec.movie_info.release_date === 'string') {
                // Check if it's just a year (e.g., "1950")
                if (/^\d{4}$/.test(rec.movie_info.release_date)) {
                    year = rec.movie_info.release_date;
                } 
                // Otherwise try to extract from date string (e.g., "1950-01-01")
                else {
                    year = rec.movie_info.release_date.split('-')[0];
                }
            }
        }
        
        html += `
            <div class="result-card">
                <h3>${index + 1}. ${rec.movie_title}</h3>
                <div class="score">
                    ${rec.similarity_score}% Match
                </div>
                
                <div class="movie-info">
                    <div class="movie-info-item">
                        <strong>Genre:</strong> ${rec.movie_info.genre || 'N/A'}
                    </div>
                    <div class="movie-info-item">
                        <strong>Rating:</strong> ${rec.movie_info.rating || 'N/A'}/10
                    </div>
                    <div class="movie-info-item">
                        <strong>Year:</strong> ${year}
                    </div>
                    <div class="movie-info-item">
                        <strong>Runtime:</strong> ${rec.movie_info.runtime_min || 'N/A'} min
                    </div>
                </div>
                
                <div class="explanation">
                    <strong>Why this movie?</strong><br>
                    ${rec.explanation}
                </div>
            </div>
        `;
    });
    
    resultDiv.innerHTML = html;
}

// Show/hide loading
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// Clear result
function clearResult(elementId) {
    document.getElementById(elementId).innerHTML = '';
}

// Show alert
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert alert-${type} show`;
    
    setTimeout(() => {
        alert.className = 'alert';
    }, 5000);
}
// Remove this line: const API_URL = 'http://localhost:5000/api';
const TOTAL_REQUIRED = 10;

let selectedMovies = [];
let excludedMovies = [];
let currentMovies = [];

// Protect this page
protectPage();

// Initialize survey
document.addEventListener('DOMContentLoaded', () => {
    loadNextMovies();
});

// Load next set of movies
async function loadNextMovies() {
    showLoading(true);
    
    try {
        const excludeParam = [...excludedMovies, ...selectedMovies.map(m => m.movie_id)].join(',');
        const response = await fetch(`${API_URL}/survey/movies?exclude=${excludeParam}`, {
            headers: getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load movies');
        }
        
        currentMovies = data.movies;
        renderMovies(currentMovies);
        
        // Add current movies to excluded list
        excludedMovies.push(...currentMovies.map(m => m.movie_id));
        
    } catch (error) {
        showAlert(error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Render movies in grid
function renderMovies(movies) {
    const grid = document.getElementById('moviesGrid');
    grid.innerHTML = '';
    
    movies.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.onclick = () => toggleMovie(movie, card);
        
        // Safely extract year from release_date
        let year = 'N/A';
        if (movie.release_date) {
            if (typeof movie.release_date === 'string') {
                year = movie.release_date.split('-')[0];
            } else if (movie.release_date instanceof Date) {
                year = movie.release_date.getFullYear();
            } else if (typeof movie.release_date === 'number') {
                year = movie.release_date;
            }
        }
        
        card.innerHTML = `
            <h3>${movie.title}</h3>
            <p><strong>Genre:</strong> ${movie.genre || 'N/A'}</p>
            <p><strong>Rating:</strong> ${movie.rating || 'N/A'}</p>
            <p><strong>Year:</strong> ${year}</p>
        `;
        
        grid.appendChild(card);
    });
}
// Toggle movie selection
function toggleMovie(movie, cardElement) {
    const index = selectedMovies.findIndex(m => m.movie_id === movie.movie_id);
    
    if (index > -1) {
        // Deselect
        selectedMovies.splice(index, 1);
        cardElement.classList.remove('selected');
    } else {
        // Select (if under limit)
        if (selectedMovies.length < TOTAL_REQUIRED) {
            selectedMovies.push(movie);
            cardElement.classList.add('selected');
        } else {
            showAlert(`You can only select ${TOTAL_REQUIRED} movies`, 'error');
        }
    }
    
    updateProgress();
}

// Update progress bar
function updateProgress() {
    const count = selectedMovies.length;
    const percentage = (count / TOTAL_REQUIRED) * 100;
    
    document.getElementById('selectedCount').textContent = count;
    document.getElementById('progressFill').style.width = `${percentage}%`;
    document.getElementById('progressFill').textContent = `${Math.round(percentage)}%`;
    
    // Enable submit button when exactly 10 movies selected
    document.getElementById('submitBtn').disabled = count !== TOTAL_REQUIRED;
}

// Submit survey
async function submitSurvey() {
    if (selectedMovies.length !== TOTAL_REQUIRED) {
        showAlert(`Please select exactly ${TOTAL_REQUIRED} movies`, 'error');
        return;
    }
    
    // Confirm submission
    if (!confirm(`You've selected ${TOTAL_REQUIRED} movies. Submit survey and compute your preferences?`)) {
        return;
    }
    
    showProcessing(true);
    
    try {
        const response = await fetch(`${API_URL}/survey/submit`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                movie_ids: selectedMovies.map(m => m.movie_id)
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to submit survey');
        }
        
        showAlert('Survey completed successfully! Redirecting to dashboard...', 'success');
        
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 2000);
        
    } catch (error) {
        showAlert(error.message, 'error');
        showProcessing(false);
    }
}

// Show/hide loading
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
    document.getElementById('surveyContent').style.display = show ? 'none' : 'block';
}

// Show/hide processing
function showProcessing(show) {
    document.getElementById('processingEmbedding').style.display = show ? 'block' : 'none';
    document.getElementById('surveyContent').style.display = show ? 'none' : 'block';
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
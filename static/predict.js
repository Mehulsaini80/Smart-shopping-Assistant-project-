// Get DOM elements
const form = document.getElementById('predictionForm');
const resultsSection = document.getElementById('resultsSection');
const discountValue = document.getElementById('discountValue');
const platformBadge = document.getElementById('platformBadge');
const confidenceValue = document.getElementById('confidenceValue');
const originalPrice = document.getElementById('originalPrice');
const discountedPrice = document.getElementById('discountedPrice');
const savingsAmount = document.getElementById('savingsAmount');
const recommendationsList = document.getElementById('recommendationsList');
const modelName = document.getElementById('modelName');
const predictBtn = document.getElementById('predictBtn');

// Create error message element on page load
let errorDiv = document.createElement('div');
errorDiv.className = 'error-message';
errorDiv.style.display = 'none';
form.parentNode.insertBefore(errorDiv, form.nextSibling);

// Show error message
function showError(message) {
  errorDiv.textContent = '❌ ' + message;
  errorDiv.style.display = 'block';
  
  // Auto-hide after 8 seconds
  setTimeout(() => {
    errorDiv.style.display = 'none';
  }, 8000);
}

// Hide error message
function hideError() {
  errorDiv.style.display = 'none';
}

// Smooth scroll to results
function scrollToResults() {
  const offset = 80; // Account for fixed navbar
  const elementPosition = resultsSection.getBoundingClientRect().top;
  const offsetPosition = elementPosition + window.pageYOffset - offset;

  window.scrollTo({
    top: offsetPosition,
    behavior: 'smooth'
  });
}

// Form submission
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Hide any previous errors
  hideError();

  // Disable button and show loading
  predictBtn.disabled = true;
  predictBtn.innerHTML = '<span class="spinner"></span> <span>Analyzing...</span>';

  const formData = {
    category: document.getElementById('category').value,
    budget: parseFloat(document.getElementById('budget').value),
    platform: document.getElementById('platform').value || null
  };

  console.log('📄 Sending prediction request:', formData);

  try {
    const response = await fetch('/api/predict', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(formData)
    });

    console.log('📡 Response status:', response.status);

    // Check if response is ok
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Server error:', errorText);
      throw new Error(`Server returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Response data:', data);

    if (data.success) {
      // Show results section first
      resultsSection.style.display = 'block';
      
      // Update discount
      discountValue.textContent = data.predicted_discount + '%';
      
      // Update platform
      platformBadge.textContent = data.best_platform;
      confidenceValue.textContent = data.platform_confidence + '%';
      
      // Update prices
      originalPrice.textContent = data.estimated_price.toFixed(2);
      discountedPrice.textContent = data.discounted_price.toFixed(2);
      savingsAmount.textContent = data.savings.toFixed(2);
      
      // Update model name
      modelName.textContent = data.model_used || 'ML Model';
      
      // Update recommendations
      recommendationsList.innerHTML = '';
      if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach(item => {
          const li = document.createElement('li');
          li.textContent = item;
          recommendationsList.appendChild(li);
        });
      }
      
      // Scroll to results after a delay
      setTimeout(() => {
        scrollToResults();
      }, 400);
      
    } else {
      // Show error from API
      showError(data.error || 'Prediction failed. Please try again.');
    }
    
  } catch (err) {
    console.error('❌ Fetch error:', err);
    
    // User-friendly error messages
    let errorMessage = '';
    
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      errorMessage = 'Cannot connect to server. Please ensure Flask is running on http://localhost:5000';
    } else if (err.message.includes('500')) {
      errorMessage = 'Server error. Please check if models are loaded correctly.';
    } else if (err.message.includes('404')) {
      errorMessage = 'API endpoint not found. Please check your Flask routes.';
    } else {
      errorMessage = 'An error occurred: ' + err.message;
    }
    
    showError(errorMessage);
    
  } finally {
    // Re-enable button
    predictBtn.disabled = false;
    predictBtn.innerHTML = '<i class="fas fa-search"></i> <span>Find Best Deals</span>';
  }
});
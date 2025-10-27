// ===== CONTACT FORM HANDLING =====
const contactForm = document.getElementById('contactForm');
const successMessage = document.getElementById('successMessage');

if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        console.log('Contact form submitted'); // Debug log

        // Get form data
        const formData = {
            name: document.getElementById('name').value.trim(),
            email: document.getElementById('email').value.trim(),
            message: document.getElementById('message').value.trim() 
        };

        console.log('Contact form data:', formData); // Debug log

        // Validate email
        if (!validateEmail(formData.email)) {
            if (typeof showNotification === 'function') {
                showNotification('Please enter a valid email address', 'error');
            } else {
                alert('Please enter a valid email address');
            }
            return;
        }

        // Show loading state
        const submitBtn = contactForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            console.log('Contact response status:', response.status); // Debug log

            const data = await response.json();
            console.log('Contact response data:', data); // Debug log

            if (data.success) {
                // Hide form and show success message
                contactForm.style.display = 'none';
                if (successMessage) {
                    successMessage.style.display = 'block';
                }
                
                if (typeof showNotification === 'function') {
                    showNotification('Message sent successfully!', 'success');
                }

                // Reset form after 3 seconds
                setTimeout(() => {
                    contactForm.style.display = 'block';
                    if (successMessage) {
                        successMessage.style.display = 'none';
                    }
                    contactForm.reset();
                }, 3000);
            } else {
                if (typeof showNotification === 'function') {
                    showNotification(data.error || 'Failed to send message. Please try again.', 'error');
                } else {
                    alert(data.error || 'Failed to send message. Please try again.');
                }
            }
        } catch (error) {
            console.error('Contact form error:', error); // Debug log
            
            if (typeof showNotification === 'function') {
                showNotification('An error occurred. Please try again later.', 'error');
            } else {
                alert('An error occurred. Please try again later.');
            }
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });
}

// ===== EMAIL VALIDATION =====
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ===== SHOW NOTIFICATION (Fallback) =====
if (typeof showNotification !== 'function') {
    window.showNotification = function(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <i class="fas fa-times notification-close"></i>
        `;
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
        `;
        document.body.appendChild(notification);

        // Close notification on click
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => notification.remove());
        }

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    };
}

// ===== FAQ TOGGLE =====
const faqItems = document.querySelectorAll('.faq-item');
if (faqItems.length > 0) {
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', () => {
                // Close all other FAQs
                faqItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove('active');
                        const otherAnswer = otherItem.querySelector('.faq-answer');
                        if (otherAnswer) {
                            otherAnswer.style.maxHeight = '0';
                        }
                    }
                });

                // Toggle current FAQ
                item.classList.toggle('active');
                const answer = item.querySelector('.faq-answer');
                if (answer) {
                    if (item.classList.contains('active')) {
                        answer.style.maxHeight = answer.scrollHeight + 'px';
                    } else {
                        answer.style.maxHeight = '0';
                    }
                }
            });
        }
    });
}

console.log('contact.js loaded successfully'); // Debug log
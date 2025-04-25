// Initialize the TrulyFAQ client with your API key
// Replace 'YOUR_API_KEY' with an actual API key from your TrulyFAQ dashboard
const API_KEY = 'sa6jLkSvcVPdLz1T1Q5DQQL8wmjupqGCmxGWvEaWPTuW2QEi0adhryOYHanawfpj';
const faqClient = new TrulyFAQClient(API_KEY);

document.addEventListener('DOMContentLoaded', function() {
    // Load FAQs
    loadFAQs();
    
    // Set up question form
    setupQuestionForm();
});

function loadFAQs() {
    const faqContainer = document.getElementById('truelyfaq-faqs');
    
    faqClient.getFAQs()
        .then(response => {
            faqContainer.innerHTML = ''; // Clear loading message
            
            if (response.results && response.results.length > 0) {
                response.results.forEach(faq => {
                    const faqElement = document.createElement('div');
                    faqElement.className = 'truelyfaq-faq-item';
                    faqElement.innerHTML = `
                        <h3 class="truelyfaq-question">${faq.question_text}</h3>
                        <div class="truelyfaq-answer">${faq.answer_text}</div>
                    `;
                    faqContainer.appendChild(faqElement);
                });
            } else {
                faqContainer.innerHTML = '<p>No FAQs available yet.</p>';
            }
        })
        .catch(error => {
            console.error('Error loading FAQs:', error);
            faqContainer.innerHTML = '<p>Failed to load FAQs. Please check your API key and try again.</p>';
        });
}

function setupQuestionForm() {
    const questionForm = document.getElementById('truelyfaq-question-form');
    const emailInput = document.getElementById('truelyfaq-email');
    const questionInput = document.getElementById('truelyfaq-question');
    const submitButton = document.getElementById('truelyfaq-submit');
    const statusMessage = document.getElementById('truelyfaq-status');
    
    questionForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        if (!emailInput.value || !questionInput.value) {
            showStatus('Please fill in all fields.', 'error');
            return;
        }
        
        // Disable form while submitting
        emailInput.disabled = true;
        questionInput.disabled = true;
        submitButton.disabled = true;
        showStatus('Submitting your question...', 'info');
        
        faqClient.submitQuestion(emailInput.value, questionInput.value)
            .then(response => {
                showStatus('Your question has been submitted. We will email you when it\'s answered.', 'success');
                questionForm.reset();
            })
            .catch(error => {
                showStatus('Failed to submit your question. Please check your API key and try again.', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                // Re-enable form
                emailInput.disabled = false;
                questionInput.disabled = false;
                submitButton.disabled = false;
            });
    });
}

function showStatus(message, type) {
    const statusMessage = document.getElementById('truelyfaq-status');
    statusMessage.textContent = message;
    statusMessage.className = 'status-message';
    
    if (type === 'error') {
        statusMessage.classList.add('truelyfaq-error');
    } else if (type === 'success') {
        statusMessage.classList.add('truelyfaq-success');
    } else if (type === 'info') {
        statusMessage.classList.add('truelyfaq-info');
    }
}
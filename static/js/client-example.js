/**
 * TrulyFAQ Client Integration Example
 * 
 * This script demonstrates how to integrate TrulyFAQ with your website.
 * Replace 'YOUR_API_KEY' with your actual API key from the TrulyFAQ dashboard.
 */

class TrulyFAQClient {
    constructor(apiKey, baseUrl = 'https://truelyfaq.com/api') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    /**
     * Submit a question to TrulyFAQ
     * @param {string} email - User's email address
     * @param {string} question - The question text
     * @returns {Promise} - Promise resolving to the API response
     */
    async submitQuestion(email, question) {
        try {
            const response = await fetch(`${this.baseUrl}/questions/submit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey
                },
                body: JSON.stringify({
                    user_email: email,
                    question_text: question
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error submitting question:', error);
            throw error;
        }
    }

    /**
     * Get all FAQs for the website
     * @returns {Promise} - Promise resolving to the list of FAQs
     */
    async getFAQs() {
        try {
            const response = await fetch(`${this.baseUrl}/faqs/`, {
                method: 'GET',
                headers: {
                    'X-API-Key': this.apiKey
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching FAQs:', error);
            throw error;
        }
    }
}

/**
 * Example usage:
 * 
 * 1. Initialize the client with your API key
 * const faqClient = new TrulyFAQClient('YOUR_API_KEY');
 * 
 * 2. Submit a question
 * faqClient.submitQuestion('user@example.com', 'How do I reset my password?')
 *   .then(response => console.log('Question submitted:', response))
 *   .catch(error => console.error('Error:', error));
 * 
 * 3. Get FAQs
 * faqClient.getFAQs()
 *   .then(faqs => {
 *     // Render FAQs on your website
 *     const faqContainer = document.getElementById('faq-container');
 *     faqs.results.forEach(faq => {
 *       const faqElement = document.createElement('div');
 *       faqElement.innerHTML = `
 *         <h3>${faq.question_text}</h3>
 *         <p>${faq.answer_text}</p>
 *       `;
 *       faqContainer.appendChild(faqElement);
 *     });
 *   })
 *   .catch(error => console.error('Error:', error));
 */

// Example HTML form integration
document.addEventListener('DOMContentLoaded', function() {
    const apiKey = 'YOUR_API_KEY'; // Replace with your actual API key
    const faqClient = new TrulyFAQClient(apiKey);
    
    // Load FAQs if there's a container for them
    const faqContainer = document.getElementById('truelyfaq-faqs');
    if (faqContainer) {
        faqClient.getFAQs()
            .then(response => {
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
                faqContainer.innerHTML = '<p>Failed to load FAQs. Please try again later.</p>';
            });
    }
    
    // Handle question form submission
    const questionForm = document.getElementById('truelyfaq-question-form');
    if (questionForm) {
        questionForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const emailInput = document.getElementById('truelyfaq-email');
            const questionInput = document.getElementById('truelyfaq-question');
            const submitButton = document.getElementById('truelyfaq-submit');
            const statusMessage = document.getElementById('truelyfaq-status');
            
            if (!emailInput.value || !questionInput.value) {
                statusMessage.textContent = 'Please fill in all fields.';
                statusMessage.className = 'truelyfaq-error';
                return;
            }
            
            // Disable form while submitting
            emailInput.disabled = true;
            questionInput.disabled = true;
            submitButton.disabled = true;
            statusMessage.textContent = 'Submitting your question...';
            statusMessage.className = 'truelyfaq-info';
            
            faqClient.submitQuestion(emailInput.value, questionInput.value)
                .then(response => {
                    statusMessage.textContent = 'Your question has been submitted. We will email you when it\'s answered.';
                    statusMessage.className = 'truelyfaq-success';
                    questionForm.reset();
                })
                .catch(error => {
                    statusMessage.textContent = 'Failed to submit your question. Please try again later.';
                    statusMessage.className = 'truelyfaq-error';
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
});
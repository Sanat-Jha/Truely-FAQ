/**
 * TrulyFAQ Client Integration
 */

class TrulyFAQClient {
    constructor(apiKey, baseUrl = 'http://127.0.0.1:8000/api') {
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
            console.log('Submitting question to:', `${this.baseUrl}/questions/submit/`);
            console.log('With API key:', this.apiKey);
            console.log('Email:', email);
            console.log('Question:', question);
            
            const response = await fetch(`${this.baseUrl}/questions/submit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Api-Key': this.apiKey
                },
                body: JSON.stringify({
                    user_email: email,
                    question_text: question
                })
            });

            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
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
            console.log('Fetching FAQs from:', `${this.baseUrl}/faqs/`);
            console.log('With API key:', this.apiKey);
            
            const response = await fetch(`${this.baseUrl}/faqs/`, {
                method: 'GET',
                headers: {
                    'X-Api-Key': this.apiKey
                }
            });

            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching FAQs:', error);
            throw error;
        }
    }
}
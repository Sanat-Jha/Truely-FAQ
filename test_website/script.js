document.addEventListener('DOMContentLoaded', function() {
    // API endpoint base URL - replace with your actual hosting URL
    const HOSTING_URL = 'http://localhost:8000/api';
    // Your API key - replace with your actual API key
    const API_KEY = '3qyr6SmVYDwecz2gnhoYrPGGegRumiAUwHzJHLoSVEnKGJ85hlv8tvdN1DTRLHUS';
    
    // Debug elements
    const apiStatusElement = document.getElementById('api-status');
    const faqResponseElement = document.getElementById('faq-response');
    const questionResponseElement = document.getElementById('question-response');
    
    // Check API connection
    checkApiConnection();
    
    // Fetch FAQs from the API
    fetchFAQs();
    
    // Set up the question form submission
    const questionForm = document.getElementById('question-form');
    questionForm.addEventListener('submit', submitQuestion);
    
    // Function to check API connection
    function checkApiConnection() {
        apiStatusElement.innerHTML = 'Checking connection...';
        
        // Simple ping to see if the server is reachable
        fetch(`${HOSTING_URL}/faqs/`, {
            method: 'GET',
            headers: {
                'X-Api-Key': API_KEY
            }
        })
        .then(response => {
            if (response.ok) {
                apiStatusElement.innerHTML = '<span style="color: green;">✓ Connected to API</span>';
                return response.json();
            } else {
                apiStatusElement.innerHTML = `<span style="color: red;">✗ API Error: ${response.status} ${response.statusText}</span>`;
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
        })
        .catch(error => {
            console.error('API Connection Error:', error);
            apiStatusElement.innerHTML = `<span style="color: red;">✗ Connection Error: ${error.message}</span>`;
            
            // Add troubleshooting tips
            apiStatusElement.innerHTML += `
                <div class="troubleshooting">
                    <p><strong>Troubleshooting Tips:</strong></p>
                    <ul>
                        <li>Check if the server is running on port 8000</li>
                        <li>Verify your API key is correct</li>
                        <li>Check for CORS issues in browser console</li>
                        <li>Ensure the API endpoints are correctly implemented</li>
                    </ul>
                </div>
            `;
        });
    }
    
    // Function to fetch FAQs from the API
    function fetchFAQs() {
        const faqContainer = document.getElementById('faq-container');
        
        fetch(`${HOSTING_URL}/faqs/`, {
            method: 'GET',
            headers: {
                'X-Api-Key': API_KEY
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Log the response for debugging
            console.log('FAQ Response:', data);
            faqResponseElement.textContent = JSON.stringify(data, null, 2);
            
            // Clear loading message
            faqContainer.innerHTML = '';
            
            // Check if we have results property (from the API response structure)
            const faqs = data.results || data;
            
            if (!faqs || faqs.length === 0) {
                faqContainer.innerHTML = '<p class="no-faqs">No FAQs available yet. Try submitting some questions!</p>';
                // Add debug info about why FAQs might not be showing
                faqContainer.innerHTML += `
                    <div class="debug-info" style="margin-top: 20px; padding: 10px; background: #f8f9fa; border: 1px solid #ddd; border-radius: 4px;">
                        <h4>Debug Information</h4>
                        <p>FAQs are generated when:</p>
                        <ol>
                            <li>Questions are answered by website owners</li>
                            <li>Similar questions are detected by the system</li>
                        </ol>
                        <p>Possible issues:</p>
                        <ul>
                            <li>No questions have been answered yet</li>
                            <li>NLP utilities might not be available on the server</li>
                            <li>Similarity threshold might be too high</li>
                        </ul>
                    </div>
                `;
                return;
            }
            
            // Create FAQ elements
            faqs.forEach(faq => {
                const faqItem = document.createElement('div');
                faqItem.className = 'faq-item';
                
                const question = document.createElement('div');
                question.className = 'faq-question';
                question.innerHTML = `
                    ${faq.question_text || faq.question}
                    <i class="fas fa-chevron-down"></i>
                `;
                
                const answer = document.createElement('div');
                answer.className = 'faq-answer';
                answer.textContent = faq.answer_text || faq.answer;
                
                faqItem.appendChild(question);
                faqItem.appendChild(answer);
                faqContainer.appendChild(faqItem);
                
                // Add click event to toggle answer visibility
                question.addEventListener('click', () => {
                    answer.classList.toggle('active');
                    const icon = question.querySelector('i');
                    icon.classList.toggle('fa-chevron-down');
                    icon.classList.toggle('fa-chevron-up');
                });
            });
        })
        .catch(error => {
            console.error('Error fetching FAQs:', error);
            faqContainer.innerHTML = `
                <div class="error">
                    <p>Failed to load FAQs. Please try again later.</p>
                    <p>Error: ${error.message}</p>
                </div>
            `;
            faqResponseElement.textContent = `Error: ${error.message}`;
        });
    }
    
    // Function to submit a question
    function submitQuestion(event) {
        event.preventDefault();
        
        const formResponse = document.getElementById('form-response');
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const question = document.getElementById('question').value;
        
        // Prepare the data according to API documentation
        const data = {
            user_email: email,
            question_text: question
            // Note: name is not used in the API as per documentation
        };
        
        // Show loading state
        formResponse.className = 'form-response';
        formResponse.textContent = 'Submitting your question...';
        
        // Send the question to the API using the correct endpoint
        fetch(`${HOSTING_URL}/questions/submit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Api-Key': API_KEY
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            // Log raw response for debugging
            console.log('Question Submit Response:', response);
            
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Log the response data
            console.log('Question Submit Data:', data);
            questionResponseElement.textContent = JSON.stringify(data, null, 2);
            
            // Show success message
            formResponse.className = 'form-response success';
            formResponse.textContent = 'Your question has been submitted successfully! We will notify you when it is answered.';
            
            // Reset the form
            questionForm.reset();
            
            // Refresh FAQs after a short delay (in case the question was auto-answered)
            setTimeout(fetchFAQs, 2000);
        })
        .catch(error => {
            console.error('Error submitting question:', error);
            formResponse.className = 'form-response error';
            formResponse.textContent = `Failed to submit your question. Please try again later. Error: ${error.message}`;
            questionResponseElement.textContent = `Error: ${error.message}`;
        });
    }
});
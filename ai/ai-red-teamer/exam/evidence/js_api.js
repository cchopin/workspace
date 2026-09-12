function fetchConversations() {
    return fetch('/api/conversations')
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) {
                if (data && data.error) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }
            return data.conversations;
        });
}


function fetchConversation(conversationId) {
    if (!conversationId) {
        return Promise.reject(new Error('Missing conversation_id parameter'));
    }

    return fetch(`/api/conversations/${encodeURIComponent(conversationId)}`)
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) {
                if (data && data.error) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }
            return data.conversation;
        });
}


function fetchProfile() {
    return fetch("/api/users/me")
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) {
                if (data && data.error) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }
            return data.user;
        });
}


function submitLlmQuery(event) {
    event.preventDefault();

    const form = event.target;

    // Collect form data
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((value, key) => {
        payload[key] = value;
    });

    fetch("/api/model/query", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) {
                if (data && data.error) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }

            if (!data || !data.conversation_id) {
                throw new Error('No conversation_id returned from server.');
            }

            // Redirect to conversation page
            window.location.href = `/conversation?conversation_id=${encodeURIComponent(data.conversation_id)}`;
        })
        .catch(error => {
            displayError(error.message);
        });
}



function submitChatbotQuery(event) {
    event.preventDefault();

    const form = event.target;

    // Collect form data
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((value, key) => {
        payload[key] = value;
    });

    fetch("/api/model/chatbot", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) {
                if (data && data.error) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }

            if (!data || !data.conversation) {
                throw new Error('No conversation returned from server.');
            }

            // Display conversation
            document.getElementById('conversation_id').value = data.conversation_id;
            displayConversation(data.conversation)

            // Empty the input field
            document.getElementById('prompt').value = '';
        })
        .catch(error => {
            displayError(error.message);
        });
}


function newsletterSignup(event) {
    event.preventDefault(); // Prevent page reload

    const form = document.getElementById("newsletter-form");
    const success = document.getElementById("form-success");
    const error = document.getElementById("form-error");

    const payload = {
        email: document.getElementById('email').value
    };

    fetch('/api/newsletter/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) throw new Error("Request failed");

            // Hide form, show success
            form.style.display = "none";
            success.style.display = "block";
            error.style.display = "none";
        })
        .catch(err => {
            form.style.display = "none";
            error.style.display = "block";
        });
}


function sendContactMessage(event) {
    event.preventDefault(); // Prevent page reload

    const form = document.getElementById("contact-form");
    const success = document.getElementById("newsletter-form-success");
    const error = document.getElementById("newsletter-form-error");

    const payload = {
        firstname: document.getElementById('firstname').value,
        lastname: document.getElementById('lastname').value,
        email: document.getElementById('email').value,
        subject: document.getElementById('subject').value,
        message: document.getElementById('message').value
    };

    fetch('/api/contact/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) throw new Error("Request failed");

            // Hide form, show success
            form.style.display = "none";
            success.style.display = "block";
            error.style.display = "none";
        })
        .catch(err => {
            form.style.display = "none";
            error.style.display = "block";
        });
}


function updateProfile(description) {
    const payload = {
        description: description
    };

    fetch('/api/users/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) throw new Error("Request failed");

            storeMessage("success", "Profile updated successfully!")
            window.location.href = '/profile';
        })
        .catch(error => {
            displayError(error.message);
        });
}

function fetchPositionDetails(positionId) {
    if (!positionId) {
        return Promise.reject(new Error('Missing position_id parameter'));
    }

    return fetch(`/api/positions/${encodeURIComponent(positionId)}`)
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) {
                if (data && data.error) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }
            return data.position;
        });
}


function uploadApplication(event) {
    event.preventDefault();

    const fileInput = document.getElementById("file");
    const positionId = document.getElementById("positionId").value;

    if (fileInput.files.length === 0) {
        displayError("Please select a file");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch(`/api/positions/${positionId}/apply`, {
            method: 'POST',
            body: formData
        })
        .then(response =>
            response.json()
            .then(data => ({
                response,
                data
            }))
            .catch(() => ({
                response,
                data: null
            }))
        )
        .then(({
            response,
            data
        }) => {
            if (!response.ok) {
                if (data && !data.success) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }

            if (!data || !data.application_result) {
                throw new Error('No application result returned from server.');
            }

            // Display result
            displayApplicationResult(data.is_accepted, data.application_result)
        })
        .catch(error => {
            displayError(error.message);
        });
}
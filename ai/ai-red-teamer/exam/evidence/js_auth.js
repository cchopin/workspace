function doLogin(event) {
    event.preventDefault();

    const payload = {
        username: document.getElementById('username').value,
        password: document.getElementById('password').value
    };

    fetch('/api/auth/login', {
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
                if (data && !data.success) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }

            // Login successful
            storeMessage("success", "Logged in successfully!")
            window.location.href = '/profile';
        })
        .catch(error => {
            displayError(error.message);
        });
}


function doRegistration(event) {
    event.preventDefault();

    const payload = {
        username: document.getElementById('username').value,
        password: document.getElementById('password').value
    };

    fetch('/api/auth/register', {
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
                if (data && !data.success) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }

            // Registration successful
            storeMessage("success", "User registered successfully!")
            window.location.href = '/login';
        })
        .catch(error => {
            displayError(error.message);
        });
}

function doLogout() {

    fetch('/api/auth/logout', {
            method: 'GET'
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

            // Logout successful
            storeMessage("success", "Logged out successfully!")
            window.location.href = '/login';
        })
        .catch(error => {
            displayError(error.message);
        });
}


function forgotPassword(event) {
    event.preventDefault();

    const payload = {
        username: document.getElementById('username').value
    };

    fetch('/api/auth/forgot-password', {
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
                if (data && !data.success) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }

            // Login successful
            storeMessage("success", "Success!")
            window.location.href = '/reset-password';
        })
        .catch(error => {
            displayError(error.message);
        });
}


function resetPassword(event) {
    event.preventDefault();

    const payload = {
        token: document.getElementById('token').value,
        password: document.getElementById('password').value
    };

    fetch('/api/auth/reset-password', {
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
                if (data && !data.success) {
                    throw new Error(data.error);
                } else {
                    throw new Error(`HTTP error: ${response.status}`);
                }
            }

            // Login successful
            storeMessage("success", "Password reset successfully!")
            window.location.href = '/login';
        })
        .catch(error => {
            displayError(error.message);
        });
}
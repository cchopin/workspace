function checkAdminAccess() {
    return fetch('/api/users/me')
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
            if (data.user.role !== "admin") {
                throw new Error("Unauthorized");
            }
        });
}

function getAdminMessage() {
    return fetch('/api/admin/message')
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
            return data;
        });
}

function fetchData(endpoint) {
    return fetch(`/api/admin/${endpoint}`)
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
            return data.data;
        });
}

function displayAdminMessage(data) {
    const div1 = document.getElementById(`flag`);
    const el1 = document.createElement("div");
    el1.textContent = `Flag: ${data.flag}`;
    div1.replaceChildren(el1);

    const div2 = document.getElementById(`admin-message`);
    const el2 = document.createElement("div");
    el2.innerHTML = data.message;
    div2.replaceChildren(el2);
    div2.style.display = 'block'
}

function displayAdminUsers(data) {
    const list = document.getElementById('dataList');
    list.innerHTML = '';

    if (data.length > 0) {
        const msgDiv = document.getElementById('noData');
        msgDiv.style.display = 'none';
    }

    data.forEach(data_item => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = '#';
        link.textContent = data_item.username
        li.appendChild(link);
        list.appendChild(li);
    });
}

function displayAdminConversations(data) {
    const list = document.getElementById('dataList');
    list.innerHTML = '';

    if (data.length > 0) {
        const msgDiv = document.getElementById('noData');
        msgDiv.style.display = 'none';
    }

    data.forEach(data_item => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = `/conversation?conversation_id=${encodeURIComponent(data_item.id)}`;
        link.textContent = `${data_item.title}: ${data_item.summary}`
        li.appendChild(link);
        list.appendChild(li);
    });
}

function displayAdminNewsletter(data) {
    const list = document.getElementById('dataList');
    list.innerHTML = '';

    if (data.length > 0) {
        const msgDiv = document.getElementById('noData');
        msgDiv.style.display = 'none';
    }

    data.forEach(data_item => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = '#';
        link.textContent = data_item.email
        li.appendChild(link);
        list.appendChild(li);
    });
}

function displayAdminMessages(data) {
    const list = document.getElementById('dataList');
    list.innerHTML = '';

    if (data.length > 0) {
        const msgDiv = document.getElementById('noData');
        msgDiv.style.display = 'none';
    }

    data.forEach(data_item => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = '#';
        link.textContent = `From ${data_item.email}: ${data_item.subject}`;
        li.appendChild(link);
        list.appendChild(li);
    });
}

function displayAdminApplications(data) {
    const list = document.getElementById('dataList');
    list.innerHTML = '';

    if (data.length > 0) {
        const msgDiv = document.getElementById('noData');
        msgDiv.style.display = 'none';
    }

    data.forEach(data_item => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = '#';
        link.textContent = `Accepted: ${data_item.is_accepted} - ${data_item.content.slice(0, 100)}`;
        li.appendChild(link);
        list.appendChild(li);
    });
}


function callSysmind() {
    return fetch("/api/model/sysmind")
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
            return data.sysmind_response;
        });
}

function displaySysmindResponse(response) {
    const header = document.getElementById('sysmindHeader');
    header.textContent = "SysMind recommends the following actions based on the most recent user message:";

    const body = document.getElementById('sysmindResponse');
    body.textContent = response;
}
function storeMessage(type, message) {
    sessionStorage.setItem("msg", JSON.stringify({
        type: type,
        message: message
    }));
}

function displayMessage() {
    const msg = sessionStorage.getItem("msg");
    if (!msg) return;

    const {
        type,
        message
    } = JSON.parse(msg);
    sessionStorage.removeItem("msg");

    const div = document.getElementById(`flash-${type}-message`);
    const el = document.createElement("div");
    el.textContent = message;
    div.replaceChildren(el);
    div.style.display = 'block'

    setTimeout(() => div.style.display = 'None', 4000);

    // scroll to the message
    window.scrollTo(0, 0);
}

function displayError(message) {
    storeMessage("error", message);
    displayMessage();
}

function displayConversations(conversations) {
    const list = document.getElementById('conversationList');
    list.innerHTML = '';

    if (conversations.length > 0) {
        const msgDiv = document.getElementById('noConversations');
        msgDiv.style.display = 'none';
    }

    conversations.forEach(conversation => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = `/chatbot?conversation_id=${encodeURIComponent(conversation.id)}`;
        link.textContent = `${conversation.title}: ${conversation.summary}`;
        li.appendChild(link);
        list.appendChild(li);
    });
}

function displayConversation(conversation) {
    const list = document.getElementById('conversation');
    list.innerHTML = '';

    conversation.forEach(msg => {
        if (msg.role === 'error') {
            displayError(msg.content);
            return;
        }

        const li = document.createElement('li');
        li.classList.add('message');
        li.classList.add(msg.role === 'user' ? 'user' : 'assistant');
        li.textContent = msg.content;
        list.appendChild(li);
    });
}

function displayProfile(user) {
    const username = document.getElementById('username');
    username.innerHTML = '';
    username.textContent = user.username;

    const role = document.getElementById('role');
    role.innerHTML = '';
    role.textContent = user.role;

    const description = document.getElementById('description');
    description.innerHTML = '';
    description.textContent = user.description;
}

function displayPositionDetails(position) {
    const t = document.getElementById('positionTitle');
    t.textContent = position.title;

    const s = document.getElementById('positionSalary');
    s.textContent = `${position.salary} HTB$`;

    const l = document.getElementById('positionLocation');
    l.textContent = position.location;

    const h = document.getElementById('positionHours');
    h.textContent = position.hours;

    const d = document.getElementById('positionDescription');
    d.textContent = position.description;
}

function displayApplicationResult(isAccepted, applicationResult) {
    const div1 = document.getElementById('applicationResult1');
    const div2 = document.getElementById('applicationResult2');
    result = "<b>Your application has been rejected</b>";

    if (isAccepted) {
        result = "<b>Congratulations, your application has been accepted. We will contact you with more details in the upcoming days</b>";
    }

    div1.innerHTML = result;
    div2.textContent = applicationResult;

    const form = document.getElementById("applyForm");
    form.style.display = "none";
}
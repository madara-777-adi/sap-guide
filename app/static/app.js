const $ = (id) => document.getElementById(id);

const loginView = $("login-view");
const chatView = $("chat-view");
const logoutButton = $("logout");
const loginError = $("login-error");
const messages = $("messages");
const questionBox = $("question");
const askButton = $("ask-button");

function showView(loggedIn) {
  loginView.hidden = loggedIn;
  chatView.hidden = !loggedIn;
  logoutButton.hidden = !loggedIn;
  if (loggedIn) questionBox.focus();
}

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  let data = null;
  try {
    data = await response.json();
  } catch {
    // body was not JSON
  }
  return { response, data };
}

function errorText(response, data) {
  if (data && typeof data.detail === "string") return data.detail;
  return `Something went wrong (code ${response.status}).`;
}

function addMessage(kind, text, sources) {
  const box = document.createElement("div");
  box.className = `message ${kind}`;

  const body = document.createElement("div");
  body.className = "text";
  body.textContent = text;
  box.appendChild(body);

  if (sources && sources.length) {
    const note = document.createElement("div");
    note.className = "sources";
    note.textContent =
      "Pages checked: " +
      sources.map((s) => `${s.doc}, page ${s.page}`).join(" · ");
    box.appendChild(note);
  }

  messages.appendChild(box);
  box.scrollIntoView({ block: "end", behavior: "smooth" });
  return box;
}

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  loginError.textContent = "";
  try {
    const { response, data } = await postJson("/login", {
      username: $("username").value,
      password: $("password").value,
    });
    if (response.ok) {
      $("password").value = "";
      showView(true);
    } else {
      loginError.textContent = errorText(response, data);
    }
  } catch {
    loginError.textContent = "Cannot reach the server.";
  }
});

$("ask-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionBox.value.trim();
  if (!question) return;

  addMessage("user", question);
  questionBox.value = "";
  askButton.disabled = true;
  const pending = addMessage("bot", "Thinking…");

  try {
    const { response, data } = await postJson("/ask", { question });
    pending.remove();
    if (response.status === 401) {
      showView(false);
      loginError.textContent = "Your session ended. Please log in again.";
    } else if (response.ok) {
      addMessage("bot", data.answer, data.sources);
    } else {
      addMessage("error", errorText(response, data));
    }
  } catch {
    pending.remove();
    addMessage("error", "Cannot reach the server. Check your connection.");
  } finally {
    askButton.disabled = false;
  }
});

questionBox.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("ask-form").requestSubmit();
  }
});

logoutButton.addEventListener("click", async () => {
  try {
    await postJson("/logout", {});
  } catch {
    // clearing the screen below is what matters
  }
  messages.replaceChildren();
  showView(false);
});

(async function init() {
  try {
    const response = await fetch("/session");
    showView(response.ok);
  } catch {
    showView(false);
  }
})();

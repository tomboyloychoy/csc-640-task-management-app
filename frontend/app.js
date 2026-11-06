const state = {
  status: "all",
  tag: null,
  tasks: [],
  tags: [],
  editingTask: null,
  toastTimer: null,
};

const isGitHubPages = location.hostname.endsWith(".github.io")
  || new URLSearchParams(location.search).has("static");
const storageKey = "tamana.tasks.v1";
const defaultTags = ["School", "Work", "House", "Personal", "Other"];

const elements = {
  taskList: document.querySelector("#task-list"),
  emptyState: document.querySelector("#empty-state"),
  emptyTitle: document.querySelector("#empty-title"),
  emptyCopy: document.querySelector("#empty-copy"),
  search: document.querySelector("#task-search"),
  sort: document.querySelector("#sort-select"),
  tagNav: document.querySelector("#tag-nav"),
  tagOptions: document.querySelector("#tag-options"),
  dialog: document.querySelector("#task-dialog"),
  form: document.querySelector("#task-form"),
  formError: document.querySelector("#form-error"),
  toast: document.querySelector("#toast"),
};

const tagColors = {
  school: "school",
  work: "work",
  house: "house",
  personal: "personal",
  other: "other",
};

function tagColor(tag) {
  return tagColors[tag.toLowerCase()] ?? "custom";
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function showToast(message) {
  clearTimeout(state.toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  state.toastTimer = setTimeout(() => elements.toast.classList.remove("is-visible"), 2800);
}

function staticTasks() {
  const stored = localStorage.getItem(storageKey);
  if (!stored) return [];
  const tasks = JSON.parse(stored);
  if (!Array.isArray(tasks)) throw new Error("Saved tasks in this browser could not be read.");
  return tasks;
}

function staticApi(path, options = {}) {
  const url = new URL(path, location.href);
  const method = options.method ?? "GET";
  const taskId = Number(url.pathname.match(/\/api\/tasks\/(\d+)$/)?.[1]);
  const tasks = staticTasks();

  if (url.pathname.endsWith("/api/tags")) {
    return [...new Set([...defaultTags, ...tasks.map((task) => task.tag)])];
  }
  if (!url.pathname.includes("/api/tasks")) throw new Error("This Pages demo route is not available.");

  if (method === "POST") {
    const body = JSON.parse(options.body);
    const task = { ...body, id: Date.now(), created_at: new Date().toISOString(), completed: false };
    tasks.push(task);
    localStorage.setItem(storageKey, JSON.stringify(tasks));
    return task;
  }
  if (method === "PUT") {
    const index = tasks.findIndex((task) => task.id === taskId);
    if (index < 0) throw new Error("Task not found.");
    tasks[index] = { ...JSON.parse(options.body), id: taskId, created_at: tasks[index].created_at };
    localStorage.setItem(storageKey, JSON.stringify(tasks));
    return tasks[index];
  }
  if (method === "DELETE") {
    const remaining = tasks.filter((task) => task.id !== taskId);
    if (remaining.length === tasks.length) throw new Error("Task not found.");
    localStorage.setItem(storageKey, JSON.stringify(remaining));
    return null;
  }

  const statusFilter = url.searchParams.get("status_filter") ?? "all";
  const tag = url.searchParams.get("tag");
  const query = url.searchParams.get("q")?.toLocaleLowerCase() ?? "";
  return tasks.filter((task) => {
    if (statusFilter === "active" && task.completed) return false;
    if (statusFilter === "completed" && !task.completed) return false;
    if (tag && task.tag.toLocaleLowerCase() !== tag.toLocaleLowerCase()) return false;
    return !query || `${task.title} ${task.description}`.toLocaleLowerCase().includes(query);
  });
}

async function api(path, options = {}) {
  if (isGitHubPages) return staticApi(path, options);
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function setBusy(isBusy) {
  document.querySelectorAll(".primary-button, .new-task-button").forEach((button) => {
    button.disabled = isBusy;
  });
}

function formatDueDate(value) {
  if (!value) return "";
  const due = new Date(`${value}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);
  if (due.getTime() === today.getTime()) return "Today";
  if (due.getTime() === tomorrow.getTime()) return "Tomorrow";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(due);
}

function taskMarkup(task) {
  const overdue = task.due_date && new Date(`${task.due_date}T00:00:00`) < new Date(new Date().toDateString());
  return `
    <article class="task-row ${task.completed ? "is-completed" : ""}" data-task-id="${task.id}">
      <button class="task-check" type="button" role="checkbox" aria-checked="${task.completed}" aria-label="${task.completed ? "Mark incomplete" : "Mark complete"}: ${escapeHtml(task.title)}">${task.completed ? "✓" : ""}</button>
      <div class="task-copy">
        <p class="task-name">${escapeHtml(task.title)}</p>
        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}
      </div>
      <div class="task-meta">
        <span class="task-tag" data-tag-color="${tagColor(task.tag)}">${escapeHtml(task.tag)}</span>
        ${task.due_date ? `<span class="task-due ${overdue && !task.completed ? "is-overdue" : ""}">${formatDueDate(task.due_date)}</span>` : ""}
        <span class="task-priority" data-priority="${task.priority}"><span class="priority-dot"></span>${task.priority}</span>
        <div class="task-actions">
          <button class="task-action edit-task" type="button" aria-label="Edit ${escapeHtml(task.title)}" title="Edit task">✎</button>
          <button class="task-action delete delete-task" type="button" aria-label="Delete ${escapeHtml(task.title)}" title="Delete task">×</button>
        </div>
      </div>
    </article>`;
}

function sortTasks(tasks) {
  const sorted = [...tasks];
  if (elements.sort.value === "newest") {
    sorted.sort((a, b) => b.created_at.localeCompare(a.created_at));
  } else if (elements.sort.value === "priority") {
    const rank = { high: 0, normal: 1, low: 2 };
    sorted.sort((a, b) => rank[a.priority] - rank[b.priority] || a.title.localeCompare(b.title));
  } else {
    sorted.sort((a, b) => {
      if (!a.due_date && !b.due_date) return b.created_at.localeCompare(a.created_at);
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return a.due_date.localeCompare(b.due_date);
    });
  }
  return sorted;
}

function renderTasks() {
  const tasks = sortTasks(state.tasks);
  elements.taskList.innerHTML = tasks.map(taskMarkup).join("");
  elements.emptyState.hidden = tasks.length > 0;
  document.querySelector("#visible-count").textContent = tasks.length;
  if (tasks.length === 0) {
    const hasFilter = Boolean(state.tag || elements.search.value.trim());
    elements.emptyTitle.textContent = hasFilter ? "No tasks found." : state.status === "completed" ? "Nothing checked off yet." : "A little breathing room.";
    elements.emptyCopy.textContent = hasFilter ? "Try another search or choose a different tag." : state.status === "completed" ? "Your finished tasks will find a home here." : "Nothing here just yet. Add a task when you’re ready.";
  }
}

async function loadTasks() {
  const query = new URLSearchParams({ status_filter: state.status });
  if (state.tag) query.set("tag", state.tag);
  if (elements.search.value.trim()) query.set("q", elements.search.value.trim());
  try {
    state.tasks = await api(`/api/tasks?${query}`);
    renderTasks();
    await loadCounts();
  } catch (error) {
    elements.taskList.innerHTML = "";
    elements.emptyState.hidden = false;
    elements.emptyTitle.textContent = "We couldn’t load your tasks.";
    elements.emptyCopy.textContent = error.message;
    showToast(error.message);
  }
}

async function loadCounts() {
  const tasks = await api("/api/tasks");
  const active = tasks.filter((task) => !task.completed).length;
  const completed = tasks.length - active;
  document.querySelector("#all-count").textContent = tasks.length;
  document.querySelector("#active-count").textContent = active;
  document.querySelector("#completed-count").textContent = completed;
  document.querySelector("#summary-active").textContent = active;
  document.querySelector("#summary-completed").textContent = completed;
}

async function loadTags() {
  state.tags = await api("/api/tags");
  elements.tagNav.innerHTML = state.tags.map((tag) => `
    <button class="nav-item ${state.tag === tag ? "is-active" : ""}" data-tag="${escapeHtml(tag)}" type="button">
      <span class="tag-dot" data-tag-color="${tagColor(tag)}"></span>
      <span>${escapeHtml(tag)}</span>
    </button>`).join("");
  elements.tagOptions.innerHTML = state.tags.map((tag) => `<option value="${escapeHtml(tag)}"></option>`).join("");
}

function updateViewTitle() {
  const title = state.tag || ({ all: "All tasks", active: "To do", completed: "Completed" })[state.status];
  document.querySelector("#breadcrumb-current").textContent = title;
  document.querySelector("#page-title").innerHTML = `${escapeHtml(title)}<span class="title-period">.</span>`;
  document.querySelector("#list-heading").textContent = title;
}

function openDialog(task = null, initialTag = "") {
  state.editingTask = task;
  elements.form.reset();
  elements.formError.textContent = "";
  document.querySelector("#dialog-title").textContent = task ? "Edit task" : "Add a task";
  document.querySelector("#save-task-button").innerHTML = task ? "Save changes <span>→</span>" : "Add task <span>→</span>";
  if (task) {
    document.querySelector("#task-title").value = task.title;
    document.querySelector("#task-description").value = task.description;
    document.querySelector("#task-tag").value = task.tag;
    document.querySelector("#task-due-date").value = task.due_date ?? "";
    document.querySelector("#task-priority").value = task.priority;
  } else {
    document.querySelector("#task-tag").value = initialTag;
    document.querySelector("#task-priority").value = "normal";
  }
  elements.dialog.showModal();
  document.querySelector("#task-title").focus();
}

function setView(status, tag = null) {
  state.status = status;
  state.tag = tag;
  document.querySelectorAll(".primary-nav .nav-item").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.status === status && !tag);
  });
  document.querySelectorAll("#tag-nav .nav-item").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tag === tag);
  });
  updateViewTitle();
  loadTasks();
}

async function saveTask(event) {
  event.preventDefault();
  const formData = new FormData(elements.form);
  const task = Object.fromEntries(formData.entries());
  task.tag = task.tag.trim() || "Personal";
  task.due_date = task.due_date || null;
  const saveButton = document.querySelector("#save-task-button");
  saveButton.disabled = true;
  elements.formError.textContent = "";
  try {
    const editing = state.editingTask;
    const url = editing ? `/api/tasks/${editing.id}` : "/api/tasks";
    await api(url, { method: editing ? "PUT" : "POST", body: JSON.stringify({ ...task, completed: editing?.completed ?? false }) });
    elements.dialog.close();
    await loadTags();
    await loadTasks();
    showToast(editing ? "Task updated." : "Task added.");
  } catch (error) {
    elements.formError.textContent = error.message;
  } finally {
    saveButton.disabled = false;
  }
}

async function toggleTask(task) {
  try {
    await api(`/api/tasks/${task.id}`, {
      method: "PUT",
      body: JSON.stringify({ ...task, completed: !task.completed }),
    });
    await loadTasks();
  } catch (error) {
    showToast(error.message);
  }
}

async function deleteTask(task) {
  if (!window.confirm(`Delete “${task.title}”? This can’t be undone.`)) return;
  try {
    await api(`/api/tasks/${task.id}`, { method: "DELETE" });
    await loadTags();
    await loadTasks();
    showToast("Task deleted.");
  } catch (error) {
    showToast(error.message);
  }
}

function bindEvents() {
  document.querySelectorAll(".primary-nav .nav-item").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.status));
  });
  elements.tagNav.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tag]");
    if (button) setView("all", button.dataset.tag);
  });
  [document.querySelector("#new-task-button"), document.querySelector("#intro-add-button"), document.querySelector("#empty-add-button")]
    .forEach((button) => button.addEventListener("click", () => openDialog()));
  document.querySelector("#add-tag-button").addEventListener("click", () => {
    const tag = window.prompt("Name your new tag:");
    if (tag?.trim()) openDialog(null, tag.trim().slice(0, 32));
  });
  document.querySelector("#close-dialog").addEventListener("click", () => elements.dialog.close());
  document.querySelector("#cancel-dialog").addEventListener("click", () => elements.dialog.close());
  elements.form.addEventListener("submit", saveTask);
  elements.search.addEventListener("input", () => {
    clearTimeout(state.searchTimer);
    state.searchTimer = setTimeout(loadTasks, 180);
  });
  elements.sort.addEventListener("change", renderTasks);
  document.querySelector("#focus-search-button").addEventListener("click", () => elements.search.focus());
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && elements.dialog.open) elements.dialog.close();
    if ((event.key === "/" && !elements.dialog.open && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName))) {
      event.preventDefault();
      elements.search.focus();
    }
    if (event.key.toLowerCase() === "n" && !elements.dialog.open && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      event.preventDefault();
      openDialog();
    }
  });
  elements.taskList.addEventListener("click", (event) => {
    const row = event.target.closest("[data-task-id]");
    if (!row) return;
    const task = state.tasks.find((item) => item.id === Number(row.dataset.taskId));
    if (!task) return;
    if (event.target.closest(".task-check")) toggleTask(task);
    else if (event.target.closest(".edit-task")) openDialog(task);
    else if (event.target.closest(".delete-task")) deleteTask(task);
  });
}

function setDateLabels() {
  const now = new Date();
  document.querySelector("#today-label").textContent = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(now);
}

async function initialize() {
  bindEvents();
  setDateLabels();
  try {
    await loadTags();
    await loadTasks();
  } catch (error) {
    showToast(`Tamana couldn’t start: ${error.message}`);
    elements.emptyState.hidden = false;
    elements.emptyTitle.textContent = "Tamana couldn’t start.";
    elements.emptyCopy.textContent = error.message;
  }
}

initialize();

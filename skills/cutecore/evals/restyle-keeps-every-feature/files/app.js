const list = document.getElementById("list");
let todos = JSON.parse(localStorage.getItem("todos") || "[]");
function save() { localStorage.setItem("todos", JSON.stringify(todos)); render(); }
function render() {
  list.innerHTML = "";
  todos.forEach((t, i) => {
    const li = document.createElement("li"); li.className = t.done ? "done" : "";
    li.innerHTML = `<input type="checkbox" ${t.done ? "checked" : ""}> <span></span> <button aria-label="Delete">x</button>`;
    li.querySelector("span").textContent = t.text;
    li.querySelector("input").addEventListener("change", () => { t.done = !t.done; save(); });
    li.querySelector("button").addEventListener("click", () => { todos.splice(i, 1); save(); });
    list.appendChild(li);
  });
  document.getElementById("left").textContent = todos.filter(t => !t.done).length;
}
document.getElementById("add").addEventListener("submit", e => { e.preventDefault(); const f = new FormData(e.target); todos.push({ text: f.get("task"), done: false }); e.target.reset(); save(); });
document.getElementById("clear").addEventListener("click", () => { todos = todos.filter(t => !t.done); save(); });
render();

// Injects a scroll-to-top button that appears after scrolling down 300px.
// When clicked, it smoothly scrolls the page back to the top.

window.addEventListener("scroll", function () {
  const btn = document.getElementById("scrollToTop");
  btn.style.display = window.scrollY > 300 ? "block" : "none";
});

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.createElement("button");
  btn.id = "scrollToTop";
  btn.textContent = "↑ Top";
  btn.setAttribute("aria-label", "Scroll to top");
  btn.onclick = scrollToTop;
  document.body.appendChild(btn);
});

document.querySelectorAll("[data-scroll-box]").forEach((link) => {
  link.addEventListener("click", (event) => {
    const target = document.getElementById("box");
    if (!target) {
      return;
    }
    event.preventDefault();
    const top = target.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top, behavior: "smooth" });
  });
});

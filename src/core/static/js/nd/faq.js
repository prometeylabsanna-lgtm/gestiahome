const ICON_OPEN = "M2 8l4-4 4 4";
const ICON_CLOSED = "M2 4l4 4 4-4";

function setOpen(item, open) {
  const button = item.querySelector("[data-faq-toggle]");
  const panel = item.querySelector("[data-faq-panel]");
  const path = item.querySelector(".nd-faq__icon-path");
  if (!button || !panel) {
    return;
  }
  button.setAttribute("aria-expanded", open ? "true" : "false");
  if (open) {
    panel.removeAttribute("hidden");
  } else {
    panel.setAttribute("hidden", "");
  }
  if (path) {
    path.setAttribute("d", open ? ICON_OPEN : ICON_CLOSED);
  }
}

function initFaq(root) {
  const items = [...root.querySelectorAll("[data-faq-item]")];
  items.forEach((item, index) => {
    setOpen(item, index === 0);
    const button = item.querySelector("[data-faq-toggle]");
    if (!button) {
      return;
    }
    button.addEventListener("click", () => {
      const open = button.getAttribute("aria-expanded") === "true";
      setOpen(item, !open);
    });
  });
}

document.querySelectorAll("[data-faq]").forEach(initFaq);

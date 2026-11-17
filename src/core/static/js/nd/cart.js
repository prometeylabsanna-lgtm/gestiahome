function submitQtyForm(form) {
  if (typeof form.requestSubmit === "function") {
    form.requestSubmit();
  } else {
    form.submit();
  }
}

function applyQty(button) {
  const form = button.closest("form");
  if (!form) {
    return;
  }
  const input = form.querySelector("[data-qty-input]");
  if (!input) {
    return;
  }
  if (button.hasAttribute("data-qty-set")) {
    input.value = button.getAttribute("data-qty-set") || "0";
  } else {
    const step = Number(button.getAttribute("data-qty-step"));
    const current = Number.parseInt(input.value, 10);
    const base = Number.isNaN(current) ? 1 : current;
    const parsedMax = Number.parseInt(input.getAttribute("max"), 10);
    const cap = Number.isNaN(parsedMax) ? 99 : Math.min(99, Math.max(0, parsedMax));
    const ceiling = Math.max(cap, 1);
    const next = Math.min(ceiling, Math.max(1, base + step));
    input.value = String(next);
  }
  submitQtyForm(form);
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-qty-step], [data-qty-set]");
  if (!button || button.closest("[data-nd-cart-drawer]")) {
    return;
  }
  if (!button.closest("[data-nd-cart]")) {
    return;
  }
  applyQty(button);
});

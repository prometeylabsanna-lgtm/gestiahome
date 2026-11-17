const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

let root = null;
let panel = null;
let mount = null;
let lastFocus = null;
let open = false;

function getRoot() {
  if (!root) {
    root = document.querySelector("[data-nd-cart-drawer]");
    panel = root ? root.querySelector("#nd-cart-drawer-panel") : null;
    mount = root ? root.querySelector("#nd-cart-drawer-body") : null;
  }
  return root;
}

function focusables() {
  if (!panel) {
    return [];
  }
  return [...panel.querySelectorAll(FOCUSABLE)].filter(
    (el) => el.offsetParent !== null || el === panel,
  );
}

function trapFocus(event) {
  if (!open || event.key !== "Tab" || !panel) {
    return;
  }
  const items = focusables();
  if (!items.length) {
    event.preventDefault();
    panel.focus();
    return;
  }
  const first = items[0];
  const last = items[items.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function closeDrawer() {
  const el = getRoot();
  if (!el || !open) {
    return;
  }
  open = false;
  el.setAttribute("hidden", "");
  if (panel) {
    panel.setAttribute("aria-hidden", "true");
  }
  document.body.classList.remove("nd-cart-drawer-open");
  if (lastFocus && typeof lastFocus.focus === "function") {
    lastFocus.focus();
  }
  lastFocus = null;
}

function openDrawer() {
  const el = getRoot();
  if (!el || !panel) {
    return;
  }
  lastFocus = document.activeElement;
  open = true;
  el.removeAttribute("hidden");
  panel.setAttribute("aria-hidden", "false");
  document.body.classList.add("nd-cart-drawer-open");
  const closeBtn = panel.querySelector("[data-nd-cart-close]");
  (closeBtn || panel).focus();
}

function refreshCartBody() {
  const body = document.getElementById("cart-body");
  if (!body || !window.htmx) {
    return;
  }
  const url = body.getAttribute("data-cart-url");
  if (!url) {
    return;
  }
  window.htmx.ajax("GET", url, { target: "#cart-body", swap: "innerHTML" });
}

function loadPanel(sku) {
  const el = getRoot();
  if (!el || !mount || !window.htmx || !sku) {
    return Promise.resolve();
  }
  const base = el.getAttribute("data-panel-url") || "";
  const url = `${base}?sku=${encodeURIComponent(sku)}`;
  return window.htmx.ajax("GET", url, {
    target: "#nd-cart-drawer-body",
    swap: "innerHTML",
  });
}

function onCartAdded(event) {
  const sku = event.detail && event.detail.sku;
  if (!sku) {
    return;
  }
  refreshCartBody();
  Promise.resolve(loadPanel(sku)).then(() => openDrawer());
}

function onCartChanged() {
  refreshCartBody();
}

function onClick(event) {
  if (!open) {
    return;
  }
  if (event.target.closest("[data-nd-cart-close]")) {
    closeDrawer();
  }
}

function onKey(event) {
  if (!open) {
    return;
  }
  if (event.key === "Escape") {
    closeDrawer();
    return;
  }
  trapFocus(event);
}

function bindQtyInDrawer(event) {
  const button = event.target.closest("[data-qty-step], [data-qty-set]");
  if (!button || !button.closest("#nd-cart-drawer-body")) {
    return;
  }
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
    input.value = String(Math.min(ceiling, Math.max(1, base + step)));
  }
  if (typeof form.requestSubmit === "function") {
    form.requestSubmit();
  } else {
    form.submit();
  }
}

document.body.addEventListener("nd:cart-added", onCartAdded);
document.body.addEventListener("nd:cart-changed", onCartChanged);
document.addEventListener("click", onClick);
document.addEventListener("keydown", onKey);
document.addEventListener("click", bindQtyInDrawer);

getRoot();

function clampQty(value, maxValue) {
  const number = Number.parseInt(value, 10);
  const parsedMax = Number.parseInt(maxValue, 10);
  const cap = Number.isNaN(parsedMax) ? 99 : Math.min(99, Math.max(0, parsedMax));
  if (cap < 1) {
    return 0;
  }
  const safe = Number.isNaN(number) ? 1 : number;
  return Math.min(cap, Math.max(1, safe));
}

function bindQty(root) {
  const input = root.querySelector("[data-qty]");
  const label = root.querySelector("[data-qty-label]");
  if (!input || !label) {
    return;
  }
  function setQty(next) {
    const value = String(clampQty(next, input.getAttribute("max")));
    input.value = value;
    label.textContent = value;
  }
  const inc = root.querySelector("[data-qty-inc]");
  const dec = root.querySelector("[data-qty-dec]");
  if (inc) {
    inc.addEventListener("click", () => setQty(Number(input.value) + 1));
  }
  if (dec) {
    dec.addEventListener("click", () => setQty(Number(input.value) - 1));
  }
}

document.querySelectorAll("[data-pdp]").forEach((root) => {
  bindQty(root);
});

function syncCheckoutSubmitLabel() {
  const root = document.querySelector("[data-nd-checkout]");
  if (!root) {
    return;
  }
  const button = root.querySelector("[data-nd-checkout-submit]");
  if (!button) {
    return;
  }
  const cardOn = root.querySelector('input[name="payment_method"][value="card"]:checked');
  const payLabel = button.getAttribute("data-label-pay") || "";
  const placeLabel = button.getAttribute("data-label-place") || "";
  button.textContent = cardOn ? payLabel : placeLabel;
}

document.addEventListener("change", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) {
    return;
  }
  if (target.name !== "payment_method") {
    return;
  }
  if (!target.closest("[data-nd-checkout]")) {
    return;
  }
  syncCheckoutSubmitLabel();
});

document.addEventListener("DOMContentLoaded", syncCheckoutSubmitLabel);

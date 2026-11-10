document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-liqpay-auto]");
  if (!(form instanceof HTMLFormElement)) {
    return;
  }
  form.submit();
});

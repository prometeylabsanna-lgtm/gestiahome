(function () {
  const root = document.querySelector("[data-waitlist-modal]");
  if (!root) {
    return;
  }

  const storageKey = root.dataset.storageKey || "gestia_waitlist_modal_seen";
  const startedKey = root.dataset.startedKey || "gestia_waitlist_site_started_at";
  const delayMs = Number(root.dataset.delayMs || 15000);
  let timerId = 0;
  let lastFocused = null;
  let scrollY = 0;

  function lockScroll(open) {
    if (open) {
      scrollY = window.scrollY || window.pageYOffset || 0;
      document.body.classList.add("waitlist-modal-open");
      document.body.style.top = "-" + scrollY + "px";
      return;
    }
    document.body.classList.remove("waitlist-modal-open");
    document.body.style.top = "";
    window.scrollTo(0, scrollY);
  }

  function alreadySeen() {
    try {
      return window.sessionStorage.getItem(storageKey) === "1";
    } catch (_error) {
      return false;
    }
  }

  function markSeen() {
    try {
      window.sessionStorage.setItem(storageKey, "1");
    } catch (_error) {
      /* ignore */
    }
  }

  function startedAt() {
    try {
      const raw = window.sessionStorage.getItem(startedKey);
      const parsed = Number(raw);
      if (parsed > 0) {
        return parsed;
      }
      const now = Date.now();
      window.sessionStorage.setItem(startedKey, String(now));
      return now;
    } catch (_error) {
      return Date.now();
    }
  }

  function openModal() {
    if (alreadySeen() || root.classList.contains("is-open")) {
      return;
    }
    var sheet = document.querySelector("[data-catalog-sheet]");
    if (sheet && !sheet.hidden) {
      return;
    }
    markSeen();
    lastFocused = document.activeElement;
    lockScroll(true);
    root.hidden = false;
    requestAnimationFrame(() => {
      root.classList.add("is-open");
    });
    const closeBtn = root.querySelector(".waitlist-modal__close");
    if (closeBtn) {
      closeBtn.focus();
    }
  }

  function closeModal(restoreFocus) {
    if (!root.classList.contains("is-open") && root.hidden) {
      return;
    }
    markSeen();
    root.classList.remove("is-open");
    lockScroll(false);
    window.setTimeout(() => {
      root.hidden = true;
    }, 280);
    if (restoreFocus !== false && lastFocused && typeof lastFocused.focus === "function") {
      lastFocused.focus();
    }
  }

  root.addEventListener("click", (event) => {
    if (event.target.closest("[data-waitlist-close]")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.classList.contains("is-open")) {
      closeModal();
    }
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-catalog], [data-burger], [data-search-open], [data-mobile-search-btn]")) {
      closeModal(false);
    }
  });

  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (!event.target) {
      return;
    }
    if (event.target.id === "waitlist-form-slot" || event.target.id === "waitlist-modal-body") {
      markSeen();
    }
    if (event.target.id === "waitlist-modal-body" && event.target.querySelector("[data-waitlist-success]")) {
      window.setTimeout(closeModal, 2200);
    }
  });

  if (alreadySeen()) {
    return;
  }

  const remaining = Math.max(0, delayMs - (Date.now() - startedAt()));
  timerId = window.setTimeout(openModal, remaining);
  window.addEventListener(
    "pagehide",
    () => {
      window.clearTimeout(timerId);
    },
    { once: true }
  );
})();

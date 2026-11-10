(function () {
  const root = document.querySelector("[data-nd-cat]");
  if (!root) {
    return;
  }

  const form = root.querySelector("[data-nd-cat-form]");
  const filtersBtn = root.querySelector("[data-nd-filters-toggle]");
  const nativeSort = root.querySelector("[data-nd-sort-native]");

  root.classList.add("is-ready");

  // Макет застосовує фільтри без перезавантаження: прокрутка панелі (sticky aside) і сторінки лишається.
  // У нас звичайний GET — зберігаємо й відновлюємо обидві позиції один раз після «Застосувати».
  const aside = root.querySelector(".nd-cat__aside");
  const SCROLL_KEY = "nd-cat-scroll";
  try {
    const saved = JSON.parse(sessionStorage.getItem(SCROLL_KEY) || "null");
    sessionStorage.removeItem(SCROLL_KEY);
    if (saved && saved.path === location.pathname) {
      if (aside) {
        aside.scrollTop = saved.aside || 0;
      }
      window.scrollTo(0, saved.page || 0);
    }
  } catch (error) {
    /* sessionStorage недоступний — без відновлення */
  }
  if (form) {
    form.addEventListener("submit", () => {
      try {
        sessionStorage.setItem(
          SCROLL_KEY,
          JSON.stringify({ path: location.pathname, aside: aside ? aside.scrollTop : 0, page: window.scrollY }),
        );
      } catch (error) {
        /* ignore */
      }
    });
  }

  function setFiltersOpen(open) {
    root.classList.toggle("is-filters-open", open);
    if (filtersBtn) {
      filtersBtn.setAttribute("aria-expanded", open ? "true" : "false");
    }
  }

  function closeSortMenus(except) {
    root.querySelectorAll("[data-nd-sort]").forEach((node) => {
      if (except && node === except) {
        return;
      }
      const menu = node.querySelector("[data-nd-sort-menu]");
      const btn = node.querySelector("[data-nd-sort-open]");
      if (menu) {
        menu.hidden = true;
      }
      node.classList.remove("is-open");
      if (btn) {
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  function applySort(value) {
    if (!nativeSort || !form) {
      return;
    }
    nativeSort.value = value || "";
    root.querySelectorAll("[data-nd-sort-label]").forEach((label) => {
      const active = root.querySelector(`[data-nd-sort-value="${value}"]`);
      if (active) {
        label.textContent = active.textContent;
      }
    });
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }

  if (filtersBtn) {
    filtersBtn.addEventListener("click", () => {
      const open = !root.classList.contains("is-filters-open");
      closeSortMenus();
      setFiltersOpen(open);
    });
  }

  root.addEventListener("click", (event) => {
    const opener = event.target.closest("[data-nd-sort-open]");
    if (opener && root.contains(opener)) {
      const sortRoot = opener.closest("[data-nd-sort]");
      if (!sortRoot) {
        return;
      }
      const menu = sortRoot.querySelector("[data-nd-sort-menu]");
      const willOpen = menu && menu.hidden;
      closeSortMenus(sortRoot);
      if (menu) {
        menu.hidden = !willOpen;
      }
      sortRoot.classList.toggle("is-open", Boolean(willOpen));
      opener.setAttribute("aria-expanded", willOpen ? "true" : "false");
      return;
    }

    const option = event.target.closest("[data-nd-sort-value]");
    if (option && root.contains(option)) {
      event.preventDefault();
      closeSortMenus();
      applySort(option.getAttribute("data-nd-sort-value") || "");
      return;
    }

    if (!event.target.closest("[data-nd-sort]")) {
      closeSortMenus();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    closeSortMenus();
    if (root.classList.contains("is-filters-open") && window.matchMedia("(max-width: 699px)").matches) {
      setFiltersOpen(false);
    }
  });

  if (nativeSort) {
    nativeSort.addEventListener("change", () => {
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
      } else {
        form.submit();
      }
    });
  }
})();

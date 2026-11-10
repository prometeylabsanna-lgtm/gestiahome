(function () {
  const root = document.querySelector("[data-nd-cat]");
  if (!root) {
    return;
  }

  const form = root.querySelector("[data-nd-cat-form]");
  const filtersBtn = root.querySelector("[data-nd-filters-toggle]");
  const nativeSort = root.querySelector("[data-nd-sort-native]");

  root.classList.add("is-ready");

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

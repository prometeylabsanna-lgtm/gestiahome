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

  function syncSortUi(value) {
    const next = value || "";
    if (nativeSort) {
      nativeSort.value = next;
    }
    root.querySelectorAll("[data-nd-sort-value]").forEach((btn) => {
      const on = (btn.getAttribute("data-nd-sort-value") || "") === next;
      btn.classList.toggle("is-active", on);
      const option = btn.closest("[role='option']");
      if (option) {
        option.setAttribute("aria-selected", on ? "true" : "false");
      }
    });
    root.querySelectorAll("[data-nd-sort-label]").forEach((label) => {
      const active = root.querySelector(`[data-nd-sort-value="${next}"]`);
      if (active) {
        label.textContent = active.textContent;
      }
    });
  }

  function applySort(value) {
    if (!form) {
      return;
    }
    const next = value || "";
    syncSortUi(next);
    const params = new URLSearchParams(new FormData(form));
    if (next) {
      params.set("sort", next);
    } else {
      params.delete("sort");
    }
    const action = form.getAttribute("action") || window.location.pathname;
    const query = params.toString();
    const url = query ? `${action}?${query}` : action;
    if (window.htmx) {
      window.htmx.ajax("GET", url, {
        target: "#catalog-results",
        swap: "innerHTML",
        push: url,
      });
      return;
    }
    window.location.assign(url);
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
      applySort(nativeSort.value || "");
    });
  }
})();

(function () {
  var KEY_REGION = "gestia.region";
  var KEY_NEXT = "gestia.region.next";
  var header = document.querySelector("[data-nd-header]");
  if (!header) return;

  var burgerBtn = header.querySelector("[data-burger]");
  var burger = document.querySelector("[data-burger-panel]");
  var catalogBtn = header.querySelector("[data-catalog]");
  var mega = header.querySelector("[data-mega]");
  var region = header.querySelector("[data-region]");
  var searchBtn = header.querySelector("[data-search-open]");
  var searchForm = header.querySelector("[data-search-form]");
  var searchInput = header.querySelector("[data-search-input]");
  var mobileSearchBtn = header.querySelector("[data-mobile-search-btn]");
  var mobileSearch = header.querySelector("[data-mobile-search]");
  var mobileSearchInput = header.querySelector("[data-mobile-search-input]");
  var scrollY = 0;
  var locked = false;

  function read(key) {
    try {
      return localStorage.getItem(key);
    } catch (err) {
      return null;
    }
  }

  function write(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (err) {}
  }

  function readSession(key) {
    try {
      return sessionStorage.getItem(key);
    } catch (err) {
      return null;
    }
  }

  function writeSession(key, value) {
    try {
      if (value == null) sessionStorage.removeItem(key);
      else sessionStorage.setItem(key, value);
    } catch (err) {}
  }

  function flag(node, open) {
    if (!node) return;
    node.hidden = !open;
  }

  function lock(open) {
    if (open) {
      if (locked) return;
      locked = true;
      scrollY = window.scrollY || window.pageYOffset || 0;
      document.body.classList.add("nav-lock");
      document.body.style.top = "-" + scrollY + "px";
      return;
    }
    if (!locked) return;
    locked = false;
    document.body.classList.remove("nav-lock");
    document.body.style.top = "";
    window.scrollTo(0, scrollY);
  }

  function syncLock() {
    var need =
      (burger && !burger.hidden) ||
      (mega && !mega.hidden) ||
      (mobileSearch && !mobileSearch.hidden);
    lock(need);
  }

  function setBurgerIcons(open) {
    if (!burgerBtn) return;
    var openIcon = burgerBtn.querySelector(".nd-header__burger-open");
    var closeIcon = burgerBtn.querySelector(".nd-header__burger-close");
    if (openIcon) openIcon.hidden = !!open;
    if (closeIcon) closeIcon.hidden = !open;
    burgerBtn.setAttribute("aria-expanded", open ? "true" : "false");
    burgerBtn.setAttribute(
      "aria-label",
      open ? burgerBtn.getAttribute("data-label-close") || "Закрити меню" : burgerBtn.getAttribute("data-label-open") || "Меню"
    );
  }

  function setBurger(open) {
    flag(burger, open);
    document.body.classList.toggle("is-burger", open);
    setBurgerIcons(open);
    if (open) {
      setMega(false);
      setMobileSearch(false);
      setDeskSearch(false);
    }
    syncLock();
  }

  function setMega(open) {
    flag(mega, open);
    document.body.classList.toggle("is-mega", open);
    if (catalogBtn) catalogBtn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      setBurger(false);
      setDeskSearch(false);
      setRegion(false);
    }
    syncLock();
  }

  function setDeskSearch(open) {
    if (!searchBtn || !searchForm) return;
    flag(searchForm, open);
    searchBtn.hidden = !!open;
    searchBtn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open && searchInput) {
      window.setTimeout(function () {
        searchInput.focus();
      }, 0);
    }
  }

  function setMobileSearch(open) {
    flag(mobileSearch, open);
    if (mobileSearchBtn) mobileSearchBtn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      setBurger(false);
      setMega(false);
      if (mobileSearchInput) {
        window.setTimeout(function () {
          mobileSearchInput.focus();
        }, 0);
      }
    }
    syncLock();
  }

  function regionChosen() {
    return !!read(KEY_REGION);
  }

  function showRegionStep(step) {
    if (!region) return;
    region.querySelectorAll("[data-region-step]").forEach(function (node) {
      node.hidden = node.getAttribute("data-region-step") !== step;
    });
    var closeBtn = region.querySelector("[data-region-close]");
    if (closeBtn) closeBtn.hidden = !regionChosen();
  }

  function setRegion(open, step) {
    if (!region) return;
    flag(region, open);
    document.querySelectorAll("[data-region-open]").forEach(function (btn) {
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    if (open) {
      showRegionStep(step || "confirm");
      setMega(false);
    }
  }

  if (burgerBtn) {
    burgerBtn.addEventListener("click", function () {
      setBurger(!(burger && !burger.hidden));
    });
  }

  if (catalogBtn) {
    catalogBtn.addEventListener("click", function () {
      setMega(!(mega && !mega.hidden));
    });
  }

  header.querySelectorAll("[data-catalog-close]").forEach(function (node) {
    node.addEventListener("click", function () {
      setMega(false);
    });
  });

  if (searchBtn) {
    searchBtn.addEventListener("click", function () {
      setMega(false);
      setDeskSearch(true);
    });
  }

  if (searchInput) {
    searchInput.addEventListener("blur", function () {
      if (!searchInput.value) setDeskSearch(false);
    });
  }

  if (mobileSearchBtn) {
    mobileSearchBtn.addEventListener("click", function () {
      setMobileSearch(!(mobileSearch && !mobileSearch.hidden));
    });
  }

  header.querySelectorAll("[data-mobile-search-close]").forEach(function (node) {
    node.addEventListener("click", function () {
      setMobileSearch(false);
    });
  });

  document.querySelectorAll("[data-region-open]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setRegion(true, "confirm");
      if (burger && !burger.hidden) setBurger(false);
    });
  });

  if (region) {
    var closeBtn = region.querySelector("[data-region-close]");
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        if (regionChosen()) setRegion(false);
      });
    }

    var confirmBtn = region.querySelector("[data-region-confirm]");
    if (confirmBtn) {
      confirmBtn.addEventListener("click", function () {
        write(KEY_REGION, "ua");
        var cur = region.getAttribute("data-currency") || "uah";
        if (cur !== "uah") {
          var form = region.querySelector("#region-confirm-currency");
          if (form) {
            form.submit();
            return;
          }
        }
        setRegion(false);
      });
    }

    var toRegion = region.querySelector("[data-region-to-region]");
    if (toRegion) {
      toRegion.addEventListener("click", function () {
        showRegionStep("region");
      });
    }

    region.querySelectorAll("[data-region-pick]").forEach(function (form) {
      form.addEventListener("submit", function () {
        write(KEY_REGION, form.getAttribute("data-region-pick") || "ua");
        writeSession(KEY_NEXT, "lang");
      });
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    setMega(false);
    setMobileSearch(false);
    setDeskSearch(false);
    if (burger && !burger.hidden) setBurger(false);
    if (region && !region.hidden && regionChosen()) setRegion(false);
  });

  function setMenuGroup(group, open) {
    if (!group) return;
    group.classList.toggle("is-open", open);
    if (open) group.setAttribute("data-open", "");
    else group.removeAttribute("data-open");
    var btn = group.querySelector("[data-menu-group-toggle]");
    var list = group.querySelector(".nd-mega__group-items, .nd-burger__group-items");
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
    if (list) list.hidden = !open;
  }

  function onMenuGroupToggle(event) {
    var toggle = event.target.closest("[data-menu-group-toggle]");
    if (!toggle) return false;
    var group = toggle.closest("[data-menu-group]");
    var root = toggle.closest("[data-menu-groups]");
    if (!group || !root) return true;
    var willOpen = toggle.getAttribute("aria-expanded") !== "true";
    root.querySelectorAll("[data-menu-group]").forEach(function (node) {
      setMenuGroup(node, willOpen && node === group);
    });
    return true;
  }

  if (burger) {
    burger.addEventListener("click", function (event) {
      var toggle = event.target.closest("[data-burger-catalog-toggle]");
      if (toggle) {
        var block = toggle.closest("[data-burger-catalog]");
        if (!block) return;
        var open = toggle.getAttribute("aria-expanded") !== "true";
        block.classList.toggle("is-collapsed", !open);
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        return;
      }
      if (onMenuGroupToggle(event)) return;
      if (event.target.closest("a")) setBurger(false);
    });
  }

  if (mega) {
    mega.addEventListener("click", function (event) {
      if (onMenuGroupToggle(event)) return;
      if (event.target.closest("a")) setMega(false);
    });
  }

  window.addEventListener(
    "scroll",
    function () {
      if (mega && !mega.hidden) setMega(false);
    },
    { passive: true }
  );

  document.addEventListener("click", function (event) {
    if (!region || region.hidden) return;
    if (event.target.closest("[data-region]") || event.target.closest("[data-region-open]")) return;
    if (regionChosen()) setRegion(false);
  });

  var nextStep = readSession(KEY_NEXT);
  if (nextStep === "lang" && region) {
    writeSession(KEY_NEXT, null);
    setRegion(true, "lang");
  } else if (!regionChosen() && region) {
    setRegion(true, "confirm");
  }
})();

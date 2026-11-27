(function () {
  function bind(list, input, hooks) {
    const options = hooks || {};
    let rows = [];
    let active = -1;
    let onPick = function () {};

    function setActive(index) {
      const items = list.querySelectorAll(".co-suggest__item");
      if (!items.length) {
        active = -1;
        input.removeAttribute("aria-activedescendant");
        return;
      }
      if (index < 0) {
        index = items.length - 1;
      }
      if (index >= items.length) {
        index = 0;
      }
      active = index;
      items.forEach(function (item, itemIndex) {
        const on = itemIndex === active;
        item.classList.toggle("is-active", on);
        item.setAttribute("aria-selected", on ? "true" : "false");
        if (on) {
          input.setAttribute("aria-activedescendant", item.id);
          item.scrollIntoView({ block: "nearest" });
        }
      });
    }

    function close() {
      list.hidden = true;
      list.replaceChildren();
      rows = [];
      active = -1;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    }

    function open(nextRows, pick) {
      rows = nextRows || [];
      onPick = typeof pick === "function" ? pick : function () {};
      active = -1;
      list.replaceChildren();
      if (!rows.length) {
        close();
        return;
      }
      rows.forEach(function (row, index) {
        const option = document.createElement("li");
        option.className = "co-suggest__item";
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", "false");
        option.id = list.id + "-opt-" + index;
        option.textContent = row.caption || row.label;
        option.addEventListener("pointerdown", function (event) {
          event.preventDefault();
          onPick(row);
        });
        list.appendChild(option);
      });
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
    }

    input.addEventListener("keydown", function (event) {
      if (list.hidden) {
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActive(active + 1);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setActive(active < 0 ? rows.length - 1 : active - 1);
        return;
      }
      if (event.key === "Enter" && rows.length) {
        event.preventDefault();
        const row = rows[active >= 0 ? active : 0];
        if (row) {
          onPick(row);
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        if (typeof options.onEscape === "function") {
          options.onEscape();
        }
      }
    });

    return { open: open, close: close };
  }

  window.gestiaSuggest = { bind: bind };
})();

(function () {
  var forms = document.querySelectorAll("[data-search-form][data-suggest-url]");
  if (!forms.length) return;

  forms.forEach(function (form) {
    var input = form.querySelector("input[name='q']");
    var list = form.querySelector(".nd-search-suggest");
    var url = form.getAttribute("data-suggest-url");
    if (!input || !list || !url) return;

    var timer = 0;
    var active = -1;
    var request = null;

    function hide() {
      list.hidden = true;
      list.replaceChildren();
      active = -1;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    }

    function links() {
      return list.querySelectorAll(".nd-search-suggest__link");
    }

    function mark(index) {
      var nodes = links();
      active = index;
      nodes.forEach(function (node, i) {
        var on = i === index;
        node.classList.toggle("is-active", on);
        if (on) input.setAttribute("aria-activedescendant", node.id);
      });
      if (index < 0) input.removeAttribute("aria-activedescendant");
    }

    function show(items) {
      list.replaceChildren();
      active = -1;
      input.removeAttribute("aria-activedescendant");
      if (!items.length) {
        hide();
        return;
      }
      items.forEach(function (item, index) {
        var li = document.createElement("li");
        var link = document.createElement("a");
        link.className = "nd-search-suggest__link";
        link.href = item.url;
        link.id = list.id + "-" + index;
        link.setAttribute("role", "option");
        if (item.image) {
          var img = document.createElement("img");
          img.className = "nd-search-suggest__img";
          img.src = item.image;
          img.alt = "";
          img.width = 40;
          img.height = 48;
          link.appendChild(img);
        }
        var text = document.createElement("span");
        text.className = "nd-search-suggest__text";
        var name = document.createElement("span");
        name.className = "nd-search-suggest__name";
        name.textContent = item.name || "";
        var price = document.createElement("span");
        price.className = "nd-search-suggest__price";
        price.textContent = item.price || "";
        text.append(name, price);
        link.append(text);
        li.appendChild(link);
        list.appendChild(li);
      });
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
    }

    function load() {
      var query = input.value.trim();
      if (query.length < 2) {
        hide();
        return;
      }
      if (request) request.abort();
      request = new AbortController();
      var current = request;
      fetch(url + "?q=" + encodeURIComponent(query), {
        headers: { Accept: "application/json" },
        signal: current.signal,
      })
        .then(function (response) {
          if (!response.ok) throw new Error("suggest");
          return response.json();
        })
        .then(function (data) {
          if (current !== request) return;
          if (input.value.trim() !== query) return;
          show((data && data.items) || []);
        })
        .catch(function (error) {
          if (error && error.name === "AbortError") return;
          hide();
        });
    }

    input.addEventListener("input", function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(load, 180);
    });

    input.addEventListener("keydown", function (event) {
      var nodes = links();
      if (event.key === "ArrowDown" && nodes.length) {
        event.preventDefault();
        mark(Math.min(active + 1, nodes.length - 1));
        return;
      }
      if (event.key === "ArrowUp" && nodes.length) {
        event.preventDefault();
        mark(Math.max(active - 1, 0));
        return;
      }
      if (event.key === "Escape") {
        hide();
        return;
      }
      if (event.key === "Enter" && active >= 0 && nodes[active]) {
        event.preventDefault();
        window.location.assign(nodes[active].href);
      }
    });

    input.addEventListener("blur", function () {
      window.setTimeout(function () {
        if (!form.contains(document.activeElement)) hide();
      }, 180);
    });
  });
})();

(function () {
  "use strict";

  var SKIP = {
    hidden: 1,
    file: 1,
    checkbox: 1,
    radio: 1,
    button: 1,
    submit: 1,
    color: 1,
    range: 1,
    password: 1,
  };

  function maxOf(field) {
    var max = parseInt(field.getAttribute("maxlength"), 10);
    return max > 0 ? max : 0;
  }

  function stripTags(html) {
    var node = document.createElement("div");
    node.innerHTML = html || "";
    return (node.textContent || node.innerText || "").replace(/\u00a0/g, " ");
  }

  function visibleLen(value, visible) {
    if (!visible) return (value || "").length;
    return stripTags(value).length;
  }

  function clamp(field, max) {
    if (field.value.length <= max) return;
    var pos = field.selectionStart;
    field.value = field.value.slice(0, max);
    if (typeof pos === "number" && field.setSelectionRange) {
      var next = Math.min(pos, max);
      try {
        field.setSelectionRange(next, next);
      } catch (error) {
        return;
      }
    }
  }

  function paint(counter, length, max) {
    counter.textContent = length + " / " + max;
    counter.classList.toggle("is-warn", length >= Math.floor(max * 0.9));
  }

  function place(field, counter) {
    var tiny = field.closest && field.closest(".form-row");
    if (tiny) {
      var host = tiny.querySelector(".tox-tinymce");
      if (host) {
        host.insertAdjacentElement("afterend", counter);
        return;
      }
    }
    var parent = field.parentNode;
    if (parent && parent !== document.body && parent.children.length <= 3) {
      parent.insertAdjacentElement("afterend", counter);
      return;
    }
    field.insertAdjacentElement("afterend", counter);
  }

  function isTinyTextarea(field) {
    if (!field) return false;
    if (field.dataset && field.dataset.mceConf) return true;
    if (field.classList && field.classList.contains("tinymce")) return true;
    return false;
  }

  function bindField(field) {
    if (!field || field.dataset.gestiaCount === "1") return;
    if (field.closest && field.closest(".tox-tinymce")) return;
    // TinyMCE textarea must not get a plain counter as a flex sibling —
    // that squeezes .tox-tinymce to ~100px. Counters attach via bindTiny.
    if (isTinyTextarea(field)) return;
    var type = (field.getAttribute("type") || "").toLowerCase();
    if (SKIP[type]) return;
    var max = maxOf(field);
    if (!max) return;
    field.dataset.gestiaCount = "1";
    field.setAttribute("maxlength", String(max));
    var visible = field.getAttribute("data-gestia-visible-count") === "1";

    var counter = document.createElement("span");
    counter.className = "gestia-char-count";
    counter.setAttribute("aria-live", "polite");
    place(field, counter);

    function updatePlain() {
      if (!visible) clamp(field, max);
      paint(counter, visibleLen(field.value, visible), max);
    }

    field.addEventListener("beforeinput", function (event) {
      if (visible) return;
      var kind = event.inputType || "";
      if (!kind || kind.indexOf("delete") === 0 || kind.toLowerCase().indexOf("composition") !== -1) return;
      var data = event.data || "";
      if (!data) return;
      var start = field.selectionStart;
      var end = field.selectionEnd;
      if (start == null || end == null) return;
      var room = max - (field.value.length - (end - start));
      if (data.length <= room) return;
      event.preventDefault();
      if (room > 0 && field.setRangeText) {
        field.setRangeText(data.slice(0, room), start, end, "end");
      }
      updatePlain();
    });
    field.addEventListener("input", updatePlain);
    field.addEventListener("change", updatePlain);
    field.addEventListener("compositionend", updatePlain);
    field.addEventListener("paste", function () {
      window.setTimeout(updatePlain, 0);
    });
    updatePlain();
    field._gestiaPaint = updatePlain;
  }

  function bindTiny(editor) {
    if (!editor || !editor.targetElm) return;
    var field = editor.targetElm;
    if (field.dataset.gestiaTinyCount === "1") return;
    var max = maxOf(field);
    if (!max) return;
    field.dataset.gestiaTinyCount = "1";
    field.dataset.gestiaCount = "1";
    var visible = true;
    field.setAttribute("data-gestia-visible-count", "1");

    var counter = document.createElement("span");
    counter.className = "gestia-char-count";
    counter.setAttribute("aria-live", "polite");
    var host = editor.getContainer ? editor.getContainer() : null;
    // Keep counter inside the Unfold field column (.grow.relative), under the editor.
    if (host && host.parentNode) {
      host.insertAdjacentElement("afterend", counter);
    } else {
      place(field, counter);
    }
    try {
      if (host) {
        host.style.width = "100%";
        host.style.maxWidth = "100%";
      }
      if (editor.iframeElement) editor.iframeElement.style.width = "100%";
    } catch (err) {}

    function update() {
      var html = editor.getContent({ format: "html" }) || "";
      paint(counter, visibleLen(html, visible), max);
    }

    editor.on("input SetContent Undo Redo KeyUp Change", update);
    editor.on("init", function () {
      window.setTimeout(update, 0);
    });
    update();
    field._gestiaPaint = update;
  }

  function eachEditor(fn) {
    if (!window.tinymce) return;
    var seen = {};
    var list = window.tinymce.editors;
    if (list && typeof list.forEach === "function") {
      list.forEach(function (ed) {
        if (!ed || !ed.id || seen[ed.id]) return;
        seen[ed.id] = 1;
        try {
          fn(ed);
        } catch (err) {}
      });
    }
    document.querySelectorAll("textarea.tinymce, textarea[data-mce-conf]").forEach(function (el) {
      if (!el.id || seen[el.id]) return;
      var ed = null;
      try {
        ed = window.tinymce.get(el.id);
      } catch (err) {
        ed = null;
      }
      if (!ed) return;
      seen[el.id] = 1;
      try {
        fn(ed);
      } catch (err) {}
    });
  }

  function bindTinies() {
    eachEditor(bindTiny);
  }

  function refreshTinyLayout() {
    eachEditor(function (ed) {
      try {
        ed.dispatch("ResizeEditor");
        if (ed.iframeElement) ed.iframeElement.style.width = "100%";
        if (ed.getContainer) {
          var host = ed.getContainer();
          if (host) {
            host.style.width = "100%";
            host.style.maxWidth = "100%";
          }
        }
        if (ed.targetElm && ed.targetElm._gestiaPaint) ed.targetElm._gestiaPaint();
      } catch (err) {}
    });
  }

  function hookTiny() {
    if (!window.tinymce || !window.tinymce.on || window._gestiaTinyHooked) return !!window._gestiaTinyHooked;
    window._gestiaTinyHooked = true;
    window.tinymce.on("AddEditor", function (event) {
      window.setTimeout(function () {
        bindTiny(event.editor);
        refreshTinyLayout();
      }, 50);
    });
    return true;
  }

  function bind(root) {
    var scope = root || document;
    scope.querySelectorAll("input[maxlength], textarea[maxlength]").forEach(bindField);
    hookTiny();
    bindTinies();
  }

  function start() {
    bind(document);
    window.setTimeout(bindTinies, 400);
    window.setTimeout(bindTinies, 1200);
    window.setTimeout(hookTiny, 0);
    window.setTimeout(hookTiny, 400);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }

  document.addEventListener("formset:added", function (event) {
    bind(event.target || document);
  });
  document.addEventListener("htmx:afterSettle", function (event) {
    bind(event.target || document);
  });
  document.addEventListener("click", function (event) {
    var tab = event.target.closest("[role='tab'], .unfold-tab-list a, .unfold-tab-list button, [data-tabs-target]");
    if (!tab) return;
    window.setTimeout(function () {
      bindTinies();
      refreshTinyLayout();
    }, 80);
    window.setTimeout(refreshTinyLayout, 250);
  });
})();

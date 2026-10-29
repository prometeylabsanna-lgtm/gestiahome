(function () {
  const UK = {
    required: "Поле обов'язкове для заповнення",
    name: "Ім'я не може містити цифри або спецсимволи. Будь ласка, використовуйте лише букви",
    nameShort: "Занадто коротке значення",
    phone: "Введіть коректний номер мобільного телефону у форматі +380 (XX) XXX-XX-XX",
    email: "Некоректний формат",
  };
  const EN = {
    required: "This field is required",
    name: "The name cannot contain digits or special characters. Please use letters only",
    nameShort: "The value is too short",
    phone: "Enter a valid mobile number in the format +380 (XX) XXX-XX-XX",
    email: "Invalid format",
  };
  const DEFAULTS = (document.documentElement.lang || "").toLowerCase().startsWith("en") ? EN : UK;
  const NAME_LETTERS = "A-Za-zА-Яа-яЁёІіЇїЄєҐґ";
  const NAME_PATTERN = "[" + NAME_LETTERS + "]+(?:['\u2019\u02bc -][" + NAME_LETTERS + "]+)*";
  const NAME_OK = new RegExp("^" + NAME_PATTERN + "$");
  const NAME_LETTER = new RegExp("[" + NAME_LETTERS + "]", "g");
  const UA_MOBILE_CODES = [
    "39", "50", "63", "66", "67", "68", "73", "77",
    "91", "92", "93", "94", "95", "96", "97", "98", "99",
  ];
  const PHONE_PATTERN = "\\+38 \\(0(?:" + UA_MOBILE_CODES.join("|") + ")\\) \\d{3}-\\d{2}-\\d{2}";
  const EMAIL_OK = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function formOf(el) {
    return el.closest("[data-validate-form]");
  }

  function msg(form, key) {
    const map = {
      required: form && form.dataset.msgRequired,
      name: form && form.dataset.msgName,
      nameShort: form && form.dataset.msgNameShort,
      phone: form && form.dataset.msgPhone,
      email: form && form.dataset.msgEmail,
    };
    return map[key] || DEFAULTS[key];
  }

  function wrapOf(input) {
    return input.closest("[data-field-wrap]") || input;
  }

  function errorOf(form, input) {
    if (!form || !input || !input.name) {
      return null;
    }
    const described = input.getAttribute("aria-describedby");
    if (described) {
      const byId = document.getElementById(described);
      if (byId) {
        return byId;
      }
    }
    return (
      form.querySelector('[data-error-for="' + input.name + '"]') ||
      wrapOf(input).querySelector("[data-field-error]")
    );
  }

  function setState(form, input, errorText) {
    const wrap = wrapOf(input);
    const hint = errorOf(form, input);
    const invalid = Boolean(errorText);
    wrap.classList.toggle("is-invalid", invalid);
    wrap.classList.toggle("is-valid", !invalid && hasValue(input));
    input.classList.toggle("is-invalid", invalid);
    input.classList.toggle("is-valid", !invalid && hasValue(input));
    input.setAttribute("aria-invalid", invalid ? "true" : "false");
    if (!hint) {
      return;
    }
    hint.textContent = errorText || "";
    hint.hidden = !invalid;
  }

  function clearState(form, input) {
    const wrap = wrapOf(input);
    wrap.classList.remove("is-invalid", "is-valid");
    input.classList.remove("is-invalid", "is-valid");
    input.removeAttribute("aria-invalid");
    const hint = errorOf(form, input);
    if (hint) {
      hint.textContent = "";
      hint.hidden = true;
    }
  }

  function hasValue(input) {
    if (input.type === "checkbox") {
      return input.checked;
    }
    return Boolean(String(input.value || "").trim());
  }

  function kindOf(input) {
    return input.getAttribute("data-validate") || "";
  }

  function phoneBodyDigits(value) {
    let digits = String(value || "").replace(/\D/g, "");
    if (!digits) {
      return "";
    }
    if (digits.startsWith("380")) {
      digits = digits.slice(3);
    } else if (digits.startsWith("38")) {
      digits = digits.slice(2);
    }
    if (!digits) {
      return "";
    }
    if (!digits.startsWith("0")) {
      digits = "0" + digits;
    }
    return digits.slice(0, 10);
  }

  function uaPhoneDigits(value) {
    const body = phoneBodyDigits(value);
    if (body.startsWith("0")) {
      return body.slice(1);
    }
    return body;
  }

  function formatUaPhone(value) {
    const body = phoneBodyDigits(value);
    if (!body) {
      return "";
    }
    let out = "+38 (" + body.slice(0, Math.min(3, body.length));
    if (body.length >= 3) {
      out += ")";
    }
    if (body.length > 3) {
      out += " " + body.slice(3, 6);
    }
    if (body.length > 6) {
      out += "-" + body.slice(6, 8);
    }
    if (body.length > 8) {
      out += "-" + body.slice(8, 10);
    }
    return out;
  }

  function isUaPhone(value) {
    const national = uaPhoneDigits(value);
    if (national.length !== 9) {
      return false;
    }
    return UA_MOBILE_CODES.indexOf(national.slice(0, 2)) !== -1;
  }

  function setPhoneCaretEnd(input) {
    if (typeof input.setSelectionRange !== "function" || input.type === "number") {
      return;
    }
    const end = String(input.value || "").length;
    try {
      input.setSelectionRange(end, end);
    } catch (_err) {
      /* iOS Safari can ignore caret moves on type=tel */
    }
  }

  function syncPhoneField(input) {
    applyPhoneMask(input);
    const form = formOf(input);
    if (!form) {
      return;
    }
    if (input.dataset.touched === "1" || form.dataset.submitted === "1") {
      setState(form, input, validateInput(form, input));
    }
  }

  function onPhoneKeyDown(event) {
    if (event.key !== "Backspace" && event.key !== "Delete") {
      return;
    }
    const input = event.target;
    if (!input || kindOf(input) !== "phone") {
      return;
    }
    const start = input.selectionStart;
    const end = input.selectionEnd;
    if (start == null || end == null || start !== end) {
      return;
    }
    const value = String(input.value || "");
    if (!value) {
      return;
    }
    if (event.key === "Backspace") {
      if (start === 0) {
        return;
      }
      const prev = value.charAt(start - 1);
      if (/\d/.test(prev)) {
        return;
      }
      event.preventDefault();
      const body = phoneBodyDigits(value).slice(0, -1);
      input.value = formatUaPhone(body);
      setPhoneCaretEnd(input);
      syncPhoneField(input);
      return;
    }
    const next = value.charAt(start);
    if (!next || /\d/.test(next)) {
      return;
    }
    event.preventDefault();
    const body = phoneBodyDigits(value).slice(0, -1);
    input.value = formatUaPhone(body);
    setPhoneCaretEnd(input);
    syncPhoneField(input);
  }

  function normalizeName(value) {
    return String(value || "").trim().replace(/\s+/g, " ");
  }

  function validateInput(form, input) {
    const kind = kindOf(input);
    if (!kind) {
      return "";
    }
    const value = String(input.value || "").trim();
    if (kind === "consent") {
      return input.checked ? "" : msg(form, "required");
    }
    if (!value) {
      return msg(form, "required");
    }
    if (kind === "name") {
      const name = normalizeName(value);
      if (!NAME_OK.test(name)) {
        return msg(form, "name");
      }
      const letters = name.match(NAME_LETTER) || [];
      if (letters.length < 2) {
        return msg(form, "nameShort");
      }
      return "";
    }
    if (kind === "phone") {
      return isUaPhone(value) ? "" : msg(form, "phone");
    }
    if (kind === "email") {
      return EMAIL_OK.test(value) ? "" : msg(form, "email");
    }
    return "";
  }

  function fieldsOf(form) {
    return Array.prototype.slice.call(form.querySelectorAll("[data-validate]"));
  }

  function applyPhoneMask(input) {
    const next = formatUaPhone(input.value);
    if (input.value === next) {
      return;
    }
    input.value = next;
    setPhoneCaretEnd(input);
  }

  function clipboardText(event) {
    const clipboard = event.clipboardData || window.clipboardData;
    if (!clipboard || typeof clipboard.getData !== "function") {
      return "";
    }
    const kinds = ["text/plain", "text"];
    for (let i = 0; i < kinds.length; i += 1) {
      try {
        const value = clipboard.getData(kinds[i]);
        if (value) {
          return value;
        }
      } catch (_err) {
        /* iOS Safari may reject one MIME type */
      }
    }
    return "";
  }

  function isCompletePhonePaste(text) {
    const digits = String(text || "").replace(/\D/g, "");
    if (digits.startsWith("380") && digits.length === 12) {
      return true;
    }
    if (digits.startsWith("0") && digits.length === 10) {
      return true;
    }
    return digits.length === 9;
  }

  function onPaste(event) {
    const input = event.target;
    if (!input || kindOf(input) !== "phone") {
      return;
    }
    const text = clipboardText(event);
    if (!isCompletePhonePaste(text)) {
      return;
    }
    event.preventDefault();
    input.value = text;
    applyPhoneMask(input);
    const form = formOf(input);
    if (!form) {
      return;
    }
    if (input.dataset.touched === "1" || form.dataset.submitted === "1") {
      setState(form, input, validateInput(form, input));
    }
  }

  function onInput(event) {
    const input = event.target;
    if (!input || !input.hasAttribute("data-validate")) {
      return;
    }
    const form = formOf(input);
    if (!form) {
      return;
    }
    if (kindOf(input) === "phone") {
      applyPhoneMask(input);
    }
    if (input.dataset.touched === "1" || form.dataset.submitted === "1") {
      setState(form, input, validateInput(form, input));
    }
  }

  function onBlur(event) {
    const input = event.target;
    if (!input || !input.hasAttribute("data-validate")) {
      return;
    }
    const form = formOf(input);
    if (!form) {
      return;
    }
    if (!hasValue(input) && input.dataset.touched !== "1" && form.dataset.submitted !== "1") {
      clearState(form, input);
      return;
    }
    input.dataset.touched = "1";
    setState(form, input, validateInput(form, input));
  }

  function armOnce(form) {
    if (!form.hasAttribute("data-once")) {
      return;
    }
    form.dataset.onceLock = "1";
    const button = form.querySelector("[type='submit']");
    // Disable after the event so iOS Safari still sends the first POST.
    window.setTimeout(function () {
      if (button) {
        button.disabled = true;
      }
    }, 0);
  }

  function releaseOnce() {
    document.querySelectorAll("form[data-once]").forEach((form) => {
      delete form.dataset.onceLock;
      form.querySelectorAll("[type='submit']").forEach((button) => {
        button.disabled = false;
      });
    });
  }

  function onSubmit(event) {
    const form = event.target;
    if (!form || !form.hasAttribute("data-validate-form")) {
      return;
    }
    if (form.dataset.onceLock === "1") {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    form.dataset.submitted = "1";
    let firstInvalid = null;
    fieldsOf(form).forEach((input) => {
      const errorText = validateInput(form, input);
      setState(form, input, errorText);
      if (errorText && !firstInvalid) {
        firstInvalid = input;
      }
    });
    if (!firstInvalid) {
      armOnce(form);
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    if (typeof firstInvalid.focus === "function") {
      firstInvalid.focus();
    }
    if (typeof firstInvalid.scrollIntoView === "function") {
      firstInvalid.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }

  function hydratePhones(root) {
    const scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll('[data-validate="name"]').forEach((input) => {
      input.setAttribute("pattern", NAME_PATTERN);
    });
    scope.querySelectorAll('[data-validate="phone"]').forEach((input) => {
      input.setAttribute("pattern", PHONE_PATTERN);
      if (input.value) {
        applyPhoneMask(input);
      }
    });
  }

  document.addEventListener("keydown", onPhoneKeyDown, true);
  document.addEventListener("input", onInput, true);
  document.addEventListener("change", onInput, true);
  document.addEventListener("paste", onPaste, true);
  document.addEventListener("focusout", onBlur, true);
  document.addEventListener("submit", onSubmit, true);
  window.addEventListener("pageshow", releaseOnce);
  document.addEventListener("DOMContentLoaded", () => hydratePhones(document));
  document.body.addEventListener("htmx:afterSwap", (event) => {
    hydratePhones(event.detail && event.detail.target);
  });
})();

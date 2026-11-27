function markChoice(name) {
  const inputs = document.querySelectorAll(`input[name="${name}"]`);
  inputs.forEach((input) => {
    const label = input.closest("label");
    if (!label) {
      return;
    }
    label.classList.toggle("is-on", input.checked);
  });
}

function syncChoices() {
  markChoice("delivery_method");
  markChoice("payment_method");
}

function deliveryMethodValue() {
  const checked = document.querySelector('input[name="delivery_method"]:checked');
  return checked ? checked.value : "np_branch";
}

function deliveryKind() {
  return deliveryMethodValue() === "np_locker" ? "locker" : "branch";
}

function isCourier() {
  return deliveryMethodValue() === "np_courier";
}

function initNpShip() {
  const root = document.querySelector("[data-np-ship]");
  if (!root || !window.gestiaSuggest) {
    return;
  }

  const cityInput = root.querySelector("[data-np-city]");
  const branchInput = root.querySelector("[data-np-branch]");
  const cityRefInput = root.querySelector("[data-np-city-ref]");
  const warehouseRefInput = root.querySelector("[data-np-warehouse-ref]");
  const clearButton = root.querySelector("[data-np-clear]");
  const houseWrap = root.querySelector("[data-np-house]");
  const houseInput = root.querySelector("[data-np-house-input]");
  const aptWrap = root.querySelector("[data-np-apt]");
  const aptInput = root.querySelector("[data-np-apartment]");
  const cityList = root.querySelector("#np-city-listbox");
  const branchList = root.querySelector("#np-branch-listbox");
  const hint = root.querySelector("[data-np-hint]");
  const arrow = root.querySelector("[data-np-arrow]");
  const secondWrap = root.querySelector("[data-np-second]");
  const streetLine = root.querySelector("[data-np-street-line]");
  if (!cityInput || !branchInput || !cityList || !branchList) {
    return;
  }

  const citiesUrl = root.dataset.npCitiesUrl || "";
  const warehousesUrl = root.dataset.npWarehousesUrl || "";
  const streetsUrl = root.dataset.npStreetsUrl || "";
  const minChars = Number(root.dataset.npMin || 2);
  const labelBranch = root.dataset.labelBranch || "";
  const labelLocker = root.dataset.labelLocker || "";
  const labelStreet = root.dataset.labelStreet || "";
  const hints = {
    npOff: root.dataset.hintNpOff || "",
    citiesFail: root.dataset.hintCitiesFail || "",
    noBranches: root.dataset.hintNoBranches || "",
    branchesFail: root.dataset.hintBranchesFail || "",
    streetsOff: root.dataset.hintStreetsOff || "",
    noStreets: root.dataset.hintNoStreets || "",
    streetsFail: root.dataset.hintStreetsFail || "",
    pickCity: root.dataset.hintPickCity || "",
    streetFormat: root.dataset.hintStreetFormat || "",
  };
  let cityTimer = 0;
  let branchTimer = 0;
  let streetTimer = 0;
  let cityRequest = 0;
  let branchRequest = 0;
  let streetRequest = 0;
  let cityRef = cityRefInput ? cityRefInput.value.trim() : "";
  let manualMode = false;

  const citySuggest = window.gestiaSuggest.bind(cityList, cityInput);
  const branchSuggest = window.gestiaSuggest.bind(branchList, branchInput, {
    onEscape: function () {
      setWarehouseRef("");
    },
  });

  function setCityRef(value) {
    cityRef = value || "";
    if (cityRefInput) {
      cityRefInput.value = cityRef;
    }
  }

  function setWarehouseRef(value) {
    if (warehouseRefInput) {
      warehouseRefInput.value = value || "";
    }
  }

  function syncClear() {
    if (!clearButton) {
      return;
    }
    const show = branchInput.value.trim().length > 0;
    clearButton.hidden = !show;
    const field = branchInput.closest(".nd-co-field");
    if (field) {
      field.classList.toggle("has-value", show);
    }
  }

  function syncSecondField() {
    const courier = isCourier();
    const locker = deliveryMethodValue() === "np_locker";
    branchInput.placeholder = courier ? labelStreet : locker ? labelLocker : labelBranch;
    branchInput.autocomplete = "off";
    branchInput.setAttribute("role", "combobox");
    branchInput.setAttribute("aria-autocomplete", "list");
    branchInput.setAttribute("aria-expanded", "false");
    branchInput.setAttribute("aria-controls", "np-branch-listbox");
    branchSuggest.close();
    setHint("");
    if (arrow) {
      arrow.hidden = false;
    }
    if (secondWrap) {
      secondWrap.classList.toggle("is-courier", courier);
    }
    if (streetLine) {
      streetLine.classList.toggle("is-courier", courier);
    }
    if (houseWrap) {
      houseWrap.hidden = !courier;
    }
    if (houseInput && !courier) {
      houseInput.value = "";
    }
    if (aptWrap) {
      aptWrap.hidden = !courier;
    }
    if (aptInput && !courier) {
      aptInput.value = "";
    }
    syncClear();
  }

  function enterManualMode(message) {
    manualMode = true;
    citySuggest.close();
    branchSuggest.close();
    setHint(message || hints.npOff);
  }

  function setHint(text) {
    if (!hint) {
      return;
    }
    if (!text) {
      hint.hidden = true;
      hint.textContent = "";
      return;
    }
    hint.hidden = false;
    hint.textContent = text;
  }

  async function loadCities() {
    const query = cityInput.value.trim();
    setCityRef("");
    setWarehouseRef("");
    branchSuggest.close();
    if (!citiesUrl || query.length < minChars) {
      citySuggest.close();
      setHint("");
      return;
    }

    const current = ++cityRequest;
    const url = new URL(citiesUrl, window.location.origin);
    url.searchParams.set("q", query);

    try {
      const response = await fetch(url.toString(), {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      const payload = await response.json().catch(() => ({}));
      if (current !== cityRequest) {
        return;
      }
      if (response.status === 503 || payload.error === "not_configured") {
        enterManualMode(hints.npOff);
        return;
      }
      if (!response.ok) {
        throw new Error(`cities ${response.status}`);
      }
      manualMode = false;
      setHint("");
      const items = Array.isArray(payload.items) ? payload.items : [];
      citySuggest.open(
        items.map((item) => ({ label: item.name, ref: item.ref, name: item.name })),
        (row) => {
          cityInput.value = row.name;
          setCityRef(row.ref);
          citySuggest.close();
          branchInput.value = "";
          setWarehouseRef("");
          syncClear();
          branchSuggest.close();
          branchInput.focus();
        }
      );
    } catch (_error) {
      if (current !== cityRequest) {
        return;
      }
      enterManualMode(hints.citiesFail);
    }
  }

  async function searchWarehouses() {
    const query = branchInput.value.trim();
    if (isCourier() || !warehousesUrl || manualMode || query.length < minChars) {
      branchSuggest.close();
      return;
    }

    const current = ++branchRequest;
    const url = new URL(warehousesUrl, window.location.origin);
    url.searchParams.set("q", query);
    url.searchParams.set("kind", deliveryKind());
    if (cityRef) {
      url.searchParams.set("city_ref", cityRef);
    }

    try {
      const response = await fetch(url.toString(), {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      const payload = await response.json().catch(() => ({}));
      if (current !== branchRequest) {
        return;
      }
      if (!response.ok) {
        throw new Error(`warehouses ${response.status}`);
      }
      const items = Array.isArray(payload.items) ? payload.items : [];
      const hadCity = Boolean(cityRef);
      branchSuggest.open(items, (row) => {
        branchInput.value = row.label || "";
        setWarehouseRef(row.ref || "");
        if (!hadCity && row.city_name) {
          cityInput.value = row.city_name;
        }
        if (row.city_ref) {
          setCityRef(row.city_ref);
        }
        branchSuggest.close();
        syncClear();
        setHint("");
      });
      setHint(items.length ? "" : hints.noBranches);
    } catch (_error) {
      if (current !== branchRequest) {
        return;
      }
      branchSuggest.close();
      setHint(hints.branchesFail);
    }
  }

  async function loadStreets() {
    const street = (branchInput.value || "").trim();
    if (!isCourier() || !streetsUrl || street.length < minChars) {
      if (isCourier()) {
        branchSuggest.close();
      }
      return;
    }
    if (manualMode || !cityRef) {
      branchSuggest.close();
      if (!cityRef && !manualMode) {
        setHint(hints.pickCity);
      }
      return;
    }

    const current = ++streetRequest;
    const url = new URL(streetsUrl, window.location.origin);
    url.searchParams.set("city_ref", cityRef);
    url.searchParams.set("q", street);

    try {
      const response = await fetch(url.toString(), {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      const payload = await response.json().catch(() => ({}));
      if (current !== streetRequest) {
        return;
      }
      if (response.status === 503 || payload.error === "not_configured") {
        enterManualMode(hints.streetsOff);
        return;
      }
      if (!response.ok) {
        throw new Error(`streets ${response.status}`);
      }
      setHint("");
      const items = Array.isArray(payload.items) ? payload.items : [];
      branchSuggest.open(
        items.map((item) => ({ label: item.label, ref: item.ref })),
        (row) => {
          branchInput.value = row.label;
          branchSuggest.close();
          syncClear();
          if (houseInput) {
            houseInput.focus();
          } else if (aptInput) {
            aptInput.focus();
          }
        }
      );
      if (!items.length) {
        setHint(hints.noStreets);
      }
    } catch (_error) {
      if (current !== streetRequest) {
        return;
      }
      enterManualMode(hints.streetsFail);
    }
  }

  function scheduleCities() {
    window.clearTimeout(cityTimer);
    cityTimer = window.setTimeout(loadCities, 280);
  }

  function scheduleWarehouses() {
    window.clearTimeout(branchTimer);
    branchTimer = window.setTimeout(searchWarehouses, 280);
  }

  function scheduleStreets() {
    window.clearTimeout(streetTimer);
    streetTimer = window.setTimeout(loadStreets, 280);
  }

  cityInput.addEventListener("input", () => {
    setCityRef("");
    setWarehouseRef("");
    scheduleCities();
  });
  cityInput.addEventListener("focus", () => {
    if (cityInput.value.trim().length >= minChars && cityList.childElementCount) {
      cityList.hidden = false;
      cityInput.setAttribute("aria-expanded", "true");
    } else {
      scheduleCities();
    }
  });
  cityInput.addEventListener("blur", () => {
    window.setTimeout(() => citySuggest.close(), 140);
  });

  branchInput.addEventListener("input", () => {
    setWarehouseRef("");
    syncClear();
    if (isCourier()) {
      scheduleStreets();
      return;
    }
    scheduleWarehouses();
  });
  branchInput.addEventListener("focus", () => {
    if (isCourier()) {
      if (manualMode) {
        setHint(hints.streetFormat);
        return;
      }
      if (!cityRef) {
        setHint(hints.pickCity);
        return;
      }
      const street = (branchInput.value || "").trim();
      if (street.length >= minChars) {
        scheduleStreets();
      } else {
        setHint(hints.streetFormat);
      }
      return;
    }
    if (manualMode) {
      setHint(hints.npOff);
      return;
    }
    const query = branchInput.value.trim();
    if (query.length >= minChars) {
      scheduleWarehouses();
      return;
    }
    if (!cityRef && cityInput.value.trim().length >= minChars) {
      setHint(hints.pickCity);
    }
  });
  branchInput.addEventListener("blur", () => {
    window.setTimeout(() => branchSuggest.close(), 140);
  });

  if (clearButton) {
    clearButton.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      branchInput.value = "";
      setWarehouseRef("");
      branchSuggest.close();
      setHint("");
      syncClear();
      branchInput.focus();
    });
  }

  document.addEventListener("change", (event) => {
    const input = event.target;
    if (input && input.name === "delivery_method") {
      branchInput.value = "";
      setWarehouseRef("");
      if (houseInput) {
        houseInput.value = "";
      }
      if (aptInput) {
        aptInput.value = "";
      }
      branchSuggest.close();
      syncSecondField();
    }
  });

  syncSecondField();
}

document.addEventListener("change", (event) => {
  const input = event.target;
  if (!input || !input.name) {
    return;
  }
  if (input.name === "delivery_method" || input.name === "payment_method") {
    markChoice(input.name);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  syncChoices();
  initNpShip();
});

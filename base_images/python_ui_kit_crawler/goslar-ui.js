(function () {
  function normalize(value) {
    return String(value || "")
      .toLocaleLowerCase("de-DE")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function initSearch(root) {
    var input = root.querySelector("[data-gs-search-input]");
    if (!input) return;

    var targetSelector = input.getAttribute("data-gs-search-target") || "[data-gs-search-item]";
    var items = Array.prototype.slice.call(root.querySelectorAll(targetSelector));
    var empty = root.querySelector("[data-gs-search-empty]");

    function applyFilter() {
      var query = normalize(input.value);
      var visibleCount = 0;

      items.forEach(function (item) {
        var source = item.getAttribute("data-gs-search-text") || item.textContent;
        var visible = !query || normalize(source).indexOf(query) !== -1;
        item.classList.toggle("gs-hidden", !visible);
        item.setAttribute("aria-hidden", visible ? "false" : "true");
        if (visible) visibleCount += 1;
      });

      if (empty) {
        empty.classList.toggle("gs-hidden", visibleCount !== 0);
      }
    }

    input.addEventListener("input", applyFilter);
    applyFilter();
  }

  function initAll() {
    Array.prototype.slice.call(document.querySelectorAll("[data-gs-search]")).forEach(initSearch);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();

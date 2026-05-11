let allData = [];
let currentRouteLine = null;
let routeInfoPanel = null;
let currentDistanceFilter = "all";
let currentRoutingControl = null;
const backToListBtn = document.getElementById("back-to-list");

const southWest = L.latLng(51.6, 10),
    northEast = L.latLng(52.1, 10.75),
    bounds = L.latLngBounds(southWest, northEast);


const map = L.map("map", {
    center: [51.9075, 10.4283],
    maxBounds: bounds,
    zoom: 12,
    maxZoom: 18,
    minZoom: 10,
    gestureHandling: true
});

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap"
}).addTo(map);

/* ============================= */
/* ROUTE INFO PANEL UNTEN       */
/* ============================= */

function createRouteInfoPanel() {
  routeInfoPanel = L.control({ position: "bottomleft" });

  routeInfoPanel.onAdd = function () {
    const div = L.DomUtil.create("div");
    div.className = "route-info-box";
    div.id = "route-info-box";
    return div;
  };

  routeInfoPanel.addTo(map);
}

createRouteInfoPanel();

/* ============================= */
/* MARKER ICONS                 */
/* ============================= */

const defiIcon24h = L.icon({
  iconUrl:
    "https://cdn.jsdelivr.net/gh/pointhi/leaflet-color-markers@v1.0.0/img/marker-icon-2x-green.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const defiIconLimited = L.icon({
  iconUrl:
    "https://cdn.jsdelivr.net/gh/pointhi/leaflet-color-markers@v1.0.0/img/marker-icon-2x-red.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const markerGroup = L.markerClusterGroup({
  showCoverageOnHover: false,
  maxClusterRadius: 160,
  disableClusteringAtZoom: 17
}).addTo(map);


/*=============================/
/* PERMISSION CHECK FOR POSITIONS */
/*===========================*/



function watchPosition() {

navigator.geolocation.watchPosition(
  (position) => {

    const { latitude, longitude, accuracy } = position.coords;
    const latlng = [latitude, longitude];

    lastUserPosition = { latitude, longitude };

    // Standort-Marker
    if (!userMarker) {
      userMarker = L.circleMarker(latlng, {
        radius: 8,
        color: "#22c55e",
        fillColor: "#22c55e",
        fillOpacity: 1
      }).addTo(map);
    } else {
      userMarker.setLatLng(latlng);
    }

    // Genauigkeits-Kreis (hier Radius erhöhen!)
    const displayRadius = Math.max(accuracy *2, 75);

    if (!userAccuracyCircle) {
      userAccuracyCircle = L.circle(latlng, {
        radius: displayRadius,
        color: "#22c55e",
        fillColor: "#22c55e",
        fillOpacity: 0.08
      }).addTo(map);
    } else {
      userAccuracyCircle.setLatLng(latlng);
      userAccuracyCircle.setRadius(displayRadius);
    }

    applySearchAndRender();
  },
  () => {},
  { enableHighAccuracy: true }
);
}

function handlePermission() {
  navigator.permissions.query({ name: "geolocation" }).then((result) => {
    if (result.state === "granted") {
      watchPosition();
    } else if (result.state === "prompt") {
      watchPosition();
    } else if (result.state === "denied") {
		console.log("Permission denied");
    }
    result.addEventListener("change", () => {
      report(result.state);
    });
  });
}

/* ============================= */
/* USER LOCATION                */
/* ============================= */

let lastUserPosition = null;
let userMarker = null;
let userAccuracyCircle = null;

handlePermission();



/* ============================= */
/* DATA LADEN                   */
/* ============================= */

fetch("data.json")
  .then((res) => res.json())
  .then((data) => {
    allData = data;
    applySearchAndRender();
  });

const distanceButtons = document.querySelectorAll("[data-distance-filter]");

distanceButtons.forEach(btn => {
  btn.addEventListener("click", () => {

    currentDistanceFilter = btn.dataset.distanceFilter;

    // Active-Klasse umschalten
    distanceButtons.forEach(b => b.classList.remove("filter-btn--active"));
    btn.classList.add("filter-btn--active");

    applySearchAndRender();
  });
});


  function extractCity(description) {
    if (!description) return "";

    // Nach Bindestrich oder Komma aufteilen
    let parts = description.split("-");

    if (parts.length > 1) {
      return parts[0].trim();
    }

    parts = description.split(",");
    if (parts.length > 1) {
      return parts[0].trim();
    }

    return description.trim();
  }
/* ============================= */
/* RENDER                       */
/* ============================= */
function applySearchAndRender() {

  let filtered = [...allData];


  /* =============================
     3️⃣ NUR GEÖFFNETE (optional)
  ============================== */
  filtered = filtered.filter(item =>
    isCurrentlyOpenStructured(item.opening_hours)
  );

  /* =============================
     4️⃣ ENTFERNUNGSBERECHNUNG
  ============================== */
  if (lastUserPosition) {

    filtered = filtered.map(item => {

      const distance = haversineDistance(
        lastUserPosition.latitude,
        lastUserPosition.longitude,
        item.lat,
        item.lng
      );

      return {
        ...item,
        _distance: distance
      };
    });

    /* =============================
       5️⃣ DISTANZFILTER
    ============================== */

    if (currentDistanceFilter !== "all") {

      const maxDistanceMap = {
        "500": 500,
        "1000": 1000,
        "2000": 2000
      };

      const maxDistance = maxDistanceMap[currentDistanceFilter];

      if (maxDistance) {
        filtered = filtered.filter(item => item._distance <= maxDistance);
      }
    }

    /* =============================
       6️⃣ SORTIERUNG NACH DISTANZ
    ============================== */
    filtered.sort((a, b) => a._distance - b._distance);

  } else {

    /* =============================
       Fallback: Alphabetisch
    ============================== */
    filtered.sort((a, b) =>
      a.title.localeCompare(b.title)
    );
  }

  render(filtered);
}

function render(data) {

  const listEl = document.getElementById("list");

  if (data.length === 0) {
    listEl.innerHTML = `
      <div class="no-results">
        <div class="no-results__icon">🔍</div>
        <div class="no-results__title">Keine Standorte gefunden</div>
        <div class="no-results__text">
          Bitte Suche oder Filter anpassen.
        </div>
      </div>
    `;
    markerGroup.clearLayers();
    return;
  }

  markerGroup.clearLayers();
  listEl.innerHTML = "";

  data.forEach((item) => {

    const isOpen = isCurrentlyOpenStructured(item.opening_hours);

    const marker = L.marker([item.lat, item.lng], {
      icon: isOpen ? defiIcon24h : defiIconLimited
    });

    markerGroup.addLayer(marker);

    const distanceInfo = getLocationDistanceInfo(item);

    const div = document.createElement("div");
    div.className = "location";

    div.innerHTML = `
      <div class="location__header">
        <h3>${item.title}</h3>
      </div>
      <p class="location__label">
        Wo liegt der Defi?
        ${item.Defi ? ` – ${item.Defi}` : ""}
      </p>
      <p>${item.description}</p>
      <p class="location__distance">${distanceInfo.label}</p>
      <div class="location__actions">
        <button class="location__route-btn" type="button" data-lat="${item.lat} data-lng="${item.lng}" data-title="${item.title}">
          Route
        </button>
        ${
          item.phone
            ? `<a href="tel:${item.phone.replace(/\s+/g, "")}"
                 class="location__call-btn"
                 onclick="event.stopPropagation()">
                 Anrufen
               </a>`
            : ""
        }
      </div>
    `;

    const routeBtn = div.querySelector(".location__route-btn");

    routeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      startRoute(item);
    });

    div.addEventListener("click", () => {

      // Zur Karte scrollen
      document.getElementById("map").scrollIntoView({
        behavior: "smooth"
      });

      map.setView([item.lat, item.lng], 17);
      startRoute(item);

      // Button anzeigen
      backToListBtn.classList.add("back-to-list-btn--visible");
    });

    listEl.appendChild(div);

  }); // ← forEach sauber schließen

  } // ← render() sauber schließen

/* ============================= */
/* ROUTING                      */
/* ============================= */

function startRoute(item) {
  if (!lastUserPosition) {
    alert("Standort wird noch ermittelt...");
    return;
  }

  const lat = parseFloat(item.lat);
  const lng = parseFloat(item.lng);
  const title = item.title || "";

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

  openNativeRoute(lat, lng, title);
}

function openNativeRoute(lat, lng, label = "") {
  const ua = navigator.userAgent || navigator.vendor || window.opera;
  const encodedLabel = encodeURIComponent(label);

  const isIOS = /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
  const isAndroid = /android/i.test(ua);

  if (isIOS) {
    // Apple Maps (Fußweg)

	const url = `https://maps.apple.com/?saddr=Current+Location&daddr=${lat},${lng}&dirflg=w`;
    window.open(url, "_blank");
    return;
  }

  if (isAndroid) {
    // Android: native Karten-App
    const geoUrl = `geo:0,0?q=${lat},${lng}${encodedLabel ? `(${encodedLabel})` : ""}`;
    const googleNavUrl = `https://www.google.com/maps/dir/?saddr=Current%20Location&api=1&destination=${lat},${lng}&travelmode=walking`;

    window.open(geourl, "_blank");

    // Fallback auf Google Maps
    setTimeout(() => {
      window.open(googleNavUrl, "_blank");
    }, 700);

    return;
  }

  // Desktop / Fallback
  const fallbackUrl = `https://www.google.com/maps/dir/?saddr=Current%20Location&api=1&destination=${lat},${lng}&travelmode=walking`;
  window.open(fallbackUrl, "_blank");
}

/* ============================= */
/* HILFSFUNKTIONEN              */
/* ============================= */

function haversineDistance(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371000;

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) ** 2;

  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function getLocationDistanceInfo(item) {
  if (!lastUserPosition || typeof item.lat !== "number" || typeof item.lng !== "number") {
    return {
      meters: null,
      minutes: null,
      label: "Standortfreigabe erforderlich"
    };
  }

  const meters = haversineDistance(
    lastUserPosition.latitude,
    lastUserPosition.longitude,
    item.lat,
    item.lng
  );

  const minutes = estimateWalkingMinutes(meters);

  return {
    meters,
    minutes,
    label: `${formatDistance(meters)} • ca. ${minutes} Min. Fußweg`
  };
}

function estimateWalkingMinutes(meters) {
  const walkingSpeedMetersPerMinute = 80;
  return Math.max(1, Math.round(meters / walkingSpeedMetersPerMinute));
}

function formatDistance(meters) {
  if (meters < 50) return "< 50 m";
  if (meters < 950) return `${Math.round(meters / 10) * 10} m`;
  return `${(meters / 1000).toFixed(1).replace(".", ",")} km`;
}

function formatWalkingTime(meters) {
  const minutes = estimateWalkingMinutes(meters);
  return `${minutes} Min`;
}

function isCurrentlyOpenStructured(openingHours) {
  if (!openingHours) return false;
  if (openingHours === "24/7") return true;

  const now = new Date();
  const dayMap = ["so","mo","di","mi","do","fr","sa"];
  const today = dayMap[now.getDay()];
  const slots = openingHours[today];
  if (!slots) return false;

  const current = now.getHours() * 60 + now.getMinutes();

  for (const [start, end] of slots) {
    const [sh, sm] = start.split(":").map(Number);
    const [eh, em] = end.split(":").map(Number);
    const s = sh * 60 + sm;
    const e = eh * 60 + em;

    if (s <= e && current >= s && current <= e) return true;
    if (s > e && (current >= s || current <= e)) return true;
  }
  return false;
}
/* ============================= */
/* ROUTING HILFSFUNKTION        */
/* ============================= */

function getWalkingDistance(start, destination) {
  return L.Routing.osrmv1({
    profile: "foot"
  }).route([
    L.Routing.waypoint(start),
    L.Routing.waypoint(destination)
  ]);
}
/* ============================= */
/* THEME TOGGLE                 */
/* ============================= */

const themeToggleBtn = document.getElementById("theme-toggle");

const savedTheme = localStorage.getItem("theme");

if (savedTheme === "light") {
  document.body.classList.add("light");
  themeToggleBtn.textContent = "☀️";
}

themeToggleBtn.addEventListener("click", () => {
  document.body.classList.toggle("light");

  const isLight = document.body.classList.contains("light");

  themeToggleBtn.textContent = isLight ? "☀️" : "🌙";

  localStorage.setItem("theme", isLight ? "light" : "dark");
});

backToListBtn.addEventListener("click", () => {

  document.querySelector(".locations").scrollIntoView({
    behavior: "smooth"
  });

  backToListBtn.classList.remove("back-to-list-btn--visible");
});

window.addEventListener("scroll", () => {

  const mapSection = document.getElementById("map");
  const rect = mapSection.getBoundingClientRect();

  if (rect.top > window.innerHeight / 2) {
    backToListBtn.classList.remove("back-to-list-btn--visible");
  }
});
document.addEventListener("DOMContentLoaded", () => {

  const backToListBtn = document.getElementById("back-to-list");

  if (!backToListBtn) return;

  backToListBtn.addEventListener("click", () => {

    const headerHeight = document.querySelector(".page-header").offsetHeight;
    const listSection = document.querySelector(".locations");

    const y = listSection.offsetTop - headerHeight - 10;

    window.scrollTo({
      top: y,
      behavior: "smooth"
    });

    backToListBtn.classList.remove("back-to-list-btn--visible");
  });

});

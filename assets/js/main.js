(function () {
  "use strict";

  var root = document.documentElement;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var ease = function (f) { return f < 0.5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2; };

  /* ---------- Full-screen mobile menu ---------- */
  var menuBtn = document.querySelector(".menu-toggle");
  if (menuBtn) {
    var setMenu = function (open) {
      root.classList.toggle("menu-open", open);
      menuBtn.setAttribute("aria-expanded", String(open));
    };
    menuBtn.addEventListener("click", function () { setMenu(!root.classList.contains("menu-open")); });
    document.querySelectorAll(".nav-links a").forEach(function (a) {
      a.addEventListener("click", function () { setMenu(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && root.classList.contains("menu-open")) { setMenu(false); menuBtn.focus(); }
    });
    window.matchMedia("(min-width: 681px)").addEventListener("change", function (m) { if (m.matches) setMenu(false); });
  }

  /* ---------- Scroll reveal ---------- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.05 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  }

  // Run fn(visible) whenever el enters / leaves the viewport
  function onVisible(el, fn, threshold) {
    if (!("IntersectionObserver" in window)) { fn(true); return; }
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { fn(e.isIntersecting); });
    }, { threshold: threshold || 0.35 }).observe(el);
  }

  /* ---------- Marker moving along SVG paths (network figure) ---------- */
  function Mover(marker, pause) {
    this.marker = marker;
    this.paths = [];
    this.pause = pause || 900;
    this.raf = null;
  }
  Mover.prototype.setPaths = function (paths, duration) {
    this.paths = paths;
    this.lens = paths.map(function (p) { return p.getTotalLength(); });
    this.total = this.lens.reduce(function (a, b) { return a + b; }, 0);
    this.duration = duration;
    this.place(reduceMotion ? 1 : 0);
  };
  Mover.prototype.place = function (f) {
    var d = f * this.total, i = 0;
    while (i < this.lens.length - 1 && d > this.lens[i]) { d -= this.lens[i]; i++; }
    var pt = this.paths[i].getPointAtLength(Math.min(d, this.lens[i]));
    this.marker.setAttribute("cx", pt.x);
    this.marker.setAttribute("cy", pt.y);
  };
  Mover.prototype.start = function () {
    if (reduceMotion || this.raf || !this.paths.length) return;
    var self = this, FADE_IN = 400, HOLD = 250, t0 = performance.now();
    var tick = function (now) {
      var e = (now - t0) % (self.duration + self.pause);
      self.place(ease(Math.min(e / self.duration, 1)));
      // Fade in at the start, fade out at the end before looping back
      var o = 1;
      if (e < FADE_IN) o = e / FADE_IN;
      else if (e > self.duration + HOLD) o = Math.max(0, 1 - (e - self.duration - HOLD) / (self.pause - HOLD));
      self.marker.style.opacity = o.toFixed(3);
      self.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  };
  Mover.prototype.stop = function () {
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = null;
  };

  /* ---------- Paper figures ---------- */
  document.querySelectorAll(".figure").forEach(function (fig) {
    if (fig.classList.contains("conf-map")) return;
    var svg = fig.querySelector("svg");
    var byId = function (id) { return svg.getElementById(id); };
    var visible = false;

    // --- Network figure: state buttons + moving ship ---
    var net = fig.querySelector(".net");
    var mover = null, cycleTimer = null, userTook = false;
    var buttons = fig.querySelectorAll(".fig-controls button");
    var live = fig.querySelector(".fig-caption-live");
    var marker = fig.querySelector("[data-mover]");
    if (marker) {
      mover = new Mover(marker, 1200);
      mover.setPaths(marker.getAttribute("data-mover").split(",").map(byId), +marker.getAttribute("data-duration") || 4000);
    }
    function setState(btn) {
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      net.setAttribute("data-state", btn.getAttribute("data-state"));
      if (live) live.textContent = btn.getAttribute("data-caption");
      if (mover) {
        mover.setPaths(btn.getAttribute("data-paths").split(",").map(byId), 3600);
        if (visible) { mover.stop(); mover.start(); }
      }
    }
    function stopCycle() { clearInterval(cycleTimer); cycleTimer = null; }
    function autoCycle() {
      if (reduceMotion || userTook || cycleTimer) return;
      cycleTimer = setInterval(function () {
        var arr = Array.prototype.slice.call(buttons);
        var cur = arr.findIndex(function (b) { return b.getAttribute("aria-pressed") === "true"; });
        setState(arr[(cur + 1) % arr.length]);
      }, 5200);
    }
    if (net && buttons.length) {
      buttons.forEach(function (b) {
        b.addEventListener("click", function () { userTook = true; stopCycle(); setState(b); });
      });
      setState(buttons[0]);
    }

    // --- Scrubbable figures: slider / pointer moves a guide line along the curves ---
    var scrub = fig.classList.contains("scrub") ? makeScrub(fig, svg, byId) : null;

    onVisible(fig, function (v) {
      visible = v;
      if (v) {
        fig.classList.add("is-visible");
        if (mover) setTimeout(function () { if (visible) mover.start(); }, 900);
        if (net) autoCycle();
        if (scrub) scrub.visible(true);
      } else {
        if (mover) mover.stop();
        stopCycle();
        if (scrub) scrub.visible(false);
      }
    });
  });

  function makeScrub(fig, svg, byId) {
    var x0 = +fig.getAttribute("data-x0"), x1 = +fig.getAttribute("data-x1");
    var caps = JSON.parse(fig.getAttribute("data-captions") || "[]");
    var guide = svg.querySelector(".scrub-guide");
    var hit = svg.querySelector(".scrub-hit");
    var input = fig.querySelector(".scrub-ui input");
    var live = fig.querySelector(".fig-caption-live");
    var dots = Array.prototype.map.call(svg.querySelectorAll(".scrub-dot"), function (c) {
      // Sample each curve once: its points sorted by x, for fast lookup
      var p = byId(c.getAttribute("data-path")), len = p.getTotalLength(), pts = [];
      for (var i = 0; i <= 240; i++) { var q = p.getPointAtLength(len * i / 240); pts.push([q.x, q.y]); }
      pts.sort(function (a, b) { return a[0] - b[0]; });
      return { el: c, pts: pts };
    });
    function yAt(pts, x) {
      for (var i = 1; i < pts.length; i++) {
        if (pts[i][0] >= x) {
          var a = pts[i - 1], b = pts[i], k = b[0] === a[0] ? 0 : (x - a[0]) / (b[0] - a[0]);
          return a[1] + k * (b[1] - a[1]);
        }
      }
      return pts[pts.length - 1][1];
    }
    var lastCap = -1;
    function set(t, fromInput) {
      t = Math.max(0, Math.min(1, t));
      var x = x0 + t * (x1 - x0);
      guide.setAttribute("x1", x); guide.setAttribute("x2", x);
      dots.forEach(function (d) { d.el.setAttribute("cx", x); d.el.setAttribute("cy", yAt(d.pts, x)); });
      if (!fromInput) input.value = Math.round(t * 1000);
      var idx = caps.findIndex(function (c) { return t <= c.to; });
      if (idx < 0) idx = caps.length - 1;
      if (idx !== lastCap && caps[idx]) {
        lastCap = idx;
        live.textContent = caps[idx].text;
        input.setAttribute("aria-valuetext", caps[idx].text);
      }
    }
    fig.classList.add("is-scrubbing");
    set(0);

    // Autoplay (sweep, fade out, restart) until the reader takes over
    var auto = fig.getAttribute("data-autoplay") === "true" && !reduceMotion;
    var raf = null, taken = false, SWEEP = 6500, PAUSE = 1400;
    function play() {
      if (!auto || taken || raf) return;
      var t0 = performance.now();
      var tick = function (now) {
        var e = (now - t0) % (SWEEP + PAUSE);
        set(ease(Math.min(e / SWEEP, 1)));
        var o = 1;
        if (e < 400) o = e / 400;
        else if (e > SWEEP + 300) o = Math.max(0, 1 - (e - SWEEP - 300) / (PAUSE - 300));
        dots.forEach(function (d) { d.el.style.opacity = o.toFixed(3); });
        guide.style.opacity = (o * 0.8).toFixed(3);
        raf = requestAnimationFrame(tick);
      };
      setTimeout(function () { if (!taken && !raf) raf = requestAnimationFrame(tick); }, 1600);
    }
    function pauseAuto() { if (raf) cancelAnimationFrame(raf); raf = null; }
    function take() {
      if (taken) return;
      taken = true; pauseAuto();
      dots.forEach(function (d) { d.el.style.opacity = ""; });
      guide.style.opacity = "";
    }

    input.addEventListener("input", function () { take(); set(input.value / 1000, true); });
    function fromPointer(e) {
      var pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
      var loc = pt.matrixTransform(svg.getScreenCTM().inverse());
      set((loc.x - x0) / (x1 - x0));
    }
    hit.addEventListener("pointermove", function (e) { take(); fromPointer(e); });
    hit.addEventListener("pointerdown", function (e) { take(); fromPointer(e); });

    return { visible: function (v) { if (v) play(); else pauseAuto(); } };
  }

  /* ---------- Conference map ---------- */
  document.querySelectorAll(".conf-map").forEach(function (fig) {
    var data = JSON.parse(fig.querySelector(".map-data").textContent);
    var tip = fig.querySelector(".map-tip");
    var wrap = fig.querySelector(".map-wrap");
    var items = document.querySelectorAll(".entries.talks > li[data-loc]");
    var markers = fig.querySelectorAll(".map-marker");
    var esc = function (s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; };

    function highlight(key) {
      markers.forEach(function (m) { m.classList.toggle("is-hl", m.getAttribute("data-loc") === key); });
      items.forEach(function (li) { li.classList.toggle("is-hl", li.getAttribute("data-loc") === key); });
    }
    function show(marker) {
      var key = marker.getAttribute("data-loc"), d = data[key];
      if (!d) return;
      tip.innerHTML = "<strong>" + esc(d.name) + "</strong><span class=\"tip-count\">" + esc(d.count) + "</span><ul>" +
        d.items.map(function (i) { return "<li>" + esc(i.title) + "<span>" + esc(i.date) + " · " + esc(i.venue) + "</span></li>"; }).join("") + "</ul>";
      tip.hidden = false;
      var r = marker.querySelector(".map-dot").getBoundingClientRect(), w = wrap.getBoundingClientRect();
      var left = r.left - w.left + r.width / 2, top = r.top - w.top;
      var tw = tip.offsetWidth, th = tip.offsetHeight;
      left = Math.max(4, Math.min(w.width - tw - 4, left - tw / 2));
      top = top - th - 12 < 0 ? r.bottom - w.top + 12 : top - th - 12;
      tip.style.left = left + "px"; tip.style.top = top + "px";
      requestAnimationFrame(function () { tip.classList.add("is-on"); });
      highlight(key);
    }
    function hide() { tip.classList.remove("is-on"); highlight(null); }

    markers.forEach(function (m) {
      m.addEventListener("mouseenter", function () { show(m); });
      m.addEventListener("mouseleave", hide);
      m.addEventListener("focus", function () { show(m); });
      m.addEventListener("blur", hide);
      m.addEventListener("click", function () { show(m); });
      m.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); show(m); } });
    });
    items.forEach(function (li) {
      li.addEventListener("mouseenter", function () { highlight(li.getAttribute("data-loc")); });
      li.addEventListener("mouseleave", function () { highlight(null); });
    });
    onVisible(fig, function (v) { if (v) fig.classList.add("is-visible"); }, 0.2);
  });

  /* ---------- Smooth open/close for <details class="findings"> ---------- */
  if (!reduceMotion && Element.prototype.animate) {
    document.querySelectorAll("details.findings").forEach(function (d) {
      var summary = d.querySelector("summary");
      var body = d.querySelector(".findings-body");
      if (!summary || !body) return;
      var anim = null;
      summary.addEventListener("click", function (e) {
        e.preventDefault();
        if (anim) anim.cancel();
        if (!d.open) {
          d.open = true;
          anim = body.animate([{ height: "0px", opacity: 0 }, { height: body.scrollHeight + "px", opacity: 1 }],
            { duration: 320, easing: "cubic-bezier(0.22, 1, 0.36, 1)" });
          anim.onfinish = function () { anim = null; };
        } else {
          anim = body.animate([{ height: body.offsetHeight + "px", opacity: 1 }, { height: "0px", opacity: 0 }],
            { duration: 220, easing: "ease-in" });
          anim.onfinish = function () { d.open = false; anim = null; };
        }
      });
    });
  }

  /* ---------- Print button (CV) ---------- */
  document.querySelectorAll("[data-print]").forEach(function (b) {
    b.addEventListener("click", function () { window.print(); });
  });
  window.addEventListener("beforeprint", function () {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  });

  /* ---------- Soft page transitions between internal pages ---------- */
  if (!reduceMotion) {
    document.addEventListener("click", function (e) {
      var a = e.target.closest("a");
      if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var href = a.getAttribute("href");
      if (!href || href.charAt(0) === "#" || a.target === "_blank" || a.hasAttribute("download")) return;
      var url = new URL(a.href, location.href);
      if (url.origin !== location.origin || url.pathname === location.pathname) return;
      e.preventDefault();
      document.body.classList.add("is-leaving");
      setTimeout(function () { location.href = url.href; }, 150);
    });
    window.addEventListener("pageshow", function (e) {
      if (e.persisted) document.body.classList.remove("is-leaving");
    });
  }

  /* ---------- Footer year ---------- */
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();

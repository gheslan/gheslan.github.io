(function () {
  "use strict";

  var root = document.documentElement;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Theme toggle ---------- */
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var current = root.getAttribute("data-theme");
      if (!current) {
        current = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      }
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  }

  /* ---------- Mobile menu ---------- */
  var menuBtn = document.querySelector(".menu-toggle");
  var links = document.querySelector(".nav-links");
  if (menuBtn && links) {
    menuBtn.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      menuBtn.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && links.classList.contains("is-open")) {
        links.classList.remove("is-open");
        menuBtn.setAttribute("aria-expanded", "false");
        menuBtn.focus();
      }
    });
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

  /* ---------- Paper figures ---------- */
  // Moves a marker along one or more SVG paths, looping while the figure is visible.
  function Mover(marker, pause) {
    this.marker = marker;
    this.paths = [];
    this.pause = pause || 900;
    this.raf = null;
    this.t0 = 0;
  }
  Mover.prototype.setPaths = function (paths, duration) {
    this.paths = paths;
    this.lens = paths.map(function (p) { return p.getTotalLength(); });
    this.total = this.lens.reduce(function (a, b) { return a + b; }, 0);
    this.duration = duration;
    this.t0 = performance.now();
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
    var self = this;
    var FADE_IN = 400, HOLD = 250;
    this.t0 = performance.now(); // always restart from the beginning, with a fade-in
    this.marker.style.transition = "transform 0.5s cubic-bezier(0.22, 1, 0.36, 1)";
    var tick = function (now) {
      var cycle = self.duration + self.pause;
      var e = (now - self.t0) % cycle;
      var f = Math.min(e / self.duration, 1);
      self.place(f < 0.5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2); // ease-in-out
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

  document.querySelectorAll(".figure").forEach(function (fig) {
    var svg = fig.querySelector("svg");
    var mover = null;
    var marker = fig.querySelector("[data-mover]");
    var byId = function (id) { return svg.getElementById ? svg.getElementById(id) : fig.querySelector("#" + id); };

    if (marker) {
      mover = new Mover(marker, 1200);
      var ids = marker.getAttribute("data-mover").split(",");
      mover.setPaths(ids.map(byId), +marker.getAttribute("data-duration") || 4000);
    }

    // Interactive state switcher (network figure)
    var net = fig.querySelector(".net");
    var buttons = fig.querySelectorAll(".fig-controls button");
    var live = fig.querySelector(".fig-caption-live");
    var cycleTimer = null, userTook = false, visible = false;

    function setState(btn) {
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      net.setAttribute("data-state", btn.getAttribute("data-state"));
      if (live) live.textContent = btn.getAttribute("data-caption");
      if (mover) {
        mover.setPaths(btn.getAttribute("data-paths").split(",").map(byId), 3600);
        if (visible) { mover.stop(); mover.start(); }
      }
    }
    function autoCycle() {
      if (reduceMotion || userTook || cycleTimer) return;
      cycleTimer = setInterval(function () {
        var arr = Array.prototype.slice.call(buttons);
        var cur = arr.findIndex(function (b) { return b.getAttribute("aria-pressed") === "true"; });
        setState(arr[(cur + 1) % arr.length]);
      }, 5200);
    }
    function stopCycle() { clearInterval(cycleTimer); cycleTimer = null; }
    if (net && buttons.length) {
      buttons.forEach(function (b) {
        b.addEventListener("click", function () { userTook = true; stopCycle(); setState(b); });
      });
      setState(buttons[0]);
    }

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          visible = entry.isIntersecting;
          if (visible) {
            fig.classList.add("is-visible");
            if (mover) setTimeout(function () { if (visible) mover.start(); }, 900);
            if (net) autoCycle();
          } else {
            if (mover) mover.stop();
            stopCycle();
          }
        });
      }, { threshold: 0.35 }).observe(fig);
    } else {
      fig.classList.add("is-visible");
    }
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
          var h = body.scrollHeight;
          anim = body.animate(
            [{ height: "0px", opacity: 0 }, { height: h + "px", opacity: 1 }],
            { duration: 320, easing: "cubic-bezier(0.22, 1, 0.36, 1)" }
          );
          anim.onfinish = function () { anim = null; };
        } else {
          anim = body.animate(
            [{ height: body.offsetHeight + "px", opacity: 1 }, { height: "0px", opacity: 0 }],
            { duration: 220, easing: "ease-in" }
          );
          anim.onfinish = function () { d.open = false; anim = null; };
        }
      });
    });
  }

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

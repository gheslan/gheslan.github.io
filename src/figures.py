"""Animated, number-free illustrations of preliminary results (one per paper).

Each function returns the <figure> HTML for one language. Figures are
stylized on purpose: they show directions of effects, never magnitudes.
"""
import html
import json

CAPTION = {"en": "Stylized illustration of preliminary results — not to scale.",
           "fr": "Illustration stylisée des résultats préliminaires — sans échelle."}


def _captions_attr(items):
    """items: list of (upper bound of t in [0, 1], text) -> escaped JSON attribute."""
    return html.escape(json.dumps([{"to": t, "text": txt} for t, txt in items], ensure_ascii=False), quote=True)


def _scrub_ui(uid, label):
    return f"""        <div class="scrub-ui">
          <label for="{uid}">{label}</label>
          <input id="{uid}" type="range" min="0" max="1000" value="0">
        </div>"""


def decarb(lang):
    L = {"en": dict(speed="Vessel speed", fleet="Fleet size", x="Carbon price →", z=("Low-carbon", "propulsion", "competitive"),
                    slider="Carbon price",
                    caps=[(0.2, "Low carbon price: operations barely change."),
                          (0.695, "Rising carbon price: ships slow down, and more vessels are needed to keep service frequency."),
                          (1.0, "Low-carbon propulsion becomes competitive: speed returns to its initial level and the fleet contracts.")],
                    aria="Stylized chart: as the carbon price rises, vessel speed falls and fleet size grows; once low-carbon propulsion becomes competitive, speed returns to its initial level and the fleet contracts."),
         "fr": dict(speed="Vitesse des navires", fleet="Taille de la flotte", x="Prix du carbone →", z=("Propulsion", "bas-carbone", "compétitive"),
                    slider="Prix du carbone",
                    caps=[(0.2, "Prix du carbone faible : les opérations changent peu."),
                          (0.695, "Prix du carbone en hausse : les navires ralentissent et il faut davantage de navires pour maintenir la fréquence de service."),
                          (1.0, "La propulsion bas-carbone devient compétitive : la vitesse revient à son niveau initial et la flotte se contracte.")],
                    aria="Graphique stylisé : quand le prix du carbone augmente, la vitesse des navires baisse et la flotte s’agrandit ; lorsque la propulsion bas-carbone devient compétitive, la vitesse revient à son niveau initial et la flotte se contracte.")}[lang]
    z1, z2, z3 = L["z"]
    return f"""      <figure class="figure scrub" data-x0="40" data-x1="345" data-autoplay="true" data-captions="{_captions_attr(L['caps'])}">
        <svg viewBox="0 0 360 220" role="img" aria-label="{L['aria']}">
          <rect class="fig-zone fade" style="--d:1.6s" x="252" y="20" width="93" height="170" rx="4"/>
          <text class="fig-label fade" style="--d:1.9s" x="298" y="160" text-anchor="middle">{z1}</text>
          <text class="fig-label fade" style="--d:1.9s" x="298" y="171" text-anchor="middle">{z2}</text>
          <text class="fig-label fade" style="--d:1.9s" x="298" y="182" text-anchor="middle">{z3}</text>
          <path class="fig-grid" d="M40 60H345M40 105H345M40 150H345" stroke-dasharray="2 5"/>
          <path class="fig-axis" d="M40 20V190H345"/>
          <path id="f1-speed" class="fig-line accent draw" style="--d:.2s" pathLength="1" d="M40 45 C 110 50, 170 128, 240 130 C 285 131, 310 52, 345 45"/>
          <path id="f1-fleet" class="fig-line warm draw" style="--d:.6s" pathLength="1" d="M40 165 C 110 163, 160 64, 220 64 C 275 64, 305 128, 345 158"/>
          <text class="fig-label accent fade" style="--d:1s" x="48" y="36">{L['speed']}</text>
          <text class="fig-label warm fade" style="--d:1.4s" x="196" y="52" text-anchor="middle">{L['fleet']}</text>
          <text class="fig-label" x="345" y="208" text-anchor="end">{L['x']}</text>
          <line class="scrub-guide" x1="40" x2="40" y1="20" y2="190"/>
          <circle class="scrub-dot accent" r="4.5" cx="40" cy="45" data-path="f1-speed"/>
          <circle class="scrub-dot warm" r="5" cx="40" cy="165" data-path="f1-fleet"/>
          <rect class="scrub-hit" x="40" y="20" width="305" height="170"/>
        </svg>
{_scrub_ui("s-decarb-" + lang, L['slider'])}
        <p class="fig-caption-live" aria-live="polite">{L['caps'][0][1]}</p>
        <figcaption>{CAPTION[lang]}</figcaption>
      </figure>"""


def trade(lang):
    L = {"en": dict(reg="Regulation", ton="Tonnage", val="Trade value", x="Time →", slider="Time",
                    caps=[(0.367, "Before the regulation: trade value and tonnage move together."),
                          (1.0, "After the regulation: the value of trade on exposed routes declines, while tonnage stays flat.")],
                    aria="Stylized chart: after the regulation, the value of containerized trade on exposed routes declines gradually while shipped tonnage stays flat."),
         "fr": dict(reg="Réglementation", ton="Tonnage", val="Valeur des échanges", x="Temps →", slider="Temps",
                    caps=[(0.367, "Avant la réglementation : la valeur des échanges et le tonnage évoluent ensemble."),
                          (1.0, "Après la réglementation : la valeur des échanges sur les routes exposées diminue, tandis que le tonnage reste stable.")],
                    aria="Graphique stylisé : après la réglementation, la valeur du commerce conteneurisé sur les routes exposées diminue progressivement tandis que le tonnage reste stable.")}[lang]
    val = [(40, 92), (70, 88), (100, 93), (130, 89), (150, 90), (180, 104), (210, 119), (240, 133), (270, 145), (300, 155), (340, 162)]
    ton = [(40, 88), (70, 92), (100, 89), (130, 92), (150, 90), (180, 93), (210, 88), (240, 94), (270, 89), (300, 93), (340, 90)]
    d_val = "M" + " L".join(f"{x} {y}" for x, y in val)
    d_ton = "M" + " L".join(f"{x} {y}" for x, y in ton)
    dots = "\n".join(f'          <circle class="fig-dot pop" style="--d:{1.0 + k * 0.12:.2f}s" cx="{x}" cy="{y}" r="3.2"/>'
                     for k, (x, y) in enumerate(val[5:]))
    return f"""      <figure class="figure scrub" data-x0="40" data-x1="340" data-captions="{_captions_attr(L['caps'])}">
        <svg viewBox="0 0 360 220" role="img" aria-label="{L['aria']}">
          <rect class="fig-zone fade" style="--d:.1s" x="150" y="20" width="195" height="170"/>
          <path class="fig-grid" d="M40 90H345"/>
          <path class="fig-axis" d="M40 20V190H345"/>
          <path class="fig-axis fade" d="M150 20V190" stroke-dasharray="4 4"/>
          <text class="fig-label strong fade" x="156" y="34">{L['reg']}</text>
          <path id="f2-ton" class="fig-line muted draw" style="--d:.3s" pathLength="1" d="{d_ton}"/>
          <path id="f2-val" class="fig-line warm draw" style="--d:.6s" pathLength="1" d="{d_val}"/>
{dots}
          <text class="fig-label fade" style="--d:1.6s" x="345" y="80" text-anchor="end">{L['ton']}</text>
          <text class="fig-label warm fade" style="--d:1.9s" x="345" y="182" text-anchor="end">{L['val']}</text>
          <text class="fig-label" x="345" y="208" text-anchor="end">{L['x']}</text>
          <line class="scrub-guide" x1="40" x2="40" y1="20" y2="190"/>
          <circle class="scrub-dot muted" r="4.5" cx="40" cy="88" data-path="f2-ton"/>
          <circle class="scrub-dot warm" r="5" cx="40" cy="92" data-path="f2-val"/>
          <rect class="scrub-hit" x="40" y="20" width="300" height="170"/>
        </svg>
{_scrub_ui("s-trade-" + lang, L['slider'])}
        <p class="fig-caption-live" aria-live="polite">{L['caps'][0][1]}</p>
        <figcaption>{CAPTION[lang]}</figcaption>
      </figure>"""


def leak(lang):
    L = {"en": dict(asia="Asia", hub="Non-EU hub", eu="EU port", zone="EU",
                    s=[("regional", "Regional price (EU ETS)", "f3-direct",
                        "Under the EU ETS, a voyage entering the EU from outside is priced for half of its emissions."),
                       ("hub", "Hub call", "f3-a,f3-b",
                        "Calling at a nearby non-EU hub leaves the long deep-sea leg unpriced: only the short final hop is taxed."),
                       ("global", "Global price", "f3-direct",
                        "A universal carbon price — or a transport border adjustment — covers the whole voyage and closes the channel.")],
                    leg=("Fully priced", "Half priced", "Unpriced"),
                    ctl="Carbon pricing scenario",
                    aria="Stylized map of a liner service from Asia to an EU port, directly or via a non-EU hub, showing which legs are priced."),
         "fr": dict(asia="Asie", hub="Hub hors UE", eu="Port de l’UE", zone="UE",
                    s=[("regional", "Prix régional (SEQE-UE)", "f3-direct",
                        "Avec le SEQE-UE, un voyage entrant dans l’UE depuis l’extérieur est tarifé pour la moitié de ses émissions."),
                       ("hub", "Escale dans un hub", "f3-a,f3-b",
                        "Une escale dans un hub voisin hors UE laisse le long trajet océanique non tarifé : seul le court trajet final est taxé."),
                       ("global", "Prix mondial", "f3-direct",
                        "Un prix du carbone universel — ou un ajustement carbone aux frontières sur le transport — couvre tout le voyage et ferme ce canal.")],
                    leg=("Tarifé", "Tarifé à moitié", "Non tarifé"),
                    ctl="Scénario de tarification du carbone",
                    aria="Carte stylisée d’une ligne régulière de l’Asie vers un port de l’UE, en direct ou via un hub hors UE, indiquant quels trajets sont tarifés.")}[lang]
    buttons = "\n".join(
        f'          <button type="button" data-state="{st}" data-paths="{paths}" data-caption="{html.escape(cap)}" aria-pressed="{str(k == 0).lower()}">{lab}</button>'
        for k, (st, lab, paths, cap) in enumerate(L["s"]))
    f, h, u = L["leg"]
    return f"""      <figure class="figure">
        <div class="fig-controls" role="group" aria-label="{L['ctl']}">
{buttons}
        </div>
        <svg class="net" data-state="regional" viewBox="0 0 360 200" role="img" aria-label="{L['aria']}">
          <path class="fig-zone" d="M262 0 H360 V200 H300 C 272 150, 270 60, 262 0 Z"/>
          <text class="fig-label strong" x="340" y="22" text-anchor="end">{L['zone']}</text>
          <path id="f3-direct" class="leg leg-direct" d="M40 165 C 140 120, 220 92, 310 80"/>
          <path id="f3-a" class="leg leg-a" d="M40 165 C 110 158, 170 150, 232 150"/>
          <path id="f3-b" class="leg leg-b" d="M232 150 C 262 142, 288 112, 310 80"/>
          <circle class="fig-node" cx="40" cy="165" r="6"/>
          <g class="hub-node"><circle class="fig-node" cx="232" cy="150" r="6"/><text class="fig-label" x="226" y="176" text-anchor="middle">{L['hub']}</text></g>
          <circle class="fig-node" cx="310" cy="80" r="6"/>
          <text class="fig-label" x="40" y="190" text-anchor="middle">{L['asia']}</text>
          <text class="fig-label" x="310" y="64" text-anchor="middle">{L['eu']}</text>
          <circle class="fig-dot" r="4.5" cx="40" cy="165" data-mover="f3-direct" data-duration="3600"/>
        </svg>
        <p class="fig-caption-live" aria-live="polite">{L['s'][0][3]}</p>
        <ul class="fig-legend">
          <li><svg viewBox="0 0 26 8" aria-hidden="true"><path d="M1 4H25" stroke="var(--warm)" stroke-width="2.4"/></svg>{f}</li>
          <li><svg viewBox="0 0 26 8" aria-hidden="true"><path d="M1 4H25" stroke="var(--warm)" stroke-width="2.4" stroke-dasharray="5 4"/></svg>{h}</li>
          <li><svg viewBox="0 0 26 8" aria-hidden="true"><path d="M1 4H25" stroke="var(--fig-muted)" stroke-width="2.4"/></svg>{u}</li>
        </ul>
        <figcaption>{CAPTION[lang]}</figcaption>
      </figure>"""


FIGURES = {"decarb": decarb, "trade": trade, "leak": leak}

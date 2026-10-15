#!/usr/bin/env python3
"""Hand check of the intake dilution with the ASHRAE minimum-dilution method (Wilson and Lamb).

    python3 postproc/hand_method.py --out results/applied/hand_method.md --fig results/applied/figures/hand_method.png

The method (ASHRAE Handbook Fundamentals 1993 ch. 14 and 1997 ch. 15; Wilson and Lamb 1994;
reproduced as equations 2.1 to 2.3 of ASHRAE RP-1635, Petersen and Ritter 2016):

    D_min = (sqrt(D_o) + sqrt(D_s))^2
    D_o   = 1 + C1 * beta * M^2          initial dilution by the jet, M = V_e / U_H, beta = 1 vertical uncapped
    D_s   = B1 * U_H * S^2 / Q_e         dilution by spread over the stretched-string distance S

Constant sets (kind: empirical, cited in RP-1635 section 2 and 4):
    Wilson and Chiu 1994   C1 = 7,  B1 = 0.0625   (lower bound to wind-tunnel data)
    ASHRAE 1997            C1 = 13, B1 = 0.059
    Wilson and Lamb 1994   C1 = 13, B1 = 0.04     (lower bound to full-scale tracer data)

The method is built as a lower bound for the worst wind direction and has no stack-height term
beyond the geometric distance S, so it is compared with the CFD at the worst direction (180 deg).
Four flues: concentrations add, so the combined dilution is 1 / sum(1/D_i).
Inputs: params/hall_geometry.json (geometry), params/applied_design.json (flows), results/applied/*.json (CFD).
"""
import argparse, glob, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))

SETS = [("Wilson & Chiu 1994", 7.0, 0.0625), ("ASHRAE 1997", 13.0, 0.059), ("Wilson & Lamb 1994", 13.0, 0.04)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/applied/hand_method.md"); ap.add_argument("--fig", default="results/applied/figures/hand_method.png")
    ap.add_argument("--UH", type=float, default=10.0); a = ap.parse_args()
    G = json.load(open("params/hall_geometry.json")); P = json.load(open("params/applied_design.json"))
    L, roof = G["hall"]["length_x"], G["hall"]["height"]; F = G["flues"]; I = G["intake"]
    d = F["diameter"]; n = F["count"]; Q1 = P["flows"]["flue_exit_m3ps"] / n; Ve = Q1 / (math.pi * d * d / 4); M = Ve / a.UH
    xf = L / 2 - F["inset_from_parapet_x"]; ys = [(i - (n - 1) / 2) * F["spacing_y"] for i in range(n)]
    # nearest louvre point: the louvre is on the +/-y faces of the intake box, centred on the box
    xi0, xi1 = I["centre_x"] - I["louvre_width"] / 2, I["centre_x"] + I["louvre_width"] / 2
    yl = I["size_y"] / 2; zl0 = roof + (I["height"] - I["louvre_height"]) / 2; zl1 = zl0 + I["louvre_height"]
    tips = {v: P["variants"][v]["flue_tip_m"] for v in sorted(P["variants"])}
    cfd = {}
    for f in glob.glob("results/applied/*.json"):
        r = json.load(open(f)); m = re.match(r"(D\d)_dir(\d+)_U([\d.]+)$", r["case"])
        if m and float(m.group(3)) == a.UH: cfd[(m.group(1), int(m.group(2)))] = r["intake_dilution_flues"]
    rows = []
    for v, tip in tips.items():
        zt = roof + tip; Dc = {}
        for name, C1, B1 in SETS:
            inv = 0.0
            for y in ys:
                dx = max(xf - xi1, 0.0); dy = max(abs(y) - yl, 0.0); dz = max(zt - zl1, 0.0) if zt > zl1 else max(zl0 - zt, 0.0)
                S = math.sqrt(dx * dx + dy * dy + dz * dz)
                Do = 1 + C1 * 1.0 * M * M; Ds = B1 * a.UH * S * S / Q1
                inv += 1.0 / (math.sqrt(Do) + math.sqrt(Ds)) ** 2
            Dc[name] = 1.0 / inv
        rows.append((v, tip, S, Dc, cfd.get((v, 180)), cfd.get((v, 90))))
    hr = 3 * 1.0 * d * Ve / a.UH   # Briggs momentum rise as used by the ASHRAE geometric method, h_r = 3 beta d_e V_e / U_H
    lines = ["# Hand check: ASHRAE minimum-dilution method against the CFD", "",
             f"U_H = {a.UH:g} m/s, V_e = {Ve:.1f} m/s (Q = {Q1:.2f} m3/s per flue, d = {d} m), M = {M:.2f}. "
             f"Stretched-string distance S from the nearest flue tip to the nearest louvre point; four flues combined by adding concentrations.", "",
             "| flue tip | S [m] | " + " | ".join(f"D_min {s[0]}" for s in SETS) + " | CFD 180 deg | CFD 90 deg |", "|---|---|" + "---|" * (len(SETS) + 2)]
    for v, tip, S, Dc, c180, c90 in rows:
        lines.append(f"| {tip:g} m ({v}) | {S:.1f} | " + " | ".join(f"{Dc[s[0]]:.0f}" for s in SETS) + f" | {c180:.0f} | {c90:.0f} |" if c180 and c90 else
                     f"| {tip:g} m ({v}) | {S:.1f} | " + " | ".join(f"{Dc[s[0]]:.0f}" for s in SETS) + " | | |")
    lines += ["", f"Briggs momentum rise used by the ASHRAE geometric method: h_r = 3 d_e V_e / U_H = {hr:.1f} m, so the plume centreline passes "
              f"{roof + tips['D0'] + hr - zl1:.1f} m above the louvre top with the 3 m tip. Kind: empirical (ASHRAE Handbook HVAC Applications, "
              "Building Air Intake and Exhaust Design chapter; Briggs 1984), quoted from secondary sources, not from the chapter text.", "",
              "Reading: the hand method is a lower bound for the worst direction and carries no stack-height credit beyond S, so it should sit "
              "below the CFD at 180 deg and should not follow the CFD's gain with flue height. Where the CFD at 180 deg lies below the hand "
              "lower bound, the CFD is the more conservative of the two; where it lies far above, the RANS plume rise is doing what the hand method cannot."]
    os.makedirs(os.path.dirname(a.out), exist_ok=True); open(a.out, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
    # figure
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import style; style.use()
    fig, ax = plt.subplots(figsize=(style.HALF + 0.6, 2.8))
    t = [r[1] for r in rows]
    lo = [min(r[3].values()) for r in rows]; hi = [max(r[3].values()) for r in rows]
    ax.fill_between(t, lo, hi, color=style.LIGHT, lw=0, label="ASHRAE $D_{min}$, three constant sets")
    ax.plot(t, [r[4] for r in rows], "o-", color=style.CFD3, label="CFD, 180° (flues upwind)")
    ax.plot(t, [r[5] for r in rows], "s-", color=style.CFD, label="CFD, 90° (across)")
    ax.axhline(2000, color=style.INK, lw=0.8, ls="--"); ax.text(t[-1], 2000, " limit", va="center", fontsize=7)
    ax.set_yscale("log"); ax.set_xlabel("flue tip above the roof [m]"); ax.set_ylabel("dilution at the intake"); ax.set_xticks(t)
    ax.legend(loc="upper left", fontsize=7); ax.set_ylim(10, 1e5)
    style.save(fig, a.fig); print("wrote", a.fig)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from colorsys import hls_to_rgb, rgb_to_hls
import re
from matplotlib.colors import ListedColormap
import numpy as np


def parse_color(s):
    m = re.match(r"\(([0-9\.eE+-]+),\s*([0-9\.eE+-]+),\s*([0-9\.eE+-]+)\)", s)
    if m:
        r, g, b = float(m[1]), float(m[2]), float(m[3])
        if not (0 <= r <= 1 and 0 <= g <= 1 and 0 <= b <= 1):
            raise ValueError(f"Color components out of range {s!r}")
        return r, g, b
    m = re.match(r"(?:#|0x)?([0-9A-Fa-f]{6})", s)
    if m:
        r, g, b = int(m[1][:2], 16), int(m[1][2:4], 16), int(m[1][4:], 16)
        return r / 255, g / 255, b / 255
    m = re.match(r"(?:#|0x)?([0-9A-Fa-f]{3})", s)
    if m:
        r, g, b = int(m[1][:1], 16), int(m[1][1:2], 16), int(m[1][2:], 16)
        return r / 15, g / 15, b / 15
    raise ValueError(f"Invalid color {s!r}")


def to_hex(rgb):
    r, g, b = rgb
    return f"{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def plot_cmap(ax, color_list):
    gradient = np.linspace(0, 1, len(color_list))
    gradient = np.vstack((gradient, gradient))
    ax.imshow(gradient, aspect='auto', cmap=ListedColormap(color_list))
    ax.set_axis_off()


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(help="Sub-command", dest='cmd')
    # Plot palette
    cmd = sub.add_parser("plot", aliases=["p"], help="Plots a palette's components (reads new-line separated colors from stdin)")
    cmd.add_argument("--dalton", "-d", action="store_true", help="Simulate color blindness")
    cmd.add_argument("--ntsc", action="store_true", help="Show NTSC brightness")
    # Create diverging palette
    cmd = sub.add_parser("create-diverging", aliases=["cd"], help="Creates a diverging palette")
    cmd.add_argument("n_colors", type=int, help="Number of colors")
    cmd.add_argument("h_min", type=float, help="Hue below middle point")
    cmd.add_argument("h_max", type=float, help="Hue above middle point")
    cmd.add_argument("s_min", type=float, help="Saturation below middle point")
    cmd.add_argument("s_max", type=float, help="Saturation above middle point")
    cmd.add_argument("l_min", type=float, help="Lightness at minimum")
    cmd.add_argument("l_mid", type=float, help="Lightness at middle point")
    cmd.add_argument("l_max", type=float, help="Lightness at maximum (default: same as l_min)", nargs="?", default=-1)
    args = parser.parse_args()

    if args.cmd in ["plot", "p"]:
        colors = []
        for i, ln in enumerate(sys.stdin):
            ln = ln.strip()
            if ln:
                try:
                    colors.append(parse_color(ln))
                except Exception as ex:
                    print(f"Bad line {i+1}: {ex}")

        import matplotlib.pyplot as plt
        fig, (ax1, axc) = plt.subplots(2, 1, sharex=True, gridspec_kw=dict(height_ratios=[0.9, 0.1]))
        hls = list(map(lambda x: rgb_to_hls(*x), colors))
        h, l, s = [x[0] for x in hls], [x[1] for x in hls], [x[2] for x in hls]
        ax1.plot(h, 'k-', label='H')
        ax1.plot(l, 'k--', label='L')
        ax1.plot(s, 'k:', label='S')
        if args.dalton:
            from daltonlens.simulate import Deficiency, Simulator_Vienot1999
            u_colors = (np.array(colors) * 255).astype(np.uint8).reshape((-1, 1, 3))
            sim = Simulator_Vienot1999()
            for d, lbl, c in [(Deficiency.DEUTAN, "Deu", 'tab:blue'), (Deficiency.PROTAN, "Pro", 'tab:orange'), (Deficiency.TRITAN, "Tri", 'tab:green')]:
                d_colors = sim.simulate_cvd(u_colors, d, 1.0).reshape(-1, 3).astype(np.float) / 255
                hls = list(map(lambda x: rgb_to_hls(*x), d_colors))
                h, l, s = [x[0] for x in hls], [x[1] for x in hls], [x[2] for x in hls]
                ax1.plot(h, '-', c=c, label=f'H {lbl}')
                ax1.plot(l, '--', c=c, label=f'L {lbl}')
                ax1.plot(s, ':', c=c, label=f'S {lbl}')
        if args.ntsc:
            ntsc_brightness = [0.3 * x[0] + 0.59 * x[1] + 0.11 * x[2] for x in colors]
            ax1.plot(ntsc_brightness, 'r-', label='NTSC')
        ax1.set_ylim(0, 1)
        ax1.legend(ncols=4 if args.dalton else 1)
        ax1.grid()
        plot_cmap(axc, colors)
        plt.show()

    elif args.cmd in ["create-diverging", "cd"]:
        odd = (args.n_colors % 2) == 1
        half = args.n_colors // 2
        h = ([args.h_min] * half) + ([0] * int(odd)) + ([args.h_max] * half)
        s = ([args.s_min] * half) + ([0] * int(odd)) + ([args.s_max] * half)
        l_max = args.l_max if args.l_max >= 0 else args.l_min
        l1 = np.linspace(args.l_min, args.l_mid, half + int(odd), endpoint=True)
        l2 = np.linspace(args.l_mid, l_max, half + int(odd), endpoint=True)
        l = list(l1) + list(l2)[int(odd):]
        assert len(h) == len(s)
        assert len(h) == len(l)
        for a, b, c in zip(h, l, s):
            print(to_hex(hls_to_rgb(a, b, c)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


FRAMEWORKS = ["NIST CSF 2.0", "ISO/IEC\n27001:2022", "HITRUST CSF", "NHS DSPT"]

THREATS = ["Ransomware", "FHIR API\nExploitation", "IoMT\nVulnerabilities",
           "Insider\nThreats", "Nation-State\nAPT"]

# Table 4.1 (columns: NIST, ISO, HITRUST, DSPT)
TABLE_4_1 = np.array([
    [2, 2, 3, 1],   # Ransomware
    [1, 1, 1, 1],   # FHIR API
    [1, 1, 1, 2],   # IoMT
    [2, 2, 3, 2],   # Insider
    [2, 2, 2, 2],   # Nation-state APT
])

METHODS = ["STRIDE", "LINDDUN", "PASTA", "MITRE ATT&CK"]

# Table 4.2 (None = 1, Partial = 2, Referenced = 3)
TABLE_4_2 = np.array([
    [2, 2, 2, 1],   # STRIDE
    [1, 2, 1, 2],   # LINDDUN
    [2, 2, 2, 1],   # PASTA
    [3, 1, 1, 1],   # ATT&CK
])

# GDPR alignment from Table 5.1 (Weak = 1, Moderate = 2, Strong = 3)
GDPR = np.array([2, 3, 1, 2])

WEAK, MODERATE, STRONG = "#C0504D", "#D9A441", "#4F8A5B"
COLOURS = [WEAK, MODERATE, STRONG]
# amber is light enough to need dark text, the other two take white
TEXT_COLOURS = ["white", "#3A2E00", "white"]

# figures 4.5 and 4.6 compare different measures, so they use their own colours
BLUE, ORANGE, PURPLE = "#3B6EA5", "#D95B33", "#5B4E9E"
RATING_LABELS = ["Weak", "Moderate", "Strong"]
TM_LABELS = ["None", "Partial", "Referenced"]


def heatmap(data, row_labels, cell_labels, filename, height):
    fig, ax = plt.subplots(figsize=(9, height))
    cmap = matplotlib.colors.ListedColormap(COLOURS)
    ax.imshow(data, cmap=cmap, vmin=1, vmax=3, aspect="auto")

    ax.set_xticks(range(len(FRAMEWORKS)))
    ax.set_xticklabels(FRAMEWORKS, fontsize=10, fontweight="bold")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=10, fontweight="bold")
    ax.xaxis.set_ticks_position("top")

    for r in range(data.shape[0]):
        for c in range(data.shape[1]):
            v = data[r, c]
            ax.text(c, r, cell_labels[v - 1], ha="center", va="center",
                    fontsize=11, fontweight="bold", color=TEXT_COLOURS[v - 1])

    # white lines between cells
    ax.set_xticks(np.arange(-0.5, data.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, data.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2.5)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved", filename)


def stacked_bars(counts, labels, ylabel, filename, width, ylim):
    fig, ax = plt.subplots(figsize=(width, 5))
    bottom = np.zeros(len(labels))

    for i in range(3):
        vals = counts[:, i]
        ax.bar(labels, vals, bottom=bottom, color=COLOURS[i],
               label=RATING_LABELS[i], edgecolor="white", linewidth=2)
        for x, v in enumerate(vals):
            if v:
                ax.text(x, bottom[x] + v / 2, str(v), ha="center", va="center",
                        fontweight="bold", fontsize=12, color=TEXT_COLOURS[i])
        bottom += vals

    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_ylim(0, ylim)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09),
              ncol=3, frameon=False, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved", filename)


def grouped_bars(first, second, labels, colours, filename, notes, ylabel, decimals):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(FRAMEWORKS))
    w = 0.35

    for offset, values, label, colour, dp in [(-w / 2, first, labels[0], colours[0], decimals[0]),
                                               (w / 2, second, labels[1], colours[1], decimals[1])]:
        ax.bar(x + offset, values, w, label=label, color=colour, edgecolor="white", linewidth=1.5)
        for xi, v in zip(x + offset, values):
            ax.text(xi, v + 0.04, f"{v:.{dp}f}", ha="center", va="bottom",
                    fontsize=11, fontweight="bold", color=colour)

    for text, xy, xytext, colour in notes:
        ax.annotate(text, xy=xy, xytext=xytext, ha="center", fontsize=9.5,
                    fontweight="bold", color=colour,
                    arrowprops=dict(arrowstyle="->", color=colour, lw=1.4))

    ax.set_xticks(x)
    ax.set_xticklabels(FRAMEWORKS, fontsize=10)
    ax.set_ylim(0, 3.6)
    ax.set_yticks([1, 2, 3])
    ax.set_ylabel(ylabel, fontsize=10)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=10)

    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved", filename)


def count_ratings(data, axis):
    # axis=0 counts down each column (per framework), axis=1 across each row (per threat)
    n = data.shape[1] if axis == 0 else data.shape[0]
    counts = np.zeros((n, 3), dtype=int)
    for idx in range(n):
        values = data[:, idx] if axis == 0 else data[idx, :]
        for v in values:
            counts[idx, v - 1] += 1
    return counts


def print_scores():
    print("\nFramework scores (out of 15):")
    for i, name in enumerate(FRAMEWORKS):
        print(f"  {name.replace(chr(10), ' '):22} {TABLE_4_1[:, i].sum()}")

    print("\nThreat scores (out of 12):")
    for i, name in enumerate(THREATS):
        print(f"  {name.replace(chr(10), ' '):22} {TABLE_4_1[i, :].sum()}")

    flat = TABLE_4_1.flatten()
    print("\nDistribution across 20 ratings:")
    for v, label in enumerate(RATING_LABELS, start=1):
        n = int((flat == v).sum())
        print(f"  {label:10} {n:2}  ({n * 5}%)")


if __name__ == "__main__":
    heatmap(TABLE_4_1, THREATS, RATING_LABELS, "fig4_1_heatmap.png", 5.5)
    heatmap(TABLE_4_2, METHODS, TM_LABELS, "fig4_2_tm_heatmap.png", 4.8)

    stacked_bars(count_ratings(TABLE_4_1, axis=0), FRAMEWORKS,
                 "Number of threat categories", "fig4_3_by_framework.png", 9, 5.6)
    stacked_bars(count_ratings(TABLE_4_1, axis=1), THREATS,
                 "Number of frameworks (out of 4)", "fig4_4_by_threat.png", 10, 5.2)

    coverage = TABLE_4_1.mean(axis=0)   # average threat rating per framework
    tm_integration = TABLE_4_2.mean(axis=0)   # average threat-modelling rating per framework

    grouped_bars(
        GDPR, coverage, ["GDPR alignment", "Average EHR threat coverage"],
        [BLUE, ORANGE], "fig4_5_gdpr_vs_coverage.png",
        notes=[
            ("Highest GDPR alignment,\nbut Strong on no threat", (0.93, 2.85), (1.45, 3.35), "#2B5486"),
            ("Weakest GDPR alignment,\nhighest threat coverage", (2.28, 1.85), (2.8, 2.75), "#A8391A"),
        ],
        ylabel="Rating (1 = Weak, 2 = Moderate, 3 = Strong)",
        decimals=(0, 1),
    )

    grouped_bars(
        coverage, tm_integration, ["Average EHR threat coverage", "Average threat-modelling integration"],
        [ORANGE, PURPLE], "fig4_6_coverage_vs_tm.png",
        notes=[
            ("Joint-lowest threat coverage,\nbest threat-model integration", (0.28, 1.85), (0.9, 3.0), "#3F3478"),
            ("Highest threat coverage,\nthird on threat-model integration", (1.93, 1.85), (2.6, 3.0), "#A8391A"),
        ],
        ylabel="Rating (1 = Weak/None, 2 = Moderate/Partial,\n3 = Strong/Referenced)",
        decimals=(1, 2),
    )

    print_scores()

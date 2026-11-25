import pandas as pd
import seaborn as sns
# import statsmodels.api as sm
import matplotlib.pyplot as plt
import base64
import io

rangeland_color = "#4A86C8"
postive_color = "#1A9850"
negative_color = "#D73027"

fontname = 'Google Sans'
fontsize = 10
plt.figure(figsize=(3.75, 4))
tick_labels = {'fontname':fontname, 'fontsize':fontsize}
xtick_labels = {'fontname':fontname, 'fontsize':fontsize, "rotation":50}
axes_labels = {'fontname':fontname, 'fontsize':fontsize}

restrend_df = pd.read_csv(r"data/final_trend_stats_municipality_withPA.csv")

def make_rangeland_barplot(restrend_df = restrend_df):
    restrend_df = restrend_df[~(restrend_df["ha_rangeland"] == 0)] #Removing municipalities with no rangeland

    grouped_province = restrend_df.groupby(by='province').sum().reset_index()[["province", "ha_rangeland"]]
    ## Add dummy data to dataframe for madhesh
    grouped_province.loc[len(grouped_province)] = {"province": "Madhesh", "ha_rangeland":0}

    grouped_province = grouped_province.sort_values(by='ha_rangeland', ascending= False)


    sns.despine(top=True, right=True)
    sns.set_style(style='ticks')
    sns.barplot(data=grouped_province, x="province", y="ha_rangeland", legend=False, linewidth=0, edgecolor=".3", facecolor=rangeland_color, width=0.6)

    plt.xticks(ticks=range(0, 7), labels = grouped_province.province, **xtick_labels)
    plt.yticks(ticks=range(0,1200000,200000), labels=range(0,1200000,200000), **tick_labels)
    plt.xlabel("")#('Districts in Karnali Province', **axes_labels)

    plt.ylabel('Area (ha)', **axes_labels, labelpad=-2)
    sns.despine(top=True, right=True)
    plt.xticks(ha="right")
    plt.tick_params(pad=1)
    plt.tight_layout()
    plt.show()

def make_rangeland_barplot_b64(
    restrend_df,
    rangeland_color,
    tick_labels,
    axes_labels,
    xtick_labels,
    figsize=(4, 2.5),
    dpi=120,
):
    import io, base64
    import matplotlib.pyplot as plt
    import seaborn as sns

    ALL_PROVINCES = ["Koshi", "Madhesh", "Bagmati", "Gandaki",
                     "Lumbini", "Karnali", "Sudurpashchim"]

    df = restrend_df[restrend_df["ha_rangeland"] != 0]
    grouped = df.groupby("province", as_index=False)["ha_rangeland"].sum()

    # Ensure every province is present, even with 0
    grouped = (
        grouped.set_index("province")
        .reindex(ALL_PROVINCES, fill_value=0)
        .reset_index()
        .sort_values("ha_rangeland", ascending=False)
    )

    with sns.axes_style("ticks"):
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        sns.barplot(
            data=grouped, x="province", y="ha_rangeland",
            order=grouped["province"],           # explicit, matches labels
            color=rangeland_color,
            edgecolor=".3", linewidth=0, width=0.6,
            ax=ax,
        )

        ax.set_xlabel("")
        ax.set_ylabel("Area (ha)", **axes_labels)
        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels(
            grouped["province"],
            ha="right", rotation=30, **xtick_labels
        )
        ax.set_yticks(range(0, 1200000, 200000))
        ax.set_yticklabels(range(0, 1200000, 200000), **tick_labels)
        ax.tick_params(pad=1)
        sns.despine(top=True, right=True, ax=ax)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()
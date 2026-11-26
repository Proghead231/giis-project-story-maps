import pandas as pd
import seaborn as sns
# import statsmodels.api as sm
import matplotlib.pyplot as plt
import base64
import io
from IPython.display import HTML, display
import pandas as pd
import plotly.graph_objects as go

# rangeland_color = "#4A86C8"
# postive_color = "#1A9850"
# negative_color = "#D73027"

# fontname = 'Google Sans'
# fontsize = 10
# plt.figure(figsize=(3.75, 4))
# tick_labels = {'fontname':fontname, 'fontsize':fontsize}
# xtick_labels = {'fontname':fontname, 'fontsize':fontsize, "rotation":50}
# axes_labels = {'fontname':fontname, 'fontsize':fontsize}

# restrend_df = pd.read_csv(r"data/final_trend_stats_municipality_withPA.csv")

# def make_rangeland_barplot(restrend_df = restrend_df):
#     restrend_df = restrend_df[~(restrend_df["ha_rangeland"] == 0)] #Removing municipalities with no rangeland

#     grouped_province = restrend_df.groupby(by='province').sum().reset_index()[["province", "ha_rangeland"]]
#     ## Add dummy data to dataframe for madhesh
#     grouped_province.loc[len(grouped_province)] = {"province": "Madhesh", "ha_rangeland":0}

#     grouped_province = grouped_province.sort_values(by='ha_rangeland', ascending= False)


#     sns.despine(top=True, right=True)
#     sns.set_style(style='ticks')
#     sns.barplot(data=grouped_province, x="province", y="ha_rangeland", legend=False, linewidth=0, edgecolor=".3", facecolor=rangeland_color, width=0.6)

#     plt.xticks(ticks=range(0, 7), labels = grouped_province.province, **xtick_labels)
#     plt.yticks(ticks=range(0,1200000,200000), labels=range(0,1200000,200000), **tick_labels)
#     plt.xlabel("")#('Districts in Karnali Province', **axes_labels)

#     plt.ylabel('Area (ha)', **axes_labels, labelpad=-2)
#     sns.despine(top=True, right=True)
#     plt.xticks(ha="right")
#     plt.tick_params(pad=1)
#     plt.tight_layout()
#     plt.show()

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

def plot_lc_stats():
    display(
        HTML(
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;700&display=swap">'
        )
    )

    data = {
        "land_class": [
            "Impervious areas",
            "Snow and ice",
            "Waterbodies",
            "Croplands",
            "Shrublands",
            "Grasslands",
            "Bare lands",
            "Forest",
        ],
        "area_km2": [
            2.41e5,
            1.96e6,
            3.95e6,
            7.77e6,
            1.24e7,
            1.50e7,
            3.28e7,
            3.73e7,
        ],
        "pct_label": [
            "0.66%",
            "12.81%",
            "3.56%",
            "6.90%",
            "11.49%",
            "13.37%",
            "16.51%",
            "28.35%",
        ],
    }

    df = pd.DataFrame(data)
    total_km2 = df["area_km2"].sum()
    df["area_m_km2"] = df["area_km2"] / 1e6
    df["share_of_sum_pct"] = df["area_km2"] / total_km2 * 100

    single_color = "#2780e3"
    doi_url = "https://doi.org/10.1080/01431161.2012.748992"

    fig = go.Figure(
        go.Bar(
            x=df["area_m_km2"],
            y=df["land_class"],
            orientation="h",
            width=0.72,
            marker=dict(color=single_color, line=dict(width=0)),
            text=[f"{val:.2f}" for val in df["area_m_km2"]],
            textposition="outside",
            textfont=dict(size=13, family="Be Vietnam Pro, sans-serif", color="#222222"),
            cliponaxis=False,
            customdata=list(zip(df["area_km2"], df["share_of_sum_pct"], df["pct_label"])),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Area: %{customdata[0]:,.0f} km² (%{x:.2f}M km²)<br>"
                "Share of plotted sum: %{customdata[1]:.1f}%<br>"
                "Reported % value: %{customdata[2]}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        # title=dict(
        #     text=(
        #         f'<a href="{doi_url}" target="_blank" rel="noopener noreferrer" '
        #         f'style="color:#222222; text-decoration:underline; font-weight:700; font-size:12">'
        #         f"Source: Gong et al. (2012)</a>"
        #     ),
        #     font=dict(size=17, family="Be Vietnam Pro, sans-serif", color="#222222"),
        #     x=0,
        # ),
        xaxis=dict(
            title=dict(
                text="Area (Million Km²)",
                font=dict(size=14, family="Be Vietnam Pro, sans-serif", color="#222222"),
            ),
            range=[0, 48],
            showgrid=False,
            showline=True,
            linecolor="#444444",
            linewidth=1.2,
            ticks="outside",
            tickcolor="#444444",
            tickfont=dict(size=13, family="Be Vietnam Pro, sans-serif", color="#222222"),
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(
                text="",
                font=dict(size=14, family="Be Vietnam Pro, sans-serif", color="#222222"),
            ),
            showgrid=False,
            showline=True,
            linecolor="#444444",
            linewidth=1.2,
            ticks="",
            # tickcolor="#444444",
            tickfont=dict(size=13, family="Be Vietnam Pro, sans-serif", color="#222222"),
            fixedrange=True,
        ),
        font=dict(family="Be Vietnam Pro, sans-serif", size=13, color="#222222"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=15, r=25, t=48, b=45),
        height=380,
    )

    fig.show(config={"displayModeBar": False, "responsive": True})
    plt.close("all")
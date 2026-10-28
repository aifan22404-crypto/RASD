"""Page 4 — Bidder Connections."""
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from rasd import data_access as da
from rasd import ui
from rasd.i18n import t

db, res = da.get()

st.title(t("nav_connections"))
tid = ui.tender_selector(db)
nodes, bidders, links = da.connection_graph(db, tid)

OWNER_RED, OWNER_GREY, PHONE_ORANGE, ADDRESS_GREY = "#C62828", "#3E4C59", "#EF8F00", "#9AA5B1"
NODE_COLOR = "#0B5394"


def edge_style(link: dict) -> tuple[str, str]:
    if link["link_type"] == "owner":
        return (OWNER_GREY if link["disclosed"] else OWNER_RED), "solid"
    if link["link_type"] == "phone":
        return PHONE_ORANGE, "dash"
    return ADDRESS_GREY, "dot"


def edge_text(link: dict) -> str:
    if link["link_type"] == "owner":
        key = "edge_owner_d" if link["disclosed"] else "edge_owner_nd"
        return t(key, value=link["value"], group=link["group"])
    return t(f"edge_{link['link_type']}", value=link["value"])


graph = nx.MultiGraph()
graph.add_nodes_from(nodes)
graph.add_edges_from((lk["a"], lk["b"]) for lk in links)
pos = nx.spring_layout(graph, seed=42)

fig = go.Figure()
mid_x, mid_y, mid_text = [], [], []
for lk in links:
    (x0, y0), (x1, y1) = pos[lk["a"]], pos[lk["b"]]
    color, dash = edge_style(lk)
    fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", hoverinfo="skip", showlegend=False,
                             line=dict(color=color, width=3, dash=dash)))
    mid_x.append((x0 + x1) / 2)
    mid_y.append((y0 + y1) / 2)
    mid_text.append(f"{lk['a']} — {lk['b']}: {edge_text(lk)}")
if links:  # invisible midpoint markers carry the edge hover text
    fig.add_trace(go.Scatter(x=mid_x, y=mid_y, mode="markers", marker=dict(size=14, opacity=0),
                             hovertext=mid_text, hoverinfo="text", showlegend=False))

co = db["companies"].set_index("company_id")
for filled in (True, False):
    group = [n for n in nodes if (n in bidders) == filled]
    if not group:
        continue
    hover = [f"<b>{n}</b> — {co.loc[n, 'name_en']}<br>{t('hover_owner')}: {co.loc[n, 'owner_id']}"
             f"<br>{t('hover_emirate')}: {co.loc[n, 'emirate']}<br>{t('hover_size')}: {co.loc[n, 'size']}" for n in group]
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in group], y=[pos[n][1] for n in group], mode="markers+text",
        text=group, textposition="top center", textfont=dict(size=14, color="#1F2933"),
        hovertext=hover, hoverinfo="text", showlegend=False,
        marker=dict(size=34, color=NODE_COLOR if filled else "#FFFFFF", line=dict(color=NODE_COLOR, width=3)),
    ))
fig.update_layout(height=460, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="#FFFFFF",
                  xaxis=dict(visible=False), yaxis=dict(visible=False), title=t("graph_title"))
with ui.ltr_container("network"):
    st.plotly_chart(fig, width="stretch")


def legend_line(color: str, style: str) -> str:
    return f'<span class="rasd-legend-line" style="border-top: 3px {style} {color}"></span>'


st.markdown(
    f"**{t('legend_title')}**<br>"
    f"{legend_line(OWNER_RED, 'solid')}{t('legend_owner')}<br>"
    f"{legend_line(OWNER_GREY, 'solid')}{t('legend_owner_disclosed')}<br>"
    f"{legend_line(PHONE_ORANGE, 'dashed')}{t('legend_phone')}<br>"
    f"{legend_line(ADDRESS_GREY, 'dotted')}{t('legend_address')}<br>"
    f"{t('legend_nodes')}",
    unsafe_allow_html=True,
)

st.subheader(t("links_table"))
if links:
    def disclosed(link):
        if link["disclosed"] is None:
            return "—"
        return f"{t('yes')} ({link['group']})" if link["disclosed"] else t("no")

    st.dataframe(pd.DataFrame([{
        t("col_company_a"): da.company_label(db, lk["a"]),
        t("col_company_b"): da.company_label(db, lk["b"]),
        t("col_link_type"): t(f"link_{lk['link_type']}"),
        t("col_link_value"): lk["value"],
        t("col_disclosed"): disclosed(lk),
    } for lk in links]), hide_index=True, width="stretch")
else:
    st.info(t("no_links"))

st.caption(t("conn_caption"))

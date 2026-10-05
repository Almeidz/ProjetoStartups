import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Radar de Startups Brasil",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Radar de Startups Brasil")
st.markdown("### Lucas de Almeida Brugger Cavalcante")
st.caption("Linguagem de Programação • Professor: Louzada • G1 — 2026")
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados/simulacao_startups_brasil.csv")
    df["data"] = pd.to_datetime(df["data"])
    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month
    df["periodo"] = df["data"].dt.to_period("M").astype(str)
    df["resultado_financeiro"] = df["faturamento"] - df["investimento_recebido"]
    df["retorno_sobre_investimento"] = np.where(
        df["investimento_recebido"] > 0,
        df["faturamento"] / df["investimento_recebido"],
        np.nan
    )
    return df

df = carregar_dados()

st.title("🚀 Radar de Startups Brasil")
st.markdown(
    "**Pergunta de negócio:** como investimento, setor, tecnologia e localização "
    "se relacionam com o desempenho financeiro das startups brasileiras?"
)
st.caption("Base analisada: 2015–2024 | 4.440 registros | 199 startups únicas")

st.sidebar.header("Filtros")

def filtro_multiselect(label, coluna):
    opcoes = sorted(df[coluna].dropna().unique().tolist())
    return st.sidebar.multiselect(label, opcoes, default=opcoes)

anos = st.sidebar.multiselect(
    "Ano",
    sorted(df["ano"].unique()),
    default=sorted(df["ano"].unique())
)
regioes = filtro_multiselect("Região", "regiao")
ufs = filtro_multiselect("UF", "uf")
setores = filtro_multiselect("Setor", "setor")
tecnologias = filtro_multiselect("Tecnologia", "tecnologia_principal")
estagios = filtro_multiselect("Estágio", "estagio")
inovacoes = filtro_multiselect("Nível de inovação", "nivel_inovacao")

cidades_disponiveis = sorted(
    df.loc[
        df["regiao"].isin(regioes) & df["uf"].isin(ufs),
        "cidade"
    ].unique()
)
cidades = st.sidebar.multiselect("Cidade", cidades_disponiveis, default=cidades_disponiveis)

filtrado = df[
    df["ano"].isin(anos)
    & df["regiao"].isin(regioes)
    & df["uf"].isin(ufs)
    & df["setor"].isin(setores)
    & df["tecnologia_principal"].isin(tecnologias)
    & df["estagio"].isin(estagios)
    & df["nivel_inovacao"].isin(inovacoes)
    & df["cidade"].isin(cidades)
].copy()

if filtrado.empty:
    st.warning("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()

# KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Startups únicas", f"{filtrado['startup'].nunique():,}".replace(",", "."))
c2.metric("Investimento", f"R$ {filtrado['investimento_recebido'].sum()/1e6:.2f} mi")
c3.metric("Faturamento", f"R$ {filtrado['faturamento'].sum()/1e6:.2f} mi")
c4.metric("Crescimento médio", f"{filtrado['crescimento_percentual'].mean():.1f}%")
c5.metric("Funcionários", f"{filtrado['funcionarios'].sum():,}".replace(",", "."))

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Visão geral", "📈 Evolução temporal", "🔎 Relações e detalhes"])

with tab1:
    col1, col2 = st.columns(2)

    regiao = (
        filtrado.groupby("regiao", as_index=False)
        .agg(investimento=("investimento_recebido", "sum"),
             faturamento=("faturamento", "sum"))
        .sort_values("investimento", ascending=False)
    )
    fig = px.bar(
        regiao,
        x="regiao",
        y=["investimento", "faturamento"],
        barmode="group",
        title="Investimento e faturamento por região"
    )
    fig.update_layout(yaxis_title="Valor (R$)", xaxis_title="")
    col1.plotly_chart(fig, use_container_width=True)

    setor = (
        filtrado.groupby("setor", as_index=False)
        .agg(faturamento=("faturamento", "sum"),
             crescimento=("crescimento_percentual", "mean"))
        .sort_values("faturamento", ascending=False)
    )
    fig2 = px.bar(
        setor,
        x="faturamento",
        y="setor",
        orientation="h",
        title="Faturamento por setor"
    )
    fig2.update_layout(xaxis_title="Faturamento (R$)", yaxis_title="")
    col2.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    tech = (
        filtrado.groupby("tecnologia_principal", as_index=False)
        .agg(faturamento=("faturamento", "sum"),
             crescimento=("crescimento_percentual", "mean"))
        .sort_values("faturamento", ascending=False)
    )
    fig3 = px.bar(
        tech,
        x="tecnologia_principal",
        y="faturamento",
        title="Faturamento por tecnologia"
    )
    fig3.update_layout(yaxis_title="Faturamento (R$)", xaxis_title="")
    col3.plotly_chart(fig3, use_container_width=True)

    est = (
        filtrado.groupby("estagio", as_index=False)
        .agg(investimento=("investimento_recebido", "sum"),
             crescimento=("crescimento_percentual", "mean"))
    )
    fig4 = px.bar(
        est,
        x="estagio",
        y="investimento",
        title="Investimento por estágio"
    )
    fig4.update_layout(yaxis_title="Investimento (R$)", xaxis_title="")
    col4.plotly_chart(fig4, use_container_width=True)

with tab2:
    temporal = (
        filtrado.groupby("periodo", as_index=False)
        .agg(
            investimento=("investimento_recebido", "sum"),
            faturamento=("faturamento", "sum"),
            crescimento=("crescimento_percentual", "mean")
        )
    )
    temporal["media_movel_investimento_12m"] = temporal["investimento"].rolling(12).mean()
    temporal["media_movel_faturamento_12m"] = temporal["faturamento"].rolling(12).mean()

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=temporal["periodo"], y=temporal["investimento"],
        mode="lines", name="Investimento"
    ))
    fig5.add_trace(go.Scatter(
        x=temporal["periodo"], y=temporal["faturamento"],
        mode="lines", name="Faturamento"
    ))
    fig5.add_trace(go.Scatter(
        x=temporal["periodo"], y=temporal["media_movel_investimento_12m"],
        mode="lines", name="Média móvel investimento (12m)"
    ))
    fig5.add_trace(go.Scatter(
        x=temporal["periodo"], y=temporal["media_movel_faturamento_12m"],
        mode="lines", name="Média móvel faturamento (12m)"
    ))
    fig5.update_layout(
        title="Evolução mensal e médias móveis de 12 meses",
        xaxis_title="Período",
        yaxis_title="Valor (R$)"
    )
    st.plotly_chart(fig5, use_container_width=True)

    crescimento = temporal[["periodo", "crescimento"]]
    fig6 = px.line(
        crescimento,
        x="periodo",
        y="crescimento",
        title="Crescimento percentual médio ao longo do tempo",
        markers=True
    )
    fig6.update_layout(yaxis_title="Crescimento médio (%)", xaxis_title="Período")
    st.plotly_chart(fig6, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)

    amostra = filtrado.sample(min(1500, len(filtrado)), random_state=42)
    fig7 = px.scatter(
        amostra,
        x="investimento_recebido",
        y="faturamento",
        color="setor",
        hover_data=["startup", "uf", "cidade", "tecnologia_principal"],
        title="Investimento recebido x faturamento"
    )
    fig7.update_layout(
        xaxis_title="Investimento recebido (R$)",
        yaxis_title="Faturamento (R$)"
    )
    col1.plotly_chart(fig7, use_container_width=True)

    corr_cols = [
        "funcionarios", "investimento_recebido",
        "faturamento", "crescimento_percentual"
    ]
    corr = filtrado[corr_cols].corr()
    fig8 = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        title="Matriz de correlação"
    )
    col2.plotly_chart(fig8, use_container_width=True)

    st.subheader("Ranking de UFs")
    ranking = (
        filtrado.groupby("uf", as_index=False)
        .agg(
            startups=("startup", "nunique"),
            investimento=("investimento_recebido", "sum"),
            faturamento=("faturamento", "sum"),
            crescimento_medio=("crescimento_percentual", "mean")
        )
        .sort_values("faturamento", ascending=False)
    )
    st.dataframe(ranking, use_container_width=True, hide_index=True)

st.divider()

# Interpretação executiva
top_regiao = (
    filtrado.groupby("regiao")["investimento_recebido"].sum().idxmax()
)
top_setor = (
    filtrado.groupby("setor")["faturamento"].sum().idxmax()
)
top_tech = (
    filtrado.groupby("tecnologia_principal")["faturamento"].sum().idxmax()
)
corr_if = filtrado[["investimento_recebido", "faturamento"]].corr().iloc[0, 1]

st.subheader("🧠 Interpretação executiva")
st.markdown(
    f"""
    - A região com maior volume de investimento no recorte selecionado é **{top_regiao}**.
    - O setor com maior faturamento acumulado é **{top_setor}**.
    - A tecnologia com maior faturamento acumulado é **{top_tech}**.
    - A correlação entre investimento e faturamento no recorte atual é **{corr_if:.2f}**.

    **Conclusão:** os resultados reforçam que desempenho de startups deve ser analisado por múltiplas dimensões.
    O dashboard permite alterar os filtros para verificar se essas conclusões permanecem válidas em diferentes
    regiões, anos, setores, tecnologias e estágios.
    """
)

st.caption("Projeto acadêmico — Avaliação G1 | Linguagem de Programação")

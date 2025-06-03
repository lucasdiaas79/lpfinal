# LP Agregados - Sistema com Botões de Pagamento Frete e Material Separados
import streamlit as st
import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
from PIL import Image

st.set_page_config(page_title="LP Agregados - Dashboard", layout="wide")

# Logo condicional
logo_path = "Screenshot_25.png"
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.sidebar.image(logo, width=150)
else:
    st.sidebar.warning("Logo não encontrada.")

# Autorização e leitura dos dados
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1bL_DHWIS8Su5wGIoXCSFUUGhxnjkgrvNbsE_FLZVVNc").sheet1
valores = sheet.get_all_values()
headers, dados = valores[0], valores[1:]
df = pd.DataFrame(dados, columns=headers)

# Normalização de colunas
df.columns = [col.lower().strip() for col in df.columns]

# Conversões e validações
for col in ["custo do material", "custo do frete", "preço de venda"]:
    df[col] = pd.to_numeric(df.get(col, 0), errors="coerce")
for col in ["pagamento material", "pagamento frete", "entregue", "cliente pagou"]:
    if col not in df.columns:
        df[col] = ["não"] * len(df)
    df[col] = df[col].astype(str).str.lower()

# Menu lateral
aba = st.sidebar.radio("Menu", [
    "📊 Visão Geral", "📋 Novo Pedido", "👥 Clientes", "💰 Financeiro", "📈 Relatórios", "⚙️ Configurações"])

# Aba: Visão Geral
def visao_geral():
    ...  # já implementado anteriormente

# Execução da aba selecionada
if aba == "📊 Visão Geral":
    visao_geral()
elif aba == "📋 Novo Pedido":
    ...  # já implementado anteriormente
elif aba == "👥 Clientes":
    st.subheader("👥 Relatório por Cliente")
    if 'cliente' in df.columns:
        clientes = df.groupby('cliente').agg({
            'preço de venda': 'sum',
            'pagamento material': lambda x: (x == 'sim').sum(),
            'entregue': lambda x: (x == 'sim').sum(),
        }).rename(columns={
            'preço de venda': 'Total Faturado',
            'pagamento material': 'Materiais Pagos',
            'entregue': 'Entregas Realizadas'
        })
        st.dataframe(clientes)
elif aba == "💰 Financeiro":
    st.subheader("💰 Painel Financeiro")
    total_vendido = df["preço de venda"].sum()
    total_recebido = df.loc[(df["pagamento material"] == "sim") & (df["pagamento frete"] == "sim"), "preço de venda"].sum()
    lucro_bruto = total_vendido - (df["custo do material"].sum() + df["custo do frete"].sum())

    st.metric("Total Vendido", f"R$ {total_vendido:,.2f}")
    st.metric("Total Recebido", f"R$ {total_recebido:,.2f}")
    st.metric("Lucro Bruto", f"R$ {lucro_bruto:,.2f}")
elif aba == "📈 Relatórios":
    st.subheader("📈 Relatórios com Filtros")

    if 'tipo de material' in df.columns:
        fig_mat = px.histogram(df, x='tipo de material', title='Volume por Tipo de Material')
        st.plotly_chart(fig_mat, use_container_width=True)

    if 'caçambeiro' in df.columns:
        fig_cac = px.histogram(df, x='caçambeiro', title='Entregas por Caçambeiro')
        st.plotly_chart(fig_cac, use_container_width=True)

    df_pago = df[(df['pagamento material'] == 'sim') & (df['pagamento frete'] == 'sim')].copy()
    if not df_pago.empty:
        df_pago['lucro'] = df_pago['preço de venda'] - (df_pago['custo do material'] + df_pago['custo do frete'])
        fig_lucro = px.bar(df_pago, x='cliente', y='lucro', title='Lucro por Cliente')
        st.plotly_chart(fig_lucro, use_container_width=True)

    st.markdown("---")
    filtro_entregue = st.selectbox("Filtrar por entrega", ["todos", "sim", "não"])
    filtro_pag_mat = st.selectbox("Filtrar por pagamento material", ["todos", "sim", "não"])
    filtro_pag_frete = st.selectbox("Filtrar por pagamento frete", ["todos", "sim", "não"])

    df_filtrado = df.copy()
    if filtro_entregue != "todos":
        df_filtrado = df_filtrado[df_filtrado["entregue"] == filtro_entregue]
    if filtro_pag_mat != "todos":
        df_filtrado = df_filtrado[df_filtrado["pagamento material"] == filtro_pag_mat]
    if filtro_pag_frete != "todos":
        df_filtrado = df_filtrado[df_filtrado["pagamento frete"] == filtro_pag_frete]

    st.dataframe(df_filtrado)
elif aba == "⚙️ Configurações":
    st.subheader("⚙️ Configurações do Sistema")
    if st.button("Zerar Planilha"):
        sheet.clear()
        sheet.append_row(headers)
        st.success("Todos os dados foram apagados. Apenas o cabeçalho foi mantido.")

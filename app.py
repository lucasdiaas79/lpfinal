# LP Agregados - Sistema com Botões de Pagamento Frete e Material Separados
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.express as px
from PIL import Image

st.set_page_config(page_title="LP Agregados - Dashboard", layout="wide")

# Logo
logo = Image.open("/mnt/data/Screenshot_25.png")
st.sidebar.image(logo, use_column_width=True)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
info = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_ID = "1bL_DHWIS8Su5wGIoXCSFUUGhxnjkgrvNbsE_FLZVVNc"
sheet = client.open_by_key(SHEET_ID).sheet1
valores = sheet.get_all_values()
headers = valores[0]
dados = valores[1:]
df = pd.DataFrame(dados, columns=headers)

df.columns = [col.lower().strip() for col in df.columns]
for col in ["custo do material", "custo do frete", "preço de venda"]:
    df[col] = pd.to_numeric(df.get(col, 0), errors="coerce")
for col in ["pagamento material", "pagamento frete", "entregue"]:
    if col not in df.columns:
        df[col] = "não"
    df[col] = df[col].astype(str).str.lower()

aba = st.sidebar.radio("Menu", [
    "📊 Visão Geral", "📋 Novo Pedido", "👥 Clientes", "💰 Financeiro", "📈 Relatórios", "⚙️ Configurações"])

if aba == "📊 Visão Geral":
    st.subheader("📊 Visão Geral do Sistema")

    total_entregas = len(df)
    entregues = df["entregue"].value_counts().get("sim", 0)
    pagos_material = df["pagamento material"].value_counts().get("sim", 0)
    lucro = df["preço de venda"].sum() - (df["custo do material"].sum() + df["custo do frete"].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚚 Entregas Totais", total_entregas)
    with col2:
        st.metric("📦 Entregues", entregues)
    with col3:
        st.metric("💵 Materiais Pagos", pagos_material)
    with col4:
        st.metric("📈 Lucro Estimado", f"R$ {lucro:,.2f}")

    st.markdown("---")
    st.subheader("📊 Gráficos Interativos")

    # Gráfico por tipo de material
    if 'tipo de material' in df.columns:
        fig_mat = px.histogram(df, x='tipo de material', title='Volume por Tipo de Material')
        st.plotly_chart(fig_mat, use_container_width=True)

    # Gráfico de entregas por caçambeiro
    if 'caçambeiro' in df.columns:
        fig_cac = px.histogram(df, x='caçambeiro', title='Entregas por Caçambeiro')
        st.plotly_chart(fig_cac, use_container_width=True)

    # Gráfico de lucro por cliente (apenas os que pagaram)
    df_pago = df[(df['pagamento material'] == 'sim') & (df['pagamento frete'] == 'sim')]
    if not df_pago.empty:
        df_pago['lucro'] = df_pago['preço de venda'] - (df_pago['custo do material'] + df_pago['custo do frete'])
        fig_lucro = px.bar(df_pago, x='cliente', y='lucro', title='Lucro por Cliente')
        st.plotly_chart(fig_lucro, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Pedidos Recentes")

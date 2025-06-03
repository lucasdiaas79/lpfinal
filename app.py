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
for col in ["pagamento material", "pagamento frete", "entregue"]:
    df[col] = df.get(col, "não").astype(str).str.lower()

# Menu lateral
aba = st.sidebar.radio("Menu", [
    "📊 Visão Geral", "📋 Novo Pedido", "👥 Clientes", "💰 Financeiro", "📈 Relatórios", "⚙️ Configurações"])

# Aba: Visão Geral
def visao_geral():
    st.subheader("📊 Visão Geral do Sistema")

    total_entregas = len(df)
    entregues = df["entregue"].value_counts().get("sim", 0)
    pagos_material = df["pagamento material"].value_counts().get("sim", 0)
    lucro = df["preço de venda"].sum() - (df["custo do material"].sum() + df["custo do frete"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🚚 Entregas Totais", total_entregas)
    col2.metric("📦 Entregues", entregues)
    col3.metric("💵 Materiais Pagos", pagos_material)
    col4.metric("📈 Lucro Estimado", f"R$ {lucro:,.2f}")

    st.markdown("---")
    st.subheader("📊 Gráficos Interativos")

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
    st.subheader("📋 Pedidos Recentes")

# Execução da aba selecionada
if aba == "📊 Visão Geral":
    visao_geral()

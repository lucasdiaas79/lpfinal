# LP Agregados - Sistema com Visual Estilo Painel Moderno (Visual 1) + Autenticação via secrets.toml
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="LP Agregados - Dashboard", layout="wide")

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
        df[col] = "não pago" if "pagamento" in col else "não"
    df[col] = df[col].astype(str).str.lower()

st.markdown("""
    <style>
    .css-1aumxhk, .css-1v3fvcr, .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

aba = st.sidebar.radio("Menu", [
    "📊 Visão Geral", "📋 Novo Pedido", "👥 Clientes", "💰 Financeiro", "📈 Relatórios", "⚙️ Configurações"])

if aba == "📊 Visão Geral":
    st.subheader("📊 Visão Geral do Sistema")

    total_entregas = len(df)
    entregues = df["entregue"].value_counts().get("sim", 0)
    pagos_material = df["pagamento material"].value_counts().get("pago", 0)
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
    st.subheader("📋 Pedidos Recentes")

    for i, row in df.iterrows():
        cor = "#f0f0f0"
        if row["pagamento material"] == "pago" and row["pagamento frete"] == "pago" and row["entregue"] == "sim":
            cor = "#e0ffe0"
        elif row["pagamento material"] == "não pago" and row["pagamento frete"] == "não pago" and row["entregue"] == "não":
            cor = "#ffe0e0"
        else:
            cor = "#fff5cc"

        with st.container():
            st.markdown(f"""
                <div style='background-color:{cor}; padding: 1rem; border-radius: 10px; margin-bottom: 10px;'>
                    <strong>🏘️ {row['condominio']} - 📍 Lote {row['lote']}</strong><br>
                    🚚 <i>{row['caçambeiro']} - {row['tipo de caminhão']}</i><br>
                    🧱 Material: {row['tipo de material']}<br>
                    💰 Custo Material: R$ {row['custo do material']} | 🚛 Frete: R$ {row['custo do frete']}<br>
                    💸 Preço Venda: R$ {row['preço de venda']}<br>
                    👤 Cliente: {row['cliente']}<br>
                    📦 Entregue: <b>{row['entregue'].capitalize()}</b> |
                    💵 Pag. Material: <b>{row['pagamento material'].capitalize()}</b> |
                    🚛 Pag. Frete: <b>{row['pagamento frete'].capitalize()}</b>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            if col1.button("📦 Marcar como Entregue", key=f"ent_{i}"):
                sheet.update_cell(i+2, headers.index("entregue")+1, "sim")
                st.success("Entrega atualizada.")
            if col2.button("💰 Marcar Material como Pago", key=f"pagmat_{i}"):
                sheet.update_cell(i+2, headers.index("pagamento material")+1, "pago")
                st.success("Pagamento de material atualizado.")

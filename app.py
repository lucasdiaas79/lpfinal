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

    st.subheader("📋 Pedidos Recentes")
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None

    for row_num, (i, row) in enumerate(df[::-1].iterrows()):
        linha_sheet = len(valores) - row_num  # Correção: posição real da linha no Google Sheets

        with st.expander(f"👤 {row['cliente']}"):
            st.markdown(f"""
                <div style='background-color:#f9f9f9; padding: 0.5rem; border-radius: 10px; font-size: 0.95rem;'>
                    <strong>🏘️ {row['condominio']} - 📍 Lote {row['lote']}</strong><br>
                    🚛 <i>{row['caçambeiro']} - {row['tipo de caminhão']}</i><br>
                    🧱 Material: {row['tipo de material']}<br>
                    💰 Custo Material: R$ {row['custo do material']} | 🚛 Frete: R$ {row['custo do frete']}<br>
                    💸 Preço Venda: R$ {row['preço de venda']}<br>
                    📦 Entregue: {row['entregue']} |
                    💵 Pag. Material: {row['pagamento material']} |
                    🚛 Pag. Frete: {row['pagamento frete']} |
                    💰 Cliente Pagou: {row['cliente pagou']}
                </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])
            if col1.button("📦 Marcar como Entregue", key=f"ent_{i}"):
                sheet.update_cell(linha_sheet, headers.index("entregue")+1, "sim")
                st.success("Entrega atualizada.")
            if col2.button("🚛 Frete Pago", key=f"frete_{i}"):
                sheet.update_cell(linha_sheet, headers.index("pagamento frete")+1, "sim")
                st.success("Pagamento do frete atualizado.")
            if col3.button("📥 Material Pago", key=f"mat_{i}"):
                sheet.update_cell(linha_sheet, headers.index("pagamento material")+1, "sim")
                st.success("Pagamento do material atualizado.")
            if col4.button("💰 Cliente Pagou", key=f"cliente_{i}"):
                sheet.update_cell(linha_sheet, headers.index("cliente pagou")+1, "sim")
                st.success("Cliente marcado como totalmente quitado.")
            if col5.button("🗑️ Excluir Pedido", key=f"excluir_{i}"):
                st.session_state.confirm_delete = linha_sheet

            if st.session_state.confirm_delete == linha_sheet:
                st.warning(f"Deseja realmente excluir o pedido de {row['cliente']}?")
                confirm_col1, confirm_col2 = st.columns([1, 1])
                if confirm_col1.button("✅ Sim, excluir", key=f"confirm_{i}"):
                    sheet.delete_row(linha_sheet)
                    st.success("Pedido excluído com sucesso.")
                    st.session_state.confirm_delete = None
                    st.experimental_rerun()
                if confirm_col2.button("❌ Cancelar", key=f"cancel_{i}"):
                    st.session_state.confirm_delete = Nonelen(valores) - row_num  # Correção: posição real da linha no Google Sheets

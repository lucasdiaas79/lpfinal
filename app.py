from pathlib import Path

# Conteúdo completo do app.py atualizado com recarga automática
codigo_app = """
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

# Função para carregar dados
def carregar_dados():
    valores = sheet.get_all_values()
    headers = valores[0]
    dados = valores[1:]
    df = pd.DataFrame(dados, columns=headers)
    df.columns = [col.lower().strip() for col in df.columns]

    for col in ["custo do material", "custo do frete", "preço de venda"]:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce")
    for col in ["pagamento material", "pagamento frete", "entregue", "cliente pagou"]:
        if col not in df.columns:
            df[col] = ["não"] * len(df)
        df[col] = df[col].astype(str).str.lower()
    return df, headers

# Inicialização reativa
if "df" not in st.session_state or st.session_state.get("reload", False):
    st.session_state.df, st.session_state.headers = carregar_dados()
    st.session_state.reload = False

df = st.session_state.df
headers = st.session_state.headers

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
    for i, row in df[::-1].iterrows():
        cor = "#fff5cc"
        alerta = ""
        if row["cliente pagou"] == "sim":
            cor = "#e0ffe0"
        elif row["pagamento material"] == "não" and row["pagamento frete"] == "não" and row["entregue"] == "não":
            alerta = "❗ Pedido totalmente pendente."
            cor = "#ffe0e0"

        with st.expander(f"👤 {row['cliente']}"):
            st.markdown(f'''
                <div style='background-color:{cor}; padding: 0.5rem; border-radius: 10px; font-size: 0.95rem;'>
                    <div style='color: red; font-weight: bold;'>{alerta}</div>
                    <strong>🏘️ {row['condominio']} - 📍 Lote {row['lote']}</strong><br>
                    🚚 <i>{row['caçambeiro']} - {row['tipo de caminhão']}</i><br>
                    🧱 Material: {row['tipo de material']}<br>
                    💰 Custo Material: R$ {row['custo do material']} | 🚛 Frete: R$ {row['custo do frete']}<br>
                    💸 Preço Venda: R$ {row['preço de venda']}<br>
                    👤 Cliente: {row['cliente']}<br>
                    📦 Entregue: <b>{row['entregue'].capitalize()} ✅</b> |
                    💵 Pag. Material: <b>{row['pagamento material'].capitalize()} ✅</b> |
                    🚛 Pag. Frete: <b>{row['pagamento frete'].capitalize()} ✅</b> |
                    💰 Cliente Pagou: <b>{row['cliente pagou'].capitalize()} ✅</b>
                </div>
            ''', unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            if col1.button("📦 Marcar como Entregue", key=f"ent_{i}"):
                sheet.update_cell(i+2, headers.index("entregue")+1, "sim")
                st.session_state.reload = True
                st.experimental_rerun()
            if col2.button("🚛 Frete Pago", key=f"frete_{i}"):
                sheet.update_cell(i+2, headers.index("pagamento frete")+1, "sim")
                st.session_state.reload = True
                st.experimental_rerun()
            if col3.button("📥 Material Pago", key=f"mat_{i}"):
                sheet.update_cell(i+2, headers.index("pagamento material")+1, "sim")
                st.session_state.reload = True
                st.experimental_rerun()
            if col4.button("💰 Cliente Pagou", key=f"cliente_{i}"):
                sheet.update_cell(i+2, headers.index("cliente pagou")+1, "sim")
                st.session_state.reload = True
                st.experimental_rerun()

            excluir = st.button("🗑️ Excluir Pedido", key=f"del_{i}")
            if excluir:
                sheet.delete_rows(i+2)
                st.session_state.reload = True
                st.experimental_rerun()

# Abas
if aba == "📊 Visão Geral":
    visao_geral()
"""

# Salvando como app.py
caminho = "/mnt/data/app.py"
Path(caminho).write_text(codigo_app)
caminho

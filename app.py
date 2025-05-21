# LP Agregados - Sistema com Visual Estilo Painel Moderno (Visual 1) + Autenticação via secrets.toml
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="LP Agregados - Dashboard", layout="wide")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# ✅ Autenticação segura via Streamlit secrets
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
df["custo da areia"] = pd.to_numeric(df.get("custo da areia", 0), errors="coerce")
df["custo de venda"] = pd.to_numeric(df.get("custo de venda", 0), errors="coerce")
df["pago"] = df.get("pago", "não").astype(str).str.lower()
df["entregue"] = df.get("entregue", "não").astype(str).str.lower()

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
    pagos = df["pago"].value_counts().get("sim", 0)
    lucro = df["custo de venda"].sum() - df["custo da areia"].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚚 Entregas Totais", total_entregas)
    with col2:
        st.metric("📦 Entregues", entregues)
    with col3:
        st.metric("💵 Pagos", pagos)
    with col4:
        st.metric("📈 Lucro Estimado", f"R$ {lucro:,.2f}")

    st.markdown("---")
    st.subheader("📋 Pedidos Recentes")

    for i, row in df.iterrows():
        cor = "#f0f0f0"
        if row["pago"] == "sim" and row["entregue"] == "sim":
            cor = "#e0ffe0"
        elif row["pago"] == "não" and row["entregue"] == "não":
            cor = "#ffe0e0"
        elif row["pago"] == "não" or row["entregue"] == "não":
            cor = "#fff5cc"

        with st.container():
            st.markdown(f"""
                <div style='background-color:{cor}; padding: 1rem; border-radius: 10px; margin-bottom: 10px;'>
                    <strong>🏘️ {row['condominio']} - 📍 Lote {row['lote']}</strong><br>
                    🚚 <i>{row['caçambeiro']}</i><br>
                    💰 Custo de Venda: R$ {row['custo de venda']}<br>
                    🏗️ Custo da Areia: R$ {row['custo da areia']}<br>
                    📦 Entregue: <b>{row['entregue'].capitalize()}</b> | 💵 Pago: <b>{row['pago'].capitalize()}</b><br><br>
                </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            if col1.button("📦 Marcar como Entregue", key=f"ent_{i}"):
                sheet.update_cell(i+2, headers.index("entregue")+1, "sim")
                st.success("Entrega atualizada.")
            if col2.button("💰 Marcar como Pago", key=f"pago_{i}"):
                sheet.update_cell(i+2, headers.index("pago")+1, "sim")
                st.success("Pagamento atualizado.")

elif aba == "📋 Novo Pedido":
    st.subheader("📋 Cadastrar Novo Pedido")
    with st.form("novo_pedido"):
        tipo_areia = st.selectbox("Tipo de Areia", ["Grossa", "Fina", "Mista"])
        condominio = st.text_input("Condomínio")
        lote = st.text_input("Lote")
        cacambeiro = st.text_input("Caçambeiro")
        custo_areia = st.number_input("Custo da Areia (R$)", min_value=0.0, step=0.01)
        custo_venda = st.number_input("Custo de Venda (R$)", min_value=0.0, step=0.01)
        entregue = st.selectbox("Entregue?", ["sim", "não"])
        pago = st.selectbox("Pago?", ["sim", "não"])
        submit = st.form_submit_button("Salvar Pedido")
    if submit:
        nova_linha = [tipo_areia, condominio, lote, cacambeiro, str(custo_areia), str(custo_venda), entregue, pago]
        sheet.append_row(nova_linha)
        st.success("✅ Pedido cadastrado com sucesso!")

elif aba == "👥 Clientes":
    st.subheader("👥 Clientes com Pendência")
    df_clientes = df[df["pago"] == "não"]
    clientes = df_clientes[["condominio", "lote", "custo de venda"]]
    st.dataframe(clientes, use_container_width=True)

elif aba == "💰 Financeiro":
    st.subheader("💰 Resumo Financeiro")
    total_vendas = df["custo de venda"].sum()
    total_custos = df["custo da areia"].sum()
    total_pago = df[df["pago"] == "sim"]["custo de venda"].sum()
    caixa = total_pago
    st.metric("Total Vendido", f"R$ {total_vendas:,.2f}")
    st.metric("Total Recebido", f"R$ {caixa:,.2f}")
    st.metric("Lucro Bruto", f"R$ {total_vendas - total_custos:,.2f}")

elif aba == "📈 Relatórios":
    st.subheader("📈 Relatórios de Pedidos")
    filtro_entregue = st.selectbox("Filtrar por Entregue", ["todos", "sim", "não"])
    filtro_pago = st.selectbox("Filtrar por Pago", ["todos", "sim", "não"])
    df_filtrado = df.copy()
    if filtro_entregue != "todos":
        df_filtrado = df_filtrado[df_filtrado["entregue"] == filtro_entregue]
    if filtro_pago != "todos":
        df_filtrado = df_filtrado[df_filtrado["pago"] == filtro_pago]
    st.dataframe(df_filtrado, use_container_width=True)

elif aba == "⚙️ Configurações":
    st.subheader("⚙️ Configurações do Sistema")
    st.warning("⚠️ Isso vai apagar todos os dados da planilha!")
    if st.button("🧹 ZERAR SISTEMA COMPLETO"):
        sheet.resize(rows=1)
        st.success("Todos os dados foram apagados com sucesso!")

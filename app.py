# LP Agregados - Sistema com Visual Estilo Painel Moderno (Atualizado)
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
df["custo do material"] = pd.to_numeric(df.get("custo do material", 0), errors="coerce")
df["custo do frete"] = pd.to_numeric(df.get("custo do frete", 0), errors="coerce")
df["preço de venda"] = pd.to_numeric(df.get("preço de venda", 0), errors="coerce")
df["pagamento material"] = df.get("pagamento material", "não").astype(str).str.lower()
df["pagamento frete"] = df.get("pagamento frete", "não").astype(str).str.lower()
df["entregue"] = df.get("entregue", "não").astype(str).str.lower()

aba = st.sidebar.radio("Menu", [
    "📊 Visão Geral", "📋 Novo Pedido", "👥 Clientes", "💰 Financeiro", "📈 Relatórios", "⚙️ Configurações"])

if aba == "📊 Visão Geral":
    st.subheader("📊 Visão Geral do Sistema")

    total_entregas = len(df)
    entregues = df["entregue"].value_counts().get("sim", 0)
    pagos = df[(df["pagamento material"] == "sim") & (df["pagamento frete"] == "sim")].shape[0]
    lucro = df["preço de venda"].sum() - (df["custo do material"].sum() + df["custo do frete"].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🚚 Entregas Totais", total_entregas)
    with col2: st.metric("📦 Entregues", entregues)
    with col3: st.metric("💵 Pedidos Completos Pagos", pagos)
    with col4: st.metric("📈 Lucro Estimado", f"R$ {lucro:,.2f}")

elif aba == "📋 Novo Pedido":
    st.subheader("📋 Cadastrar Novo Pedido")
    with st.form("novo_pedido"):
        tipo_material = st.selectbox("Tipo de Material", [
            "Areia Média", "Areia Grossa", "Aterro Areia", "Aterro Barro", "Areia Lavada de Rio",
            "Arenoso", "Brita 0", "Brita 3/4", "Brita 3/8", "Brita 1", "Seixo", "Pedra"])
        tipo_caminhao = st.selectbox("Tipo de Caminhão", ["Toco", "Truck"])
        cliente = st.text_input("Cliente")
        condominio = st.text_input("Condomínio")
        lote = st.text_input("Lote")
        cacambeiro = st.text_input("Caçambeiro")
        custo_material = st.number_input("Custo do Material (R$)", min_value=0.0, step=0.01)
        custo_frete = st.number_input("Custo do Frete (R$)", min_value=0.0, step=0.01)
        preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.01)
        entregue = st.selectbox("Entregue?", ["sim", "não"])
        pagamento_material = st.selectbox("Pagamento Material", ["sim", "não"])
        pagamento_frete = st.selectbox("Pagamento Frete", ["sim", "não"])
        submit = st.form_submit_button("Salvar Pedido")
    if submit:
        nova_linha = [tipo_material, tipo_caminhao, cliente, condominio, lote, cacambeiro,
                      str(custo_material), str(custo_frete), str(preco_venda), entregue,
                      pagamento_material, pagamento_frete]
        sheet.append_row(nova_linha)
        st.success("✅ Pedido cadastrado com sucesso!")

elif aba == "👥 Clientes":
    st.subheader("👥 Clientes")
    clientes = df.groupby("cliente").agg({
        "cliente": "count",
        "preço de venda": "sum",
        "pagamento material": lambda x: (x == "não").sum(),
    }).rename(columns={"cliente": "Entregas", "preço de venda": "Faturamento", "pagamento material": "Devendo"})
    st.dataframe(clientes, use_container_width=True)
    with st.expander("➕ Cadastrar Novo Cliente"):
        novo_cliente = st.text_input("Nome do Cliente")
        if st.button("Salvar Cliente"):
            st.success("Cliente cadastrado. (Este campo ainda não persiste, apenas visual)")

elif aba == "💰 Financeiro":
    st.subheader("💰 Resumo Financeiro")
    total_vendas = df["preço de venda"].sum()
    total_custos = df["custo do material"].sum() + df["custo do frete"].sum()
    total_pago = df[(df["pagamento material"] == "sim") & (df["pagamento frete"] == "sim")]["preço de venda"].sum()
    caixa = total_pago
    st.metric("Total Vendido", f"R$ {total_vendas:,.2f}")
    st.metric("Total Recebido", f"R$ {caixa:,.2f}")
    st.metric("Lucro Bruto", f"R$ {total_vendas - total_custos:,.2f}")

elif aba == "📈 Relatórios":
    st.subheader("📈 Relatórios de Pedidos")
    filtro_entregue = st.selectbox("Filtrar por Entregue", ["todos", "sim", "não"])
    filtro_pagamento_material = st.selectbox("Filtrar por Pagamento Material", ["todos", "sim", "não"])
    filtro_pagamento_frete = st.selectbox("Filtrar por Pagamento Frete", ["todos", "sim", "não"])
    df_filtrado = df.copy()
    if filtro_entregue != "todos":
        df_filtrado = df_filtrado[df_filtrado["entregue"] == filtro_entregue]
    if filtro_pagamento_material != "todos":
        df_filtrado = df_filtrado[df_filtrado["pagamento material"] == filtro_pagamento_material]
    if filtro_pagamento_frete != "todos":
        df_filtrado = df_filtrado[df_filtrado["pagamento frete"] == filtro_pagamento_frete]
    st.dataframe(df_filtrado, use_container_width=True)

elif aba == "⚙️ Configurações":
    st.subheader("⚙️ Configurações do Sistema")
    st.warning("⚠️ Isso vai apagar todos os dados da planilha!")
    if st.button("🧹 ZERAR SISTEMA COMPLETO"):
        sheet.resize(rows=1)
        st.success("Todos os dados foram apagados com sucesso!")

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

# Adicionando campo de ID único (se não existir)
if "id_pedido" not in df.columns:
    import uuid
    ids = [str(uuid.uuid4()) for _ in range(len(df))]
    df.insert(0, "id_pedido", ids)
    # Atualiza o Google Sheets com o ID
    sheet.clear()
    sheet.append_row(["id_pedido"] + headers)
    for i, row in df.iterrows():
        sheet.append_row([row["id_pedido"]] + list(row[1:]))
    valores = sheet.get_all_values()
    headers, dados = valores[0], valores[1:]
    df = pd.DataFrame(dados, columns=headers)
    df.columns = [col.lower().strip() for col in df.columns]

# Conversões e validações
for col in ["custo do material", "custo do frete", "preço de venda"]:
    df[col] = pd.to_numeric(df.get(col, 0), errors="coerce")
for col in ["pagamento material", "pagamento frete", "entregue", "cliente pagou"]:
    if col not in df.columns:
        df[col] = ["não"] * len(df)
    df[col] = df[col].astype(str).str.lower()

# Função para encontrar a linha do pedido pelo ID
def encontrar_linha_por_id(sheet, id_pedido):
    valores = sheet.get_all_values()
    for idx, row in enumerate(valores[1:], start=2):  # começa do 2 por causa do cabeçalho
        if len(row) > 0 and row[0] == id_pedido:
            return idx
    return None

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

    for i, row in df[::-1].iterrows():
        id_pedido = row["id_pedido"]
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

            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            if col1.button("📦 Marcar como Entregue", key=f"ent_{id_pedido}"):
                linha = encontrar_linha_por_id(sheet, id_pedido)
                if linha:
                    sheet.update_cell(linha, headers.index("entregue")+1, "sim")
                    st.success("Entrega atualizada.")
                else:
                    st.error("Não foi possível encontrar esse pedido para atualizar.")
            if col2.button("🚛 Frete Pago", key=f"frete_{id_pedido}"):
                linha = encontrar_linha_por_id(sheet, id_pedido)
                if linha:
                    sheet.update_cell(linha, headers.index("pagamento frete")+1, "sim")
                    st.success("Pagamento do frete atualizado.")
                else:
                    st.error("Não foi possível encontrar esse pedido para atualizar.")
            if col3.button("📥 Material Pago", key=f"mat_{id_pedido}"):
                linha = encontrar_linha_por_id(sheet, id_pedido)
                if linha:
                    sheet.update_cell(linha, headers.index("pagamento material")+1, "sim")
                    st.success("Pagamento do material atualizado.")
                else:
                    st.error("Não foi possível encontrar esse pedido para atualizar.")
            if col4.button("💰 Cliente Pagou", key=f"cliente_{id_pedido}"):
                linha = encontrar_linha_por_id(sheet, id_pedido)
                if linha:
                    sheet.update_cell(linha, headers.index("cliente pagou")+1, "sim")
                    st.success("Cliente marcado como totalmente quitado.")
                else:
                    st.error("Não foi possível encontrar esse pedido para atualizar.")

# Execução da aba selecionada
if aba == "📊 Visão Geral":
    visao_geral()

# Aba: Novo Pedido
elif aba == "📋 Novo Pedido":
    st.subheader("📋 Cadastro de Novo Pedido")
    with st.form("novo_pedido"):
        tipo_material = st.selectbox("Tipo de Material", [
            "Areia Média Branca", "Areia Grossa", "Areia Grossa Amarela", "Arenoso", "Aterro",
            "Brita 0", "Brita 3/4", "Brita 3/8", "Brita 1", "Pedra", "Seixo"])
        tipo_caminhao = st.selectbox("Tipo de Caminhão", ["Toco", "Truck"])
        cliente = st.text_input("Nome do Cliente")
        condominio = st.text_input("Condomínio")
        lote = st.text_input("Lote")
        cacambeiro = st.text_input("Caçambeiro")
        custo_material = st.number_input("Custo do Material (R$)", min_value=0.0)
        custo_frete = st.number_input("Custo do Frete (R$)", min_value=0.0)
        preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0)
        entregue = st.selectbox("Entregue?", ["não", "sim"])
        pag_mat = st.selectbox("Pagamento Material?", ["não", "sim"])
        pag_frete = st.selectbox("Pagamento Frete?", ["não", "sim"])
        cliente_pagou = st.selectbox("Cliente Pagou?", ["não", "sim"])
        submitted = st.form_submit_button("Salvar Pedido")

        if submitted:
            import uuid
            id_pedido = str(uuid.uuid4())
            novo = [id_pedido, tipo_material, tipo_caminhao, cliente, condominio, lote, cacambeiro,
                str(custo_material), str(custo_frete), str(preco_venda), entregue,
                pag_mat, pag_frete, cliente_pagou]
            sheet.append_row(novo)
            st.success("Pedido salvo com sucesso!")

# Aba: Clientes
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

# Aba: Financeiro
elif aba == "💰 Financeiro":
    st.subheader("💰 Painel Financeiro")
    total_vendido = df["preço de venda"].sum()
    total_recebido = df.loc[(df["pagamento material"] == "sim") & (df["pagamento frete"] == "sim"), "preço de venda"].sum()
    lucro_bruto = total_vendido - (df["custo do material"].sum() + df["custo do frete"].sum())

    st.metric("Total Vendido", f"R$ {total_vendido:,.2f}")
    st.metric("Total Recebido", f"R$ {total_recebido:,.2f}")
    st.metric("Lucro Bruto", f"R$ {lucro_bruto:,.2f}")

# Aba: Relatórios
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

# Aba: Configurações
elif aba == "⚙️ Configurações":
    st.subheader("⚙️ Configurações do Sistema")
    if st.button("Zerar Planilha"):
        sheet.clear()
        sheet.append_row([col for col in df.columns])
        st.success("Todos os dados foram apagados. Apenas o cabeçalho foi mantido.")

    st.markdown("### Excluir Pedido Específico")
    if len(df) > 0:
        pedidos_opcoes = df.apply(lambda row: f"{row['cliente']} - Lote {row['lote']} - ID: {row['id_pedido']}", axis=1)
        pedido_selecionado = st.selectbox("Selecione o pedido para excluir", pedidos_opcoes)
        if st.button("Excluir este pedido"):
            id_excluir = pedido_selecionado.split("ID: ")[-1]
            linha = encontrar_linha_por_id(sheet, id_excluir)
            if linha:
                sheet.delete_row(linha)
                st.success("Pedido excluído com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Não foi possível encontrar o pedido para excluir.")
    else:
        st.info("Nenhum pedido cadastrado para excluir.")

import flet as ft
import sqlite3
from datetime import datetime, timedelta, date
import re
import os

# --- CONFIGURAÇÕES GLOBAIS ---
lista_locais = [
    "Consultório", 
    "Clínica", 
    "Espaço", 
    "Salão de Beleza", 
    "Barbearia", 
    "Escritório", 
    "Studio"
]

cores_segmento = {
    "Clínica": ft.Colors.BLUE_700,
    "Consultório": ft.Colors.TEAL_700,
    "Barbearia": ft.Colors.BROWN_800,
    "Salão de Beleza": ft.Colors.PINK_700,
    "Studio": ft.Colors.PURPLE_700,
    "Espaço": ft.Colors.GREEN_700,
    "Escritório": ft.Colors.BLUE_GREY_900
}

# --- BANCO DE DADOS MESTRE (Sistema SAS) ---
def init_db():
    conn = sqlite3.connect("sistema_mestre.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes_dev 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       nome_completo TEXT, nome_estabelecimento TEXT, segmento TEXT, profissao TEXT,
                       conselho TEXT, endereco TEXT, email TEXT, fone TEXT, cpf TEXT,
                       logomarca TEXT, pix TEXT, financeiro_ativo INTEGER DEFAULT 0,
                       servico_ativo INTEGER DEFAULT 1, end_rua TEXT, end_num TEXT, 
                       end_bairro TEXT, end_cidade TEXT, end_estado TEXT)''')
    try:
        cursor.execute("ALTER TABLE clientes_dev ADD COLUMN nome_estabelecimento TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE clientes_dev ADD COLUMN servico_ativo INTEGER DEFAULT 1")
    except: pass
    try:
        cursor.execute("ALTER TABLE clientes_dev ADD COLUMN end_rua TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE clientes_dev ADD COLUMN end_num TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE clientes_dev ADD COLUMN end_bairro TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE clientes_dev ADD COLUMN end_cidade TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE clientes_dev ADD COLUMN end_estado TEXT")
    except: pass
    conn.commit()
    conn.close()

# --- BANCO DE DADOS INDIVIDUAL (Isolamento por Cliente) ---
def init_db_cliente(id_cliente):
    db_name = f"cliente_{id_cliente}.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Adicionado campo ENDERECO na tabela pacientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       cpf TEXT, nome TEXT, fone TEXT, rua TEXT, num TEXT, 
                       bairro TEXT, cidade TEXT, estado TEXT, genero TEXT, 
                       profissao TEXT, nasc TEXT, idade INTEGER, notas TEXT, endereco TEXT)''')
    
    # Migração segura para adicionar campos se não existirem
    try:
        cursor.execute("ALTER TABLE pacientes ADD COLUMN endereco TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE pacientes ADD COLUMN nasc TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE pacientes ADD COLUMN idade INTEGER")
    except: pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS agenda_vagas 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, total_vagas INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS agendamentos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       id_paciente INTEGER, nome_cliente TEXT, fone_cliente TEXT,
                       data TEXT, hora TEXT, procedimento TEXT, valor REAL DEFAULT 0,
                       pago INTEGER DEFAULT 0, observacoes TEXT, created_at TEXT)''')
    try:
        cursor.execute("ALTER TABLE agendamentos ADD COLUMN valor REAL DEFAULT 0")
    except: pass
    try:
        cursor.execute("ALTER TABLE agendamentos ADD COLUMN observacoes TEXT")
    except: pass
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS financeiro 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, valor REAL, 
                       descricao TEXT, data TEXT)''')
    conn.commit()
    conn.close()

def main(page: ft.Page):
    init_db()
    page.title = "JeSystem SAS"
    page.window_width = 450
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_scroll = ft.ScrollMode.AUTO

    # --- FUNÇÕES DE MÁSCARA ---
    def aplicar_mascara_cpf(valor):
        v = re.sub(r'\D', '', str(valor))[:11]
        if len(v) > 9: return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
        if len(v) > 6: return f"{v[:3]}.{v[3:6]}.{v[6:]}"
        if len(v) > 3: return f"{v[:3]}.{v[3:]}"
        return v

    def aplicar_mascara_fone(valor):
        v = re.sub(r'\D', '', str(valor))[:11]
        if len(v) > 7: return f"({v[:2]}) {v[2:7]}-{v[7:]}"
        if len(v) > 2: return f"({v[:2]}) {v[2:]}"
        return v

    def formatar_cpf_evento(e):
        e.control.value = aplicar_mascara_cpf(e.control.value)
        page.update()

    def formatar_fone_evento(e):
        e.control.value = aplicar_mascara_fone(e.control.value)
        page.update()

    def formatar_data(e):
        v = re.sub(r'\D', '', e.control.value)
        if len(v) > 8: v = v[:8]
        if len(v) > 4: v = f"{v[:2]}/{v[2:4]}/{v[4:]}"
        elif len(v) > 2: v = f"{v[:2]}/{v[2:]}"
        e.control.value = v
        page.update()

    # --- TELA DE LOGIN ---
    def mostrar_inicio():
        page.controls.clear()
        user_prof = ft.TextField(label="Primeiro Nome", border_radius=10)
        pass_prof = ft.TextField(label="6 últimos dígitos do CPF", password=True, can_reveal_password=True, border_radius=10)
        
        def login_click(e):
            n_val = user_prof.value.strip()
            s_val = pass_prof.value.strip()
            
            if not n_val or not s_val:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha nome e senha!"), bgcolor="orange")
                page.snack_bar.open = True
                page.update()
                return

            conn = sqlite3.connect("sistema_mestre.db")
            cursor = conn.cursor()
            # Busca pelo nome
            cursor.execute("SELECT id, nome_completo, logomarca, segmento, financeiro_ativo, nome_estabelecimento, cpf, servico_ativo FROM clientes_dev WHERE nome_completo LIKE ?", (f"{n_val}%",))
            res = cursor.fetchone()
            conn.close()

            if res:
                cpf_banco = res[6] # CPF completo salvo no banco
                servico_ativo = res[7] if len(res) > 7 else 1
                
                # Verificar se serviço está ativo
                if not servico_ativo:
                    page.snack_bar = ft.SnackBar(ft.Text("Serviço bloqueado! Entre em contato com o suporte."), bgcolor="red")
                    page.snack_bar.open = True
                    page.update()
                    return
                
                # Verifica se a senha digitada corresponde ao final do CPF
                if cpf_banco and cpf_banco.endswith(s_val):
                    init_db_cliente(res[0])
                    abrir_app_profissional(res)
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Senha Incorreta!"), bgcolor="red")
                    page.snack_bar.open = True
                    page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Usuário não encontrado!"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        page.add(
            ft.Column([
                ft.Container(height=40),
                ft.Icon(ft.Icons.LOCK_PERSON, size=80, color=ft.Colors.BLUE_900),
                ft.Text("JeSystem SAS", size=32, weight="bold", color=ft.Colors.BLUE_900),
                ft.Divider(height=40),
                user_prof, pass_prof,
                ft.ElevatedButton("ACESSAR CONTA", on_click=login_click, width=400, height=50, bgcolor=ft.Colors.BLUE_900, color="white"),
                ft.TextButton("Painel Administrativo (DEV)", on_click=lambda _: mostrar_login_dev()),
                ft.Container(height=100),
                ft.Text("JeSystem TECNOLOGIAS - 2026", size=10, color=ft.Colors.GREY_400)
            ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # --- MENU PRINCIPAL DO CLIENTE ---
    def abrir_app_profissional(dados):
        # Desempacota os dados vindos do banco
        id_p, nome, logo, seg, fin_ativo, estabelecimento, *_ = dados
        
        page.controls.clear()
        cor_tema = cores_segmento.get(seg, ft.Colors.BLUE_600)
        db_cliente = f"cliente_{id_p}.db"

        # AppBar sem a seta de voltar automática (automatically_imply_leading=False)
        page.add(
            ft.AppBar(title=ft.Text(f"{estabelecimento}"), bgcolor=cor_tema, color="white", automatically_imply_leading=False),
            ft.Column([
                ft.Container(
                    content=ft.Image(src=logo, width=100) if logo and os.path.exists(logo) else ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80),
                    alignment=ft.Alignment(0, 0), padding=20
                ),
                ft.Text(f"Bem-vindo(a), {nome}", size=16, weight="bold"),
                ft.Divider(),
                ft.ElevatedButton("CADASTRAR", icon=ft.Icons.PERSON_ADD, width=400, bgcolor=ft.Colors.BLUE_700, color="white", height=55,
                                 on_click=lambda _: abrir_form_paciente(db_cliente, dados)),
                ft.ElevatedButton("AGENDAR", icon=ft.Icons.CALENDAR_MONTH, width=400, bgcolor=ft.Colors.PURPLE_700, color="white", height=55,
                                 on_click=lambda _: iniciar_agendamento(db_cliente, dados)),
                ft.ElevatedButton("VER AGENDA", icon=ft.Icons.CALENDAR_VIEW_WEEK, width=400, bgcolor=ft.Colors.TEAL_700, color="white", height=55,
                                 on_click=lambda _: visualizar_agenda(db_cliente, dados)),
                ft.ElevatedButton("FINANCEIRO", icon=ft.Icons.ACCOUNT_BALANCE_WALLET, width=400, visible=bool(fin_ativo), 
                                 bgcolor=ft.Colors.GREEN_800, color="white", height=55,
                                 on_click=lambda _: abrir_financeiro(db_cliente, dados)),
                ft.ElevatedButton("HISTÓRICO FINANCEIRO", icon=ft.Icons.HISTORY, width=400, visible=bool(fin_ativo),
                                 bgcolor=ft.Colors.INDIGO_700, color="white", height=55,
                                 on_click=lambda _: abrir_historico_financeiro(db_cliente, dados)),
                ft.Divider(),
                ft.ElevatedButton("SAIR DO SISTEMA", icon=ft.Icons.LOGOUT, on_click=lambda _: mostrar_inicio(), width=400, bgcolor=ft.Colors.RED_700, color="white"),
                ft.Container(height=20),
                ft.Text("JeSystem TECNOLOGIAS - 2026", size=10, color=ft.Colors.GREY_400)
            ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # --- FLUXO DE AGENDAMENTO ---
    def iniciar_agendamento(db_path, dados_p):
        page.controls.clear()
        campo_fone_busca = ft.TextField(label="Telefone do Cliente", on_change=formatar_fone_evento, 
                                        width=400, border_radius=10, hint_text="Digite o telefone completo")
        
        def verificar_telefone(e):
            """Verifica o telefone apenas quando o botão for clicado"""
            # Remove formatação para contar apenas dígitos
            f_l = re.sub(r'\D', '', campo_fone_busca.value)
            
            # Valida se tem 10 ou 11 dígitos
            if len(f_l) < 10:
                page.snack_bar = ft.SnackBar(ft.Text("Digite um telefone válido (10 ou 11 dígitos)!"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
            
            # Busca no banco de dados
            conn = sqlite3.connect(db_path)
            res = conn.execute("SELECT * FROM pacientes WHERE REPLACE(REPLACE(REPLACE(REPLACE(fone, '(', ''), ')', ''), '-', ''), ' ', '') = ?", (f_l,)).fetchone()
            conn.close()
            
            if res:
                # Cliente encontrado - vai direto para calendário
                page.snack_bar = ft.SnackBar(ft.Text(f"Cliente encontrado: {res[2]}"), bgcolor="green")
                page.snack_bar.open = True
                page.update()
                passar_para_calendario(db_path, dados_p, res)
            else:
                # Cliente não encontrado - abre cadastro
                page.snack_bar = ft.SnackBar(ft.Text("Cliente não encontrado. Abrindo cadastro..."), bgcolor="orange")
                page.snack_bar.open = True
                page.update()
                abrir_form_paciente(db_path, dados_p, fone_inicial=campo_fone_busca.value, fluxo_agendamento=True)

        page.add(
            ft.AppBar(title=ft.Text("Novo Agendamento"), bgcolor=ft.Colors.PURPLE_700, color="white",
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: abrir_app_profissional(dados_p))),
            ft.Column([
                ft.Container(height=30),
                ft.Icon(ft.Icons.PHONE, size=60, color=ft.Colors.PURPLE_700),
                ft.Text("Digite o telefone do cliente", size=18, weight="bold"),
                ft.Text("Clique em BUSCAR para verificar", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                campo_fone_busca,
                ft.Container(height=20),
                ft.ElevatedButton("BUSCAR E AGENDAR", icon=ft.Icons.SEARCH, 
                                on_click=verificar_telefone, 
                                width=400, bgcolor=ft.Colors.PURPLE_700, color="white", height=50),
                ft.Container(height=10),
                ft.TextButton("Voltar", on_click=lambda _: abrir_app_profissional(dados_p))
            ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment="center", spacing=15)
        )
        page.update()

    def passar_para_calendario(db_path, dados_p, paciente):
        # Usa DatePicker nativo do dispositivo, mas converte imediatamente para string
        data_selecionada = [None]  # Usa lista para poder modificar dentro da função
        
        def handle_date_change(e):
            try:
                # Pega o valor e converte IMEDIATAMENTE para string
                if e.control.value:
                    dt_value = e.control.value
                    
                    # Converte para string formatada DD/MM/YYYY
                    if isinstance(dt_value, datetime):
                        data_selecionada[0] = dt_value.strftime("%d/%m/%Y")
                    elif isinstance(dt_value, date):
                        data_selecionada[0] = dt_value.strftime("%d/%m/%Y")
                    else:
                        # Tenta converter string
                        try:
                            dt = datetime.strptime(str(dt_value).split()[0], "%Y-%m-%d")
                            data_selecionada[0] = dt.strftime("%d/%m/%Y")
                        except:
                            data_selecionada[0] = str(dt_value)
                    
                    # Remove o date picker do overlay IMEDIATAMENTE
                    try:
                        if date_picker in page.overlay:
                            page.overlay.remove(date_picker)
                            page.update()
                    except:
                        pass
                    
                    # Se conseguiu pegar a data, continua
                    if data_selecionada[0]:
                        selecionar_hora_procedimento(db_path, dados_p, paciente, data_selecionada[0])
            except Exception as ex:
                # Remove o date picker mesmo em caso de erro
                try:
                    if date_picker in page.overlay:
                        page.overlay.remove(date_picker)
                        page.update()
                except:
                    pass
                page.snack_bar = ft.SnackBar(ft.Text("Erro ao selecionar data. Tente novamente."), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        # Cria o DatePicker nativo
        date_picker = ft.DatePicker(
            on_change=handle_date_change,
            first_date=date.today(),
            last_date=date(2030, 12, 31),
            entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY
        )
        
        # Adiciona ao overlay
        page.overlay.append(date_picker)
        page.update()
        
        # Abre o DatePicker (método correto)
        date_picker.open = True
        page.update()

    def selecionar_hora_procedimento(db_path, dados_p, paciente, data_sel):
        page.controls.clear()
        
        # Campo de hora livre para digitação
        def formatar_hora_input(e):
            """Formata a hora enquanto digita (HH:MM)"""
            valor = re.sub(r'\D', '', e.control.value)
            if len(valor) <= 2:
                e.control.value = valor
            elif len(valor) <= 4:
                e.control.value = f"{valor[:2]}:{valor[2:]}"
            else:
                e.control.value = f"{valor[:2]}:{valor[2:4]}"
            page.update()
        
        campo_hora = ft.TextField(
            label="Horário (HH:MM)", 
            hint_text="Ex: 14:30 ou 09:00",
            width=400, 
            border_radius=10,
            on_change=formatar_hora_input,
            max_length=5
        )
        campo_proc = ft.TextField(label="Procedimento", width=400, border_radius=10)
        campo_valor = ft.TextField(label="Valor (R$)", keyboard_type="number", width=400, border_radius=10)
        campo_pago = ft.Checkbox(label="Procedimento já está pago?")
        campo_obs = ft.TextField(label="Observações do Agendamento", multiline=True, width=400, border_radius=10)

        def finalizar_agendamento(e):
            if not campo_hora.value or not campo_proc.value:
                page.snack_bar = ft.SnackBar(ft.Text("Horário e Procedimento são obrigatórios!"), bgcolor="red")
                page.snack_bar.open = True; page.update(); return
            
            # Valida formato da hora (HH:MM)
            hora_val = campo_hora.value.strip()
            if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', hora_val):
                page.snack_bar = ft.SnackBar(ft.Text("Horário inválido! Use o formato HH:MM (ex: 14:30)"), bgcolor="red")
                page.snack_bar.open = True; page.update(); return
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificação de Conflito
            conflito = cursor.execute("SELECT id FROM agendamentos WHERE data=? AND hora=?", (data_sel, campo_hora.value)).fetchone()
            if conflito:
                page.snack_bar = ft.SnackBar(ft.Text("HORÁRIO JÁ OCUPADO! Escolha outro."), bgcolor="red")
                page.snack_bar.open = True; page.update(); conn.close(); return
            
            # Converter valor para float
            try:
                valor_float = float(campo_valor.value.replace(",", ".")) if campo_valor.value else 0.0
            except:
                valor_float = 0.0
            
            # Salvar Agendamento
            cursor.execute("INSERT INTO agendamentos (id_paciente, nome_cliente, fone_cliente, data, hora, procedimento, valor, pago, observacoes, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (paciente[0], paciente[2], paciente[3], data_sel, campo_hora.value, campo_proc.value, valor_float, 1 if campo_pago.value else 0, campo_obs.value, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            
            page.snack_bar = ft.SnackBar(ft.Text("Agendamento Confirmado com Sucesso!"), bgcolor="green")
            page.snack_bar.open = True
            abrir_app_profissional(dados_p)

        page.add(
            ft.AppBar(title=ft.Text(f"Agenda: {data_sel}"), bgcolor=ft.Colors.PURPLE_700, color="white"),
            ft.Column([
                ft.Text(f"Cliente: {paciente[2]}", weight="bold", size=18),
                campo_hora, 
                campo_proc, 
                campo_valor, 
                campo_pago, 
                campo_obs,
                ft.ElevatedButton("CONFIRMAR AGENDAMENTO", on_click=finalizar_agendamento, width=400, bgcolor="green", color="white", height=50),
                ft.TextButton("Cancelar", on_click=lambda _: abrir_app_profissional(dados_p))
            ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment="center", spacing=15)
        )
        page.update()

    # --- CADASTRO DE CLIENTE/PACIENTE (PROFISSIONAL) ---
    def abrir_form_paciente(db_path, dados_p, fone_inicial="", fluxo_agendamento=False):
        page.controls.clear()
        paciente_id = [None]
        
        # Campos na ordem solicitada: fone primeiro, depois CPF
        c_fone = ft.TextField(label="Telefone *", border_radius=10, value=fone_inicial, on_change=formatar_fone_evento)
        c_cpf = ft.TextField(label="CPF", border_radius=10, on_change=formatar_cpf_evento)
        c_nome = ft.TextField(label="Nome Completo *", border_radius=10)
        c_nasc = ft.TextField(label="Data de Nascimento (DD/MM/AAAA)", border_radius=10, on_change=formatar_data, width=400)
        texto_idade = ft.Text("Idade: -- anos", weight="bold", size=14, color=ft.Colors.BLUE_700)
        # Campos de endereço separados
        c_rua = ft.TextField(label="Rua", border_radius=10)
        c_num = ft.TextField(label="Número", border_radius=10)
        c_bairro = ft.TextField(label="Bairro", border_radius=10)
        c_cidade = ft.TextField(label="Cidade", border_radius=10)
        c_estado = ft.TextField(label="Estado (UF)", border_radius=10, max_length=2, hint_text="Ex: SP, RJ")
        c_anot = ft.TextField(label="Anotações", border_radius=10, multiline=True, min_lines=3)
        
        btn_exc = ft.ElevatedButton("EXCLUIR CADASTRO", icon=ft.Icons.DELETE, bgcolor="red", color="white", width=400, visible=False)
        
        def calcular_idade(e):
            formatar_data(e)
            try:
                if len(c_nasc.value) == 10:
                    hoje = datetime.now()
                    nasc = datetime.strptime(c_nasc.value, "%d/%m/%Y")
                    idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
                    texto_idade.value = f"Idade: {idade} anos"
                    page.update()
            except:
                pass
        
        c_nasc.on_change = calcular_idade

        def carregar_dados(row):
            # Preenche os campos se encontrar
            paciente_id[0] = row[0]
            c_cpf.value = aplicar_mascara_cpf(row[1]) if row[1] else ""
            c_nome.value = row[2] if row[2] else ""
            c_fone.value = aplicar_mascara_fone(row[3]) if row[3] else ""
            # Carregar endereço separado
            c_rua.value = row[4] if len(row) > 4 and row[4] else ""
            c_num.value = row[5] if len(row) > 5 and row[5] else ""
            c_bairro.value = row[6] if len(row) > 6 and row[6] else ""
            c_cidade.value = row[7] if len(row) > 7 and row[7] else ""
            c_estado.value = row[8] if len(row) > 8 and row[8] else ""
            c_anot.value = row[13] if len(row) > 13 and row[13] else ""
            if len(row) > 12 and row[12]:  # Data de nascimento
                c_nasc.value = row[12]
                if row[12]:
                    try:
                        hoje = datetime.now()
                        nasc = datetime.strptime(row[12], "%d/%m/%Y")
                        idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
                        texto_idade.value = f"Idade: {idade} anos"
                    except:
                        pass
            btn_exc.visible = True
            page.update()

        def verificar_existencia(e):
            val_l = re.sub(r'\D', '', e.control.value)
            
            # Verifica CPF quando completa 11 dígitos
            if e.control == c_cpf and len(val_l) == 11:
                conn = sqlite3.connect(db_path)
                res = conn.execute("SELECT * FROM pacientes WHERE REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '') = ?", (val_l,)).fetchone()
                conn.close()
                if res: 
                    page.snack_bar = ft.SnackBar(ft.Text("CPF já cadastrado! Carregando dados..."), bgcolor="green")
                    page.snack_bar.open = True
                    page.update()
                    carregar_dados(res)
            
            # Verifica Fone quando completa 10 ou 11 dígitos
            elif e.control == c_fone and len(val_l) >= 10:
                conn = sqlite3.connect(db_path)
                res = conn.execute("SELECT * FROM pacientes WHERE REPLACE(REPLACE(REPLACE(REPLACE(fone, '(', ''), ')', ''), '-', ''), ' ', '') = ?", (val_l,)).fetchone()
                conn.close()
                if res: 
                    page.snack_bar = ft.SnackBar(ft.Text("Telefone já cadastrado! Carregando dados..."), bgcolor="green")
                    page.snack_bar.open = True
                    page.update()
                    carregar_dados(res)

        # Vincula verificação automática
        def on_cpf_change(e):
            formatar_cpf_evento(e)
            verificar_existencia(e)
        
        def on_fone_change(e):
            formatar_fone_evento(e)
            verificar_existencia(e)
        
        c_cpf.on_change = on_cpf_change
        c_fone.on_change = on_fone_change

        def salvar(e):
            # Validação: fone e nome são obrigatórios
            fone_l = re.sub(r'\D', '', c_fone.value)
            if len(fone_l) < 10:
                page.snack_bar = ft.SnackBar(ft.Text("Telefone é obrigatório!"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
            
            if not c_nome.value or not c_nome.value.strip():
                page.snack_bar = ft.SnackBar(ft.Text("Nome é obrigatório!"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
            
            # Calcular idade se tiver data de nascimento
            idade_calc = 0
            if c_nasc.value and len(c_nasc.value) == 10:
                try:
                    hoje = datetime.now()
                    nasc = datetime.strptime(c_nasc.value, "%d/%m/%Y")
                    idade_calc = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
                except:
                    pass
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cpf_l = re.sub(r'\D', '', c_cpf.value) if c_cpf.value else ""
            
            if paciente_id[0]:
                cursor.execute("UPDATE pacientes SET cpf=?, nome=?, fone=?, rua=?, num=?, bairro=?, cidade=?, estado=?, nasc=?, idade=?, notas=? WHERE id=?", 
                               (cpf_l, c_nome.value, c_fone.value, c_rua.value, c_num.value, c_bairro.value, c_cidade.value, c_estado.value, c_nasc.value, idade_calc, c_anot.value, paciente_id[0]))
                p_id = paciente_id[0]
                msg = "Cadastro atualizado com sucesso!"
            else:
                cursor.execute("INSERT INTO pacientes (cpf, nome, fone, rua, num, bairro, cidade, estado, nasc, idade, notas) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                               (cpf_l, c_nome.value, c_fone.value, c_rua.value, c_num.value, c_bairro.value, c_cidade.value, c_estado.value, c_nasc.value, idade_calc, c_anot.value))
                p_id = cursor.lastrowid
                msg = "Cadastro realizado com sucesso!"
            
            conn.commit()
            conn.close()
            
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            page.snack_bar.open = True
            page.update()
            
            # Se veio do fluxo de agendamento, vai pro calendário
            if fluxo_agendamento:
                conn = sqlite3.connect(db_path)
                novo_pac = conn.execute("SELECT * FROM pacientes WHERE id=?", (p_id,)).fetchone()
                conn.close()
                passar_para_calendario(db_path, dados_p, novo_pac)
            else:
                abrir_app_profissional(dados_p)

        def excluir(e):
            if paciente_id[0]:
                conn = sqlite3.connect(db_path)
                conn.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id[0],))
                conn.commit()
                conn.close()
                abrir_app_profissional(dados_p)

        btn_exc.on_click = excluir

        page.add(
            ft.AppBar(title=ft.Text("Cadastro de Cliente"), bgcolor=ft.Colors.BLUE_700, color="white", 
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: abrir_app_profissional(dados_p))),
            ft.Column([
                ft.Container(height=10),
                ft.Text("Identificação", weight="bold", size=16),
                c_fone, c_cpf,
                ft.Divider(),
                    ft.Text("Dados Pessoais", weight="bold", size=16),
                    c_nome,
                    ft.Column([
                        c_nasc,
                        texto_idade
                    ], horizontal_alignment="center", spacing=5),
                    ft.Divider(),
                    ft.Text("Endereço", weight="bold", size=16),
                    c_rua, c_num, c_bairro, c_cidade, c_estado,
                    ft.Divider(),
                    ft.Text("Anotações", weight="bold", size=16),
                    c_anot,
                    ft.ElevatedButton("SALVAR CADASTRO", icon=ft.Icons.SAVE, on_click=salvar, 
                                width=400, bgcolor="green", color="white", height=50),
                    btn_exc, 
                    ft.TextButton("Voltar", on_click=lambda _: abrir_app_profissional(dados_p))
            ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=15, horizontal_alignment="center")
        )
        page.update()

    def visualizar_agenda(db_path, dados_p):
        page.controls.clear()
        conn = sqlite3.connect(db_path)
        ags = conn.execute("SELECT * FROM agendamentos ORDER BY data, hora").fetchall()
        conn.close()
        
        # Agrupar por data
        agendamentos_por_data = {}
        dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        
        for ag in ags:
            data = ag[4]  # ag[4] = data
            if data not in agendamentos_por_data:
                agendamentos_por_data[data] = []
            agendamentos_por_data[data].append(ag)
        
        lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        if not ags:
            lista.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=60, color=ft.Colors.GREY_400),
                        ft.Text("Nenhum agendamento encontrado", size=16, color=ft.Colors.GREY_600)
                    ], horizontal_alignment="center", spacing=10),
                    padding=40
                )
            )
        else:
            for data in sorted(agendamentos_por_data.keys()):
                # Converter data para dia da semana
                try:
                    dt = datetime.strptime(data, "%d/%m/%Y")
                    dia_semana = dias_semana[dt.weekday()]
                except:
                    dia_semana = "Data"
                
                # Barra do dia (destaque)
                cor_barra = ft.Colors.BLUE_700
                if dia_semana in ["Sábado", "Domingo"]:
                    cor_barra = ft.Colors.ORANGE_700
                
                barra_dia = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, color="white", size=24),
                        ft.Column([
                            ft.Text(f"{dia_semana}", size=16, weight="bold", color="white"),
                            ft.Text(f"{data}", size=14, color="white")
                        ], spacing=2, expand=True),
                        ft.Container(
                            content=ft.Text(f"{len(agendamentos_por_data[data])} agendamento(s)", 
                                          size=12, weight="bold", color="white"),
                            bgcolor=ft.Colors.BLACK26,
                            padding=8,
                            border_radius=5
                        )
                    ], spacing=10),
                    bgcolor=cor_barra,
                    padding=15,
                    border_radius=10,
                    width=400
                )
                lista.controls.append(barra_dia)
                
                # Lista de agendamentos do dia
                for ag in agendamentos_por_data[data]:
                    # ag = (id, id_paciente, nome_cliente, fone_cliente, data, hora, procedimento, valor, pago, observacoes, created_at)
                    ag_id = ag[0]
                    id_pac = ag[1]
                    nome = ag[2]
                    fone = ag[3]
                    data_ag = ag[4]
                    hora = ag[5]
                    procedimento = ag[6]
                    valor = ag[7] if len(ag) > 7 else 0
                    pago = ag[8] if len(ag) > 8 else 0
                    observacoes = ag[9] if len(ag) > 9 else ""
                    
                    status_cor = ft.Colors.GREEN_600 if pago else ft.Colors.ORANGE_600
                    status_texto = "✓ PAGO" if pago else "PENDENTE"
                    try:
                        valor_formatado = f"R$ {float(valor):.2f}".replace(".", ",") if valor else "R$ 0,00"
                    except:
                        valor_formatado = "R$ 0,00"
                    
                    card_agendamento = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.ACCESS_TIME, color=ft.Colors.BLUE_700, size=24),
                                    ft.Text(f"{hora}", size=20, weight="bold")
                                ], spacing=10),
                                ft.Divider(height=10),
                                ft.Text(f"{nome}", size=16, weight="bold"),
                                ft.Text(f"{procedimento}", size=14),
                                ft.Text(f"Tel: {fone}", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"Valor: {valor_formatado}", size=12, weight="bold"),
                                ft.Text(f"Obs: {observacoes}", size=11, color=ft.Colors.GREY_600, italic=True) if observacoes else ft.Container(height=0),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text(status_texto, size=12, weight="bold", color="white"),
                                        bgcolor=status_cor,
                                        padding=8,
                                        border_radius=5
                                    ),
                                    ft.ElevatedButton("Editar", icon=ft.Icons.EDIT, 
                                                     on_click=lambda e, ag_id=ag_id: editar_agendamento(db_path, dados_p, ag_id),
                                                     bgcolor=ft.Colors.BLUE_600, color="white", height=35),
                                    ft.ElevatedButton("Excluir", icon=ft.Icons.DELETE, 
                                                     on_click=lambda e, ag_id=ag_id: excluir_agendamento(db_path, dados_p, ag_id),
                                                     bgcolor=ft.Colors.RED_600, color="white", height=35)
                                ], spacing=5)
                            ], spacing=8),
                            padding=15
                        ),
                        margin=5,
                        width=400
                    )
                    lista.controls.append(card_agendamento)
                
                lista.controls.append(ft.Divider(height=20))
            
        page.add(
            ft.AppBar(title=ft.Text("Agenda Completa"), bgcolor=ft.Colors.BLUE_700, color="white", 
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: abrir_app_profissional(dados_p))),
            ft.Container(content=lista, padding=10, expand=True),
            ft.ElevatedButton("VOLTAR", icon=ft.Icons.ARROW_BACK, on_click=lambda _: abrir_app_profissional(dados_p), 
                            width=400, bgcolor=ft.Colors.BLUE_700, color="white")
        )
        page.update()
    
    def editar_agendamento(db_path, dados_p, ag_id):
        """Edita um agendamento existente"""
        conn = sqlite3.connect(db_path)
        ag = conn.execute("SELECT * FROM agendamentos WHERE id=?", (ag_id,)).fetchone()
        conn.close()
        
        if not ag:
            page.snack_bar = ft.SnackBar(ft.Text("Agendamento não encontrado!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        
        # Buscar paciente
        conn = sqlite3.connect(db_path)
        paciente = conn.execute("SELECT * FROM pacientes WHERE id=?", (ag[1],)).fetchone()
        conn.close()
        
        if not paciente:
            page.snack_bar = ft.SnackBar(ft.Text("Cliente não encontrado!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        
        # Abrir tela de edição (reutiliza selecionar_hora_procedimento mas com dados preenchidos)
        page.controls.clear()
        data_sel = ag[4]
        # Campo de hora livre para digitação
        def formatar_hora_edit(e):
            """Formata a hora enquanto digita (HH:MM)"""
            valor = re.sub(r'\D', '', e.control.value)
            if len(valor) <= 2:
                e.control.value = valor
            elif len(valor) <= 4:
                e.control.value = f"{valor[:2]}:{valor[2:]}"
            else:
                e.control.value = f"{valor[:2]}:{valor[2:4]}"
            page.update()
        
        campo_hora = ft.TextField(label="Horário (HH:MM)", 
                                hint_text="Ex: 14:30",
                                width=400, 
                                border_radius=10,
                                on_change=formatar_hora_edit,
                                max_length=5,
                                value=ag[5] if ag[5] else "")
        campo_proc = ft.TextField(label="Procedimento", width=400, border_radius=10, value=ag[6])
        campo_valor = ft.TextField(label="Valor (R$)", keyboard_type="number", width=400, border_radius=10, 
                                  value=str(ag[7]) if ag[7] else "")
        campo_pago = ft.Checkbox(label="Procedimento já está pago?", value=bool(ag[8]))
        campo_obs = ft.TextField(label="Observações do Agendamento", multiline=True, width=400, border_radius=10,
                                value=ag[9] if len(ag) > 9 and ag[9] else "")

        def salvar_edicao(e):
            if not campo_hora.value or not campo_proc.value:
                page.snack_bar = ft.SnackBar(ft.Text("Horário e Procedimento são obrigatórios!"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
            
            # Valida formato da hora (HH:MM)
            hora_val = campo_hora.value.strip()
            if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', hora_val):
                page.snack_bar = ft.SnackBar(ft.Text("Horário inválido! Use o formato HH:MM (ex: 14:30)"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar conflito (exceto o próprio agendamento)
            conflito = cursor.execute("SELECT id FROM agendamentos WHERE data=? AND hora=? AND id!=?", 
                                     (data_sel, campo_hora.value, ag_id)).fetchone()
            if conflito:
                page.snack_bar = ft.SnackBar(ft.Text("HORÁRIO JÁ OCUPADO! Escolha outro."), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                conn.close()
                return
            
            # Converter valor
            try:
                valor_float = float(campo_valor.value.replace(",", ".")) if campo_valor.value else 0.0
            except:
                valor_float = 0.0
            
            # Atualizar agendamento
            cursor.execute("UPDATE agendamentos SET hora=?, procedimento=?, valor=?, pago=?, observacoes=? WHERE id=?",
                          (campo_hora.value, campo_proc.value, valor_float, 1 if campo_pago.value else 0, campo_obs.value, ag_id))
            conn.commit()
            conn.close()
            
            page.snack_bar = ft.SnackBar(ft.Text("Agendamento atualizado com sucesso!"), bgcolor="green")
            page.snack_bar.open = True
            page.update()
            visualizar_agenda(db_path, dados_p)

        page.add(
            ft.AppBar(title=ft.Text(f"Editar Agendamento - {data_sel}"), bgcolor=ft.Colors.BLUE_700, color="white",
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: visualizar_agenda(db_path, dados_p))),
            ft.Column([
                ft.Text(f"Cliente: {paciente[2]}", weight="bold", size=18),
                campo_hora, campo_proc, campo_valor, campo_pago, campo_obs,
                ft.ElevatedButton("SALVAR ALTERAÇÕES", icon=ft.Icons.SAVE, on_click=salvar_edicao, 
                                width=400, bgcolor="green", color="white", height=50),
                ft.TextButton("Cancelar", on_click=lambda _: visualizar_agenda(db_path, dados_p))
            ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment="center", spacing=15)
        )
        page.update()
    
    def excluir_agendamento(db_path, dados_p, ag_id):
        """Exclui um agendamento"""
        def confirmar_exclusao(e):
            conn = sqlite3.connect(db_path)
            conn.execute("DELETE FROM agendamentos WHERE id=?", (ag_id,))
            conn.commit()
            conn.close()
            
            dialog.open = False
            page.update()
            page.snack_bar = ft.SnackBar(ft.Text("Agendamento excluído com sucesso!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            visualizar_agenda(db_path, dados_p)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text("Tem certeza que deseja excluir este agendamento?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dialog, 'open', False) or page.update()),
                ft.TextButton("Excluir", on_click=confirmar_exclusao, 
                            style=ft.ButtonStyle(color=ft.Colors.RED))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def abrir_financeiro(db_path, dados_p):
        """Módulo Financeiro (placeholder)"""
        page.controls.clear()
        page.add(
            ft.AppBar(title=ft.Text("Sistema de Caixa"), bgcolor=ft.Colors.GREEN_800, color="white",
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: abrir_app_profissional(dados_p))),
            ft.Column([
                ft.Container(height=50),
                ft.Icon(ft.Icons.CONSTRUCTION, size=80, color=ft.Colors.GREY_400),
                ft.Text("Módulo em Desenvolvimento", size=20, weight="bold"),
                ft.Text("Esta funcionalidade será implementada em breve.", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=30),
                ft.ElevatedButton("VOLTAR", on_click=lambda _: abrir_app_profissional(dados_p), width=400)
            ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment="center", spacing=20)
        )
        page.update()
    
    def abrir_historico_financeiro(db_path, dados_p):
        """Histórico Financeiro (placeholder)"""
        page.controls.clear()
        page.add(
            ft.AppBar(title=ft.Text("Histórico Financeiro"), bgcolor=ft.Colors.INDIGO_700, color="white",
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: abrir_app_profissional(dados_p))),
            ft.Column([
                ft.Container(height=50),
                ft.Icon(ft.Icons.CONSTRUCTION, size=80, color=ft.Colors.GREY_400),
                ft.Text("Módulo em Desenvolvimento", size=20, weight="bold"),
                ft.Text("Esta funcionalidade será implementada em breve.", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=30),
                ft.ElevatedButton("VOLTAR", on_click=lambda _: abrir_app_profissional(dados_p), width=400)
            ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment="center", spacing=20)
        )
        page.update()

    # --- ÁREA DO DESENVOLVEDOR (PAINEL MESTRE) ---
    def mostrar_login_dev():
        page.controls.clear()
        u_dev = ft.TextField(label="Usuário Admin", value="admin", border_radius=10)
        s_dev = ft.TextField(label="Senha SGS", password=True, border_radius=10)
        
        def check(e):
            if u_dev.value == "admin" and s_dev.value == "jere9261": 
                abrir_painel_dev()
            else: 
                page.snack_bar = ft.SnackBar(ft.Text("Credenciais Incorretas!"), bgcolor="red")
                page.snack_bar.open = True; page.update()
        
        page.add(
            ft.AppBar(title=ft.Text("Acesso Restrito"), bgcolor="black", color="white", leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: mostrar_inicio())),
            ft.Column([
                ft.Text("Painel de Controle SAS", size=24, weight="bold"), 
                u_dev, s_dev, 
                ft.ElevatedButton("ENTRAR", on_click=check, width=400, bgcolor="black", color="white")
            ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment="center", spacing=20)
        )
        page.update()

    def abrir_painel_dev():
        page.controls.clear()
        conn = sqlite3.connect("sistema_mestre.db")
        clis = conn.execute("SELECT id, nome_completo, nome_estabelecimento, segmento, servico_ativo FROM clientes_dev").fetchall()
        conn.close()
        
        lista = ft.Column(scroll="auto", expand=True)
        for c in clis:
            c_id, nome, estabelecimento, segmento, servico_ativo = c
            status_ativo = servico_ativo if servico_ativo is not None else 1
            
            # Cor e ícone baseado no status
            cor_status = ft.Colors.GREEN_700 if status_ativo else ft.Colors.RED_700
            texto_status = "ATIVO" if status_ativo else "BLOQUEADO"
            icon_status = ft.Icons.CHECK_CIRCLE if status_ativo else ft.Icons.CANCEL
            
            def toggle_servico(cid, atual):
                conn = sqlite3.connect("sistema_mestre.db")
                novo_status = 0 if atual else 1
                conn.execute("UPDATE clientes_dev SET servico_ativo=? WHERE id=?", (novo_status, cid))
                conn.commit()
                conn.close()
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Serviço {'ATIVADO' if novo_status else 'BLOQUEADO'} com sucesso!"), 
                    bgcolor="green" if novo_status else "orange"
                )
                page.snack_bar.open = True
                page.update()
                abrir_painel_dev()
            
            lista.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.BLUE_700, size=30), 
                                ft.Column([
                                    ft.Text(f"{estabelecimento}", weight="bold", size=16), 
                                    ft.Text(f"{nome} - {segmento}", size=12, color=ft.Colors.GREY_600)
                                ], expand=True, spacing=2)
                            ], spacing=10),
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(icon_status, color="white", size=20),
                                        ft.Text(texto_status, color="white", weight="bold", size=12)
                                    ], spacing=5),
                                    bgcolor=cor_status,
                                    padding=8,
                                    border_radius=5
                                ),
                                ft.ElevatedButton("Editar", icon=ft.Icons.EDIT, 
                                                 on_click=lambda e, cid=c_id: abrir_novo_profissional(cid),
                                                 bgcolor=ft.Colors.BLUE_600, color="white", height=35),
                                ft.ElevatedButton("Ativar/Bloquear", 
                                                 icon=ft.Icons.POWER_SETTINGS_NEW if status_ativo else ft.Icons.LOCK_OPEN,
                                                 on_click=lambda e, cid=c_id, atual=status_ativo: toggle_servico(cid, atual),
                                                 bgcolor=cor_status, color="white", height=35),
                                ft.IconButton(ft.Icons.DELETE, icon_color="red", 
                                             on_click=lambda e, id=c_id: excluir_cliente(id))
                            ], spacing=5)
                        ], spacing=10)
                    ),
                    margin=5
                )
            )
            
        page.add(
            ft.AppBar(title=ft.Text("Gestão de Clientes"), bgcolor="black", color="white", 
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: mostrar_login_dev())),
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("JeSystem TECNOLOGIAS", size=18, weight="bold", color=ft.Colors.BLUE_700),
                        ft.Text("Sistema de Gestão SaaS", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment="center", spacing=5),
                    padding=15
                ),
                ft.ElevatedButton("NOVO CLIENTE", icon=ft.Icons.PERSON_ADD, on_click=lambda _: abrir_novo_profissional(), 
                                width=400, bgcolor="blue", color="white", height=50),
                ft.Divider(),
                lista, 
                ft.TextButton("Sair", on_click=lambda _: mostrar_inicio())
            ], scroll=ft.ScrollMode.AUTO, expand=True)
        )
        page.update()

    def abrir_novo_profissional(c_id=None):
        page.controls.clear()
        # Campos completos na ordem solicitada
        n = ft.TextField(label="Nome do Profissional *", border_radius=10)
        cp = ft.TextField(label="CPF (6 últimos dígitos serão a senha) *", on_change=formatar_cpf_evento, border_radius=10)
        est = ft.TextField(label="Nome do Negócio *", border_radius=10)
        # Campos de endereço separados
        end_rua = ft.TextField(label="Rua", border_radius=10)
        end_num = ft.TextField(label="Número", border_radius=10)
        end_bairro = ft.TextField(label="Bairro", border_radius=10)
        end_cidade = ft.TextField(label="Cidade", border_radius=10)
        end_estado = ft.TextField(label="Estado (UF)", border_radius=10, max_length=2, hint_text="Ex: SP, RJ")
        seg = ft.Dropdown(label="Segmento *", options=[ft.dropdown.Option(x) for x in lista_locais], border_radius=10)
        prof = ft.TextField(label="Profissão do Cliente", border_radius=10)
        px = ft.TextField(label="Chave PIX", border_radius=10, hint_text="Para uso no módulo financeiro")
        logo = ft.TextField(label="Caminho da Logomarca", border_radius=10, hint_text="Caminho completo do arquivo de imagem")
        fin = ft.Checkbox(label="Habilitar Módulo Financeiro")
        serv_ativo = ft.Checkbox(label="Serviço Ativo (SaaS)", value=True)
        
        # Se for edição, carregar dados
        if c_id:
            conn = sqlite3.connect("sistema_mestre.db")
            d = conn.execute("SELECT nome_completo, cpf, nome_estabelecimento, endereco, segmento, profissao, pix, logomarca, financeiro_ativo, servico_ativo, end_rua, end_num, end_bairro, end_cidade, end_estado FROM clientes_dev WHERE id=?", (c_id,)).fetchone()
            conn.close()
            if d: 
                n.value = d[0]
                cp.value = aplicar_mascara_cpf(d[1]) if d[1] else ""
                est.value = d[2]
                # Carregar endereço separado ou do campo antigo
                if len(d) > 10 and d[10]:  # end_rua
                    end_rua.value = d[10]
                    end_num.value = d[11] if len(d) > 11 and d[11] else ""
                    end_bairro.value = d[12] if len(d) > 12 and d[12] else ""
                    end_cidade.value = d[13] if len(d) > 13 and d[13] else ""
                    end_estado.value = d[14] if len(d) > 14 and d[14] else ""
                elif d[3]:  # endereco antigo
                    # Tentar separar o endereço antigo (lógica simples)
                    end_rua.value = d[3] if d[3] else ""
                seg.value = d[4]
                prof.value = d[5] if d[5] else ""
                px.value = d[6] if d[6] else ""
                logo.value = d[7] if d[7] else ""
                fin.value = bool(d[8]) if len(d) > 8 else False
                serv_ativo.value = bool(d[9]) if len(d) > 9 else True

        def cadastrar(e):
            # Validações
            if not n.value or not cp.value or not est.value or not seg.value:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha os campos obrigatórios (*)!"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
            
            cp_l = re.sub(r'\D', '', cp.value)
            if len(cp_l) < 11:
                page.snack_bar = ft.SnackBar(ft.Text("CPF inválido! Deve ter 11 dígitos."), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
            
            conn = sqlite3.connect("sistema_mestre.db")
            cursor = conn.cursor()
            
            # Montar endereço completo para compatibilidade
            end_completo = f"{end_rua.value or ''}, {end_num.value or ''} - {end_bairro.value or ''}, {end_cidade.value or ''} - {end_estado.value or ''}".strip(", -")
            
            if c_id: # UPDATE
                cursor.execute('''UPDATE clientes_dev SET nome_completo=?, cpf=?, nome_estabelecimento=?, endereco=?, segmento=?, profissao=?, pix=?, logomarca=?, financeiro_ativo=?, servico_ativo=?, end_rua=?, end_num=?, end_bairro=?, end_cidade=?, end_estado=? WHERE id=?''', 
                               (n.value, cp_l, est.value, end_completo, seg.value, prof.value, px.value, logo.value, 1 if fin.value else 0, 1 if serv_ativo.value else 0, end_rua.value, end_num.value, end_bairro.value, end_cidade.value, end_estado.value, c_id))
                msg = "Cliente atualizado com sucesso!"
            else: # INSERT
                cursor.execute('''INSERT INTO clientes_dev (nome_completo, cpf, nome_estabelecimento, endereco, segmento, profissao, pix, logomarca, financeiro_ativo, servico_ativo, end_rua, end_num, end_bairro, end_cidade, end_estado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                               (n.value, cp_l, est.value, end_completo, seg.value, prof.value, px.value, logo.value, 1 if fin.value else 0, 1 if serv_ativo.value else 0, end_rua.value, end_num.value, end_bairro.value, end_cidade.value, end_estado.value))
                # Cria o banco do cliente logo após cadastrar
                new_id = cursor.lastrowid
                init_db_cliente(new_id)
                msg = "Cliente cadastrado com sucesso! Banco de dados criado."
                
            conn.commit()
            conn.close()
            
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            page.snack_bar.open = True
            page.update()
            abrir_painel_dev()

        page.add(
            ft.AppBar(title=ft.Text("Cadastro de Cliente" if not c_id else "Editar Cliente"), bgcolor="black", color="white", 
                     leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: abrir_painel_dev())),
            ft.Column([
                ft.Container(height=10),
                ft.Text("Dados do Profissional", weight="bold", size=16),
                n, cp,
                ft.Divider(),
                ft.Text("Dados do Negócio", weight="bold", size=16),
                est, 
                ft.Text("Endereço do Negócio", weight="bold", size=14),
                end_rua, end_num, end_bairro, end_cidade, end_estado,
                seg, prof,
                ft.Divider(),
                ft.Text("Configurações", weight="bold", size=16),
                px, logo,
                ft.Divider(),
                fin, serv_ativo,
                ft.ElevatedButton("SALVAR", icon=ft.Icons.SAVE, on_click=cadastrar, width=400, bgcolor="green", color="white", height=50),
                ft.TextButton("Cancelar", on_click=lambda _: abrir_painel_dev())
            ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=15, horizontal_alignment="center")
        )
        page.update()

    def excluir_cliente(id_c):
        conn = sqlite3.connect("sistema_mestre.db")
        conn.execute("DELETE FROM clientes_dev WHERE id=?", (id_c,))
        conn.commit(); conn.close()
        if os.path.exists(f"cliente_{id_c}.db"): os.remove(f"cliente_{id_c}.db")
        abrir_painel_dev()

    mostrar_inicio()



if __name__ == "__main__":
    # Configuração para rodar na Nuvem (Render/Railway) ou Local
    port = int(os.environ.get("PORT", 8550))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")
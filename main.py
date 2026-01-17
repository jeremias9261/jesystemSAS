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
    
    # Migrações para garantir colunas novas
    colunas_novas = ["nome_estabelecimento", "servico_ativo", "end_rua", "end_num", "end_bairro", "end_cidade", "end_estado"]
    for col in colunas_novas:
        try:
            cursor.execute(f"ALTER TABLE clientes_dev ADD COLUMN {col} TEXT")
        except: pass
        
    conn.commit()
    conn.close()

# --- BANCO DE DADOS INDIVIDUAL (Isolamento por Cliente) ---
def init_db_cliente(id_cliente):
    db_name = f"cliente_{id_cliente}.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       cpf TEXT, nome TEXT, fone TEXT, rua TEXT, num TEXT, 
                       bairro TEXT, cidade TEXT, estado TEXT, genero TEXT, 
                       profissao TEXT, nasc TEXT, idade INTEGER, notas TEXT, endereco TEXT)''')
    
    # Migrações Pacientes
    try: cursor.execute("ALTER TABLE pacientes ADD COLUMN endereco TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE pacientes ADD COLUMN nasc TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE pacientes ADD COLUMN idade INTEGER")
    except: pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS agenda_vagas 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, total_vagas INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS agendamentos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       id_paciente INTEGER, nome_cliente TEXT, fone_cliente TEXT,
                       data TEXT, hora TEXT, procedimento TEXT, valor REAL DEFAULT 0,
                       pago INTEGER DEFAULT 0, observacoes TEXT, created_at TEXT)''')
    
    # Migrações Agendamentos
    try: cursor.execute("ALTER TABLE agendamentos ADD COLUMN valor REAL DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE agendamentos ADD COLUMN observacoes TEXT")
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
                page.snack_bar.open = True; page.update(); return

            conn = sqlite3.connect("sistema_mestre.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome_completo, logomarca, segmento, financeiro_ativo, nome_estabelecimento, cpf, servico_ativo FROM clientes_dev WHERE nome_completo LIKE ?", (f"{n_val}%",))
            res = cursor.fetchone()
            conn.close()

            if res:
                cpf_banco = res[6]
                servico_ativo = res[7] if len(res) > 7 and res[7] is not None else 1
                
                if not servico_ativo:
                    page.snack_bar = ft.SnackBar(ft.Text("Serviço bloqueado! Contate o suporte."), bgcolor="red")
                    page.snack_bar.open = True; page.update(); return
                
                # Validação Rígida da Senha (6 últimos dígitos)
                senha_correta = False
                if cpf_banco:
                    cpf_limpo = re.sub(r'\D', '', cpf_banco)
                    if len(cpf_limpo) >= 6 and cpf_limpo.endswith(s_val):
                        senha_correta = True
                
                if senha_correta:
                    init_db_cliente(res[0])
                    abrir_app_profissional(res)
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Senha Incorreta!"), bgcolor="red")
                    page.snack_bar.open = True; page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Usuário não encontrado!"), bgcolor="red")
                page.snack_bar.open = True; page.update()

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
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # --- MENU PRINCIPAL DO CLIENTE ---
    def abrir_app_profissional(dados):
        id_p, nome, logo, seg, fin_ativo, estabelecimento, *_ = dados
        page.controls.clear()
        cor_tema = cores_segmento.get(seg, ft.Colors.BLUE_600)
        db_cliente = f"cliente_{id_p}.db"

        page.add(
            ft.AppBar(title=ft.Text(f"{estabelecimento}"), bgcolor=cor_tema, color="white", automatically_imply_leading=False),
            ft.Column([
                ft.Container(content=ft.Image(src=logo, width=100) if logo and os.path.exists(logo) else ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80), alignment=ft.Alignment(0, 0), padding=20),
                ft.Text(f"Bem-vindo(a), {nome}", size=16, weight="bold"),
                ft.Divider(),
                ft.ElevatedButton("AGENDAR", icon=ft.Icons.CALENDAR_MONTH, width=400, bgcolor=ft.Colors.PURPLE_700, color="white", height=60, on_click=lambda _: iniciar_agendamento(db_cliente, dados)),
                ft.ElevatedButton("CADASTRO DE CLIENTES", icon=ft.Icons.PERSON_ADD, width=400, on_click=lambda _: abrir_form_paciente(db_cliente, dados)),
                ft.ElevatedButton("VISUALIZAR AGENDA", icon=ft.Icons.LIST_ALT, width=400, on_click=lambda _: visualizar_agenda(db_cliente, dados)),
                ft.ElevatedButton("SISTEMA DE CAIXA", icon=ft.Icons.MONETIZATION_ON, width=400, visible=bool(fin_ativo), bgcolor=ft.Colors.GREEN_800, color="white"),
                ft.Divider(),
                ft.ElevatedButton("SAIR DO SISTEMA", icon=ft.Icons.LOGOUT, on_click=lambda _: mostrar_inicio(), width=400, bgcolor=ft.Colors.RED_700, color="white"),
                ft.Container(height=20),
                ft.Text("JeSystem TECNOLOGIAS - 2026", size=10, color=ft.Colors.GREY_400)
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # --- FLUXO DE AGENDAMENTO ---
    def iniciar_agendamento(db_path, dados_p):
        page.controls.clear()
        campo_fone_busca = ft.TextField(label="Fone do Cliente", on_change=formatar_fone_evento, width=400, border_radius=10)

        def confirmar_busca(e):
            f_l = re.sub(r'\D', '', campo_fone_busca.value)
            if len(f_l) < 10: 
                page.snack_bar = ft.SnackBar(ft.Text("Digite um telefone válido!"), bgcolor="orange"); page.snack_bar.open=True; page.update(); return
            
            conn = sqlite3.connect(db_path)
            res = conn.execute("SELECT * FROM pacientes WHERE REPLACE(REPLACE(REPLACE(REPLACE(fone, '(', ''), ')', ''), '-', ''), ' ', '') = ?", (f_l,)).fetchone()
            conn.close()
            
            if res:
                passar_para_calendario(db_path, dados_p, res)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Cliente não encontrado. Cadastre agora!"), bgcolor="orange"); page.snack_bar.open=True; page.update()
                abrir_form_paciente(db_path, dados_p, fone_inicial=campo_fone_busca.value, fluxo_agendamento=True)

        page.add(
            ft.AppBar(title=ft.Text("Novo Agendamento"), bgcolor=ft.Colors.PURPLE_700, color="white"),
            ft.Column([
                ft.Text("Digite o telefone do cliente:", size=16), campo_fone_busca,
                ft.ElevatedButton("CONTINUAR", on_click=confirmar_busca, width=400, bgcolor=ft.Colors.PURPLE_700, color="white", height=50),
                ft.TextButton("Voltar", on_click=lambda _: abrir_app_profissional(dados_p))
            ], horizontal_alignment="center", spacing=20)
        )
        page.update()

    def passar_para_calendario(db_path, dados_p, paciente):
        def handle_date_change(e):
            try:
                dt_value = e.control.value
                if dt_value:
                    if isinstance(dt_value, (datetime, date)):
                        data_str = dt_value.strftime("%d/%m/%Y")
                    else:
                        try:
                            dt = datetime.strptime(str(dt_value).split()[0], "%Y-%m-%d")
                            data_str = dt.strftime("%d/%m/%Y")
                        except:
                            data_str = str(dt_value)
                    
                    # Remove o date picker do overlay
                    try:
                        if date_picker in page.overlay:
                            page.overlay.remove(date_picker)
                            page.update()
                    except:
                        pass
                    
                    selecionar_hora_procedimento(db_path, dados_p, paciente, data_str)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao selecionar data: {str(ex)}"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        date_picker = ft.DatePicker(
            on_change=handle_date_change, 
            first_date=date.today(), 
            last_date=date(2030,12,31),
            entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY
        )
        page.overlay.append(date_picker)
        page.update()
        # Método correto para abrir o DatePicker
        date_picker.open = True
        page.update()

    def selecionar_hora_procedimento(db_path, dados_p, paciente, data_sel):
        page.controls.clear()
        
        def formatar_hora_input(e):
            v = re.sub(r'\D', '', e.control.value)
            if len(v) > 2: e.control.value = f"{v[:2]}:{v[2:4]}"
            else: e.control.value = v
            page.update()

        campo_hora = ft.TextField(label="Horário (HH:MM)", hint_text="Ex: 14:30", width=400, border_radius=10, on_change=formatar_hora_input, max_length=5)
        campo_proc = ft.TextField(label="Procedimento", width=400, border_radius=10)
        campo_valor = ft.TextField(label="Valor (R$)", keyboard_type="number", width=400, border_radius=10)
        campo_pago = ft.Checkbox(label="Procedimento já está pago?")
        campo_obs = ft.TextField(label="Observações", multiline=True, width=400, border_radius=10)

        def finalizar_agendamento(e):
            if not campo_hora.value or not campo_proc.value:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha horário e procedimento!"), bgcolor="red"); page.snack_bar.open=True; page.update(); return
            
            conn = sqlite3.connect(db_path)
            conflito = conn.execute("SELECT id FROM agendamentos WHERE data=? AND hora=?", (data_sel, campo_hora.value)).fetchone()
            if conflito:
                page.snack_bar = ft.SnackBar(ft.Text("HORÁRIO JÁ OCUPADO!"), bgcolor="red"); page.snack_bar.open=True; page.update(); conn.close(); return
            
            try:
                valor_float = float(campo_valor.value.replace(",", ".")) if campo_valor.value else 0.0
            except (ValueError, AttributeError):
                valor_float = 0.0
            
            conn.execute("INSERT INTO agendamentos (id_paciente, nome_cliente, fone_cliente, data, hora, procedimento, valor, pago, observacoes, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (paciente[0], paciente[2], paciente[3], data_sel, campo_hora.value, campo_proc.value, valor_float, 1 if campo_pago.value else 0, campo_obs.value or "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            page.snack_bar = ft.SnackBar(ft.Text("Agendado com Sucesso!"), bgcolor="green")
            page.snack_bar.open = True
            abrir_app_profissional(dados_p)

        page.add(
            ft.AppBar(title=ft.Text(f"Agenda: {data_sel}"), bgcolor=ft.Colors.PURPLE_700, color="white"),
            ft.Column([
                ft.Text(f"Cliente: {paciente[2]}", weight="bold", size=18),
                campo_hora, campo_proc, campo_valor, campo_pago, campo_obs,
                ft.ElevatedButton("CONFIRMAR", on_click=finalizar_agendamento, width=400, bgcolor="green", color="white", height=50),
                ft.TextButton("Cancelar", on_click=lambda _: abrir_app_profissional(dados_p))
            ], scroll="auto", horizontal_alignment="center", spacing=15)
        )
        page.update()

    # --- CADASTRO DE CLIENTE ---
    def abrir_form_paciente(db_path, dados_p, fone_inicial="", fluxo_agendamento=False):
        page.controls.clear()
        paciente_id = [None]
        
        c_fone = ft.TextField(label="Telefone *", border_radius=10, value=fone_inicial, on_change=formatar_fone_evento)
        c_cpf = ft.TextField(label="CPF", border_radius=10, on_change=formatar_cpf_evento)
        c_nome = ft.TextField(label="Nome Completo *", border_radius=10)
        c_nasc = ft.TextField(label="Nascimento (DD/MM/AAAA)", border_radius=10, on_change=formatar_data)
        
        # Campos de endereço novos
        c_rua = ft.TextField(label="Rua", border_radius=10)
        c_num = ft.TextField(label="Número", border_radius=10)
        c_bairro = ft.TextField(label="Bairro", border_radius=10)
        c_cidade = ft.TextField(label="Cidade", border_radius=10)
        c_estado = ft.TextField(label="UF", border_radius=10, max_length=2)
        c_anot = ft.TextField(label="Anotações", border_radius=10, multiline=True)
        
        btn_exc = ft.ElevatedButton("EXCLUIR", icon=ft.Icons.DELETE, bgcolor="red", color="white", visible=False)

        def carregar_dados(row):
            paciente_id[0] = row[0]
            c_cpf.value = aplicar_mascara_cpf(row[1]); c_nome.value = row[2]; c_fone.value = aplicar_mascara_fone(row[3])
            # Carregar endereço se existir
            if len(row) > 4: c_rua.value = row[4]
            if len(row) > 5: c_num.value = row[5]
            if len(row) > 6: c_bairro.value = row[6]
            if len(row) > 7: c_cidade.value = row[7]
            if len(row) > 8: c_estado.value = row[8]
            if len(row) > 13: c_anot.value = row[13]
            btn_exc.visible = True
            page.update()

        def verificar_existencia(e):
            val = re.sub(r'\D', '', e.control.value)
            if len(val) >= 10:
                conn = sqlite3.connect(db_path)
                if e.control == c_cpf and len(val) == 11:
                    res = conn.execute("SELECT * FROM pacientes WHERE cpf = ?", (val,)).fetchone()
                elif e.control == c_fone:
                    res = conn.execute("SELECT * FROM pacientes WHERE fone = ?", (e.control.value,)).fetchone()
                if res: carregar_dados(res)
                conn.close()

        c_cpf.on_change = lambda e: (formatar_cpf_evento(e), verificar_existencia(e))
        c_fone.on_change = lambda e: (formatar_fone_evento(e), verificar_existencia(e))

        def salvar(e):
            if not c_nome.value or len(c_fone.value) < 10:
                page.snack_bar = ft.SnackBar(ft.Text("Nome e Telefone são obrigatórios!"), bgcolor="red"); page.snack_bar.open=True; page.update(); return
            
            conn = sqlite3.connect(db_path); cursor = conn.cursor()
            cpf_l = re.sub(r'\D', '', c_cpf.value)
            
            if paciente_id[0]:
                cursor.execute("UPDATE pacientes SET cpf=?, nome=?, fone=?, rua=?, num=?, bairro=?, cidade=?, estado=?, nasc=?, notas=? WHERE id=?", 
                               (cpf_l, c_nome.value, c_fone.value, c_rua.value, c_num.value, c_bairro.value, c_cidade.value, c_estado.value, c_nasc.value, c_anot.value, paciente_id[0]))
                p_id = paciente_id[0]
            else:
                cursor.execute("INSERT INTO pacientes (cpf, nome, fone, rua, num, bairro, cidade, estado, nasc, notas) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                               (cpf_l, c_nome.value, c_fone.value, c_rua.value, c_num.value, c_bairro.value, c_cidade.value, c_estado.value, c_nasc.value, c_anot.value))
                p_id = cursor.lastrowid
            
            conn.commit(); conn.close()
            page.snack_bar = ft.SnackBar(ft.Text("Salvo com sucesso!"), bgcolor="green"); page.snack_bar.open=True
            
            if fluxo_agendamento:
                conn = sqlite3.connect(db_path); novo = conn.execute("SELECT * FROM pacientes WHERE id=?", (p_id,)).fetchone(); conn.close()
                passar_para_calendario(db_path, dados_p, novo)
            else:
                abrir_app_profissional(dados_p)

        def excluir(e):
            if paciente_id[0]:
                conn = sqlite3.connect(db_path); conn.execute("DELETE FROM pacientes WHERE id=?", (paciente_id[0],)); conn.commit(); conn.close()
                abrir_app_profissional(dados_p)

        btn_exc.on_click = excluir

        page.add(
            ft.AppBar(title=ft.Text("Cadastro de Cliente"), bgcolor=ft.Colors.BLUE_700, color="white", leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: abrir_app_profissional(dados_p))),
            ft.Column([
                ft.Text("Identificação", weight="bold"), c_fone, c_cpf,
                ft.Text("Dados Pessoais", weight="bold"), c_nome, c_nasc,
                ft.Text("Endereço", weight="bold"), c_rua, c_num, c_bairro, c_cidade, c_estado,
                ft.Text("Outros", weight="bold"), c_anot,
                ft.ElevatedButton("SALVAR", on_click=salvar, width=400, bgcolor="green", color="white", height=50),
                btn_exc, ft.TextButton("Voltar", on_click=lambda _: abrir_app_profissional(dados_p))
            ], scroll="auto", spacing=10)
        )
        page.update()

    def visualizar_agenda(db_path, dados_p):
        page.controls.clear()
        conn = sqlite3.connect(db_path)
        ags = conn.execute("SELECT * FROM agendamentos ORDER BY data, hora").fetchall()
        conn.close()
        
        lista = ft.Column(scroll="auto", expand=True)
        if not ags: lista.controls.append(ft.Text("Agenda vazia.", italic=True))
        
        for ag in ags:
            lista.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{ag[4]}\n{ag[3]}", weight="bold", color="white", size=16),
                        ft.VerticalDivider(color="white"),
                        ft.Column([ft.Text(ag[2], weight="bold", color="white"), ft.Text(f"R$ {ag[7]}", size=12, color="white")], expand=True),
                        ft.Text("PAGO" if ag[8] else "PENDENTE", size=12, weight="bold", color="white")
                    ]), bgcolor=ft.Colors.BLUE_700 if ag[8] else ft.Colors.ORANGE_800, padding=15, border_radius=10
                )
            )
        page.add(ft.AppBar(title=ft.Text("Agenda Completa")), lista, ft.ElevatedButton("VOLTAR", on_click=lambda _: abrir_app_profissional(dados_p), width=400))
        page.update()

    # --- ÁREA DO DESENVOLVEDOR ---
    def mostrar_login_dev():
        page.controls.clear()
        u_dev = ft.TextField(label="Usuário Admin", value="admin", border_radius=10)
        s_dev = ft.TextField(label="Senha SGS", password=True, border_radius=10)
        def check(e):
            if u_dev.value == "admin" and s_dev.value == "jere9261": abrir_painel_dev()
            else: page.snack_bar = ft.SnackBar(ft.Text("Erro!"), bgcolor="red"); page.snack_bar.open=True; page.update()
        page.add(ft.AppBar(title=ft.Text("Acesso Restrito")), ft.Column([ft.Text("Painel SAS", size=24), u_dev, s_dev, ft.ElevatedButton("ENTRAR", on_click=check)], horizontal_alignment="center"))
        page.update()

    def abrir_painel_dev():
        page.controls.clear()
        conn = sqlite3.connect("sistema_mestre.db")
        clis = conn.execute("SELECT id, nome_completo, nome_estabelecimento, segmento, servico_ativo FROM clientes_dev").fetchall()
        conn.close()
        
        lista = ft.Column(scroll="auto", expand=True)
        for c in clis:
            lista.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Row([
                ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.GREEN if (len(c)>4 and c[4]) else ft.Colors.RED),
                ft.Column([ft.Text(c[2], weight="bold"), ft.Text(c[1])], expand=True),
                ft.IconButton(ft.Icons.EDIT, icon_color="blue", on_click=lambda e, cid=c[0]: abrir_novo_profissional(cid)),
                ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda e, id=c[0]: excluir_cliente(id))
            ]))))
        page.add(ft.AppBar(title=ft.Text("Gestão")), ft.ElevatedButton("NOVO CLIENTE", on_click=lambda _: abrir_novo_profissional()), lista, ft.TextButton("Sair", on_click=lambda _: mostrar_inicio()))
        page.update()

    def abrir_novo_profissional(c_id=None):
        page.controls.clear()
        n = ft.TextField(label="Nome *"); est = ft.TextField(label="Estabelecimento *"); f = ft.TextField(label="Fone"); cp = ft.TextField(label="CPF (Senha) *"); end = ft.TextField(label="Endereço"); em = ft.TextField(label="Email"); px = ft.TextField(label="Pix"); prof = ft.TextField(label="Profissão"); seg = ft.Dropdown(label="Segmento", options=[ft.dropdown.Option(x) for x in lista_locais]); logo = ft.TextField(label="Logo"); fin = ft.Checkbox(label="Financeiro"); serv = ft.Checkbox(label="Ativo", value=True)
        
        if c_id:
            conn = sqlite3.connect("sistema_mestre.db")
            d = conn.execute("SELECT * FROM clientes_dev WHERE id=?", (c_id,)).fetchone(); conn.close()
            if d: n.value=d[1]; est.value=d[2]; seg.value=d[3]; prof.value=d[4]; end.value=d[6]; em.value=d[7]; f.value=d[8]; cp.value=d[9]; logo.value=d[10]; px.value=d[11]; fin.value=bool(d[12]); serv.value=bool(d[13] if len(d)>13 else 1)

        def cadastrar(e):
            if not n.value or not cp.value: return
            conn = sqlite3.connect("sistema_mestre.db"); cur = conn.cursor(); cp_l = re.sub(r'\D', '', cp.value)
            if c_id: cur.execute("UPDATE clientes_dev SET nome_completo=?, nome_estabelecimento=?, segmento=?, profissao=?, endereco=?, email=?, fone=?, cpf=?, logomarca=?, pix=?, financeiro_ativo=?, servico_ativo=? WHERE id=?", (n.value, est.value, seg.value, prof.value, end.value, em.value, f.value, cp_l, logo.value, px.value, 1 if fin.value else 0, 1 if serv.value else 0, c_id))
            else: 
                cur.execute("INSERT INTO clientes_dev (nome_completo, nome_estabelecimento, segmento, profissao, endereco, email, fone, cpf, logomarca, pix, financeiro_ativo, servico_ativo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (n.value, est.value, seg.value, prof.value, end.value, em.value, f.value, cp_l, logo.value, px.value, 1 if fin.value else 0, 1 if serv.value else 0))
                init_db_cliente(cur.lastrowid)
            conn.commit(); conn.close(); abrir_painel_dev()

        page.add(ft.AppBar(title=ft.Text("Dados")), ft.Column([n, est, f, cp, end, em, px, prof, seg, logo, fin, serv, ft.ElevatedButton("SALVAR", on_click=cadastrar)], scroll="auto"))
        page.update()

    def excluir_cliente(id_c):
        conn = sqlite3.connect("sistema_mestre.db"); conn.execute("DELETE FROM clientes_dev WHERE id=?", (id_c,)); conn.commit(); conn.close()
        if os.path.exists(f"cliente_{id_c}.db"): os.remove(f"cliente_{id_c}.db")
        abrir_painel_dev()

    mostrar_inicio()

if __name__ == "__main__":
    # Configuração para Render.com
    port = int(os.environ.get("PORT", 8080))
    
    # Para Render, usar configuração web simples
    # O Render já serve via web, então não precisa de view específica
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0"
    )
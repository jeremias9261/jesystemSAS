# JeSystem SAS - Sistema de Agendamento

Sistema SaaS de agendamento e gestão para diversos segmentos (clínicas, salões, barbearias, etc.).

## Deploy no Render.com

### Configuração

1. **Criar novo Web Service no Render**
   - Tipo: `Web Service`
   - Ambiente: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

2. **Variáveis de Ambiente**
   - `PORT`: Será definida automaticamente pelo Render (não precisa configurar manualmente)

3. **Arquivos Necessários**
   - `main.py` - Aplicação principal
   - `requirements.txt` - Dependências Python
   - `render.yaml` - Configuração do Render (opcional)

### Estrutura do Banco de Dados

- **sistema_mestre.db**: Banco principal com clientes do desenvolvedor
- **cliente_{id}.db**: Banco individual para cada cliente (isolamento de dados)

### Acesso

- **Login Cliente**: Primeiro nome + 6 últimos dígitos do CPF
- **Login Dev**: `admin` / `jere9261`

### Notas Importantes

- Os bancos de dados SQLite são criados automaticamente
- No Render, os dados são persistidos no sistema de arquivos efêmero
- Para produção, considere usar um banco de dados persistente (PostgreSQL)


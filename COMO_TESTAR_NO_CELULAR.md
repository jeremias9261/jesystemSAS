# 📱 Como Testar o App no Celular

## ✅ **JÁ PODE TESTAR AGORA!** 

Você pode testar no celular de duas formas:

---

## 🚀 **OPÇÃO 1: Teste via Rede Local (MAIS RÁPIDO - Recomendado para desenvolvimento)**

### **Passo a Passo:**

1. **Certifique-se que o celular e o computador estão na MESMA rede Wi-Fi**

2. **No computador, execute o app normalmente:**
   ```bash
   python main.py
   ```

3. **O Flet vai mostrar uma URL no terminal, algo como:**
   ```
   Flet app is running at http://192.168.1.100:8550
   ```

4. **No celular:**
   - Abra o navegador (Chrome, Safari, etc.)
   - Digite o endereço IP que apareceu (ex: `http://192.168.1.100:8550`)
   - O app vai abrir no navegador do celular!

5. **Para melhor experiência:**
   - No navegador do celular, vá em "Menu" → "Adicionar à Tela Inicial"
   - Isso cria um ícone na tela inicial, como um app nativo!

---

## 📦 **OPÇÃO 2: Compilar para APK (Para produção/distribuição)**

### **Requisitos:**
- Python instalado
- Flet instalado
- Android SDK (para gerar APK)

### **Passo a Passo:**

1. **Instale as dependências:**
   ```bash
   pip install flet
   ```

2. **Compile para Android:**
   ```bash
   flet build apk
   ```

3. **O APK será gerado na pasta `build/apk/`**

4. **Transfira o APK para o celular e instale**

---

## 🌐 **OPÇÃO 3: Hospedar na Web (Para acesso de qualquer lugar)**

### **Você pode hospedar em:**
- **GitHub Pages** (gratuito, mas limitado)
- **Heroku** (gratuito com limitações)
- **PythonAnywhere** (gratuito para testes)
- **VPS próprio** (AWS, DigitalOcean, etc.)

### **Exemplo com PythonAnywhere:**

1. Crie uma conta em pythonanywhere.com
2. Faça upload do `main.py`
3. Configure o app para rodar como web app
4. Acesse de qualquer lugar pelo navegador!

---

## ⚡ **DICA IMPORTANTE:**

Para testar **AGORA MESMO** no celular, use a **OPÇÃO 1** (rede local). É instantâneo e não precisa compilar nada!

---

## 🔧 **Troubleshooting:**

### **Não consegue acessar pelo IP?**
- Verifique se o firewall do Windows não está bloqueando
- Certifique-se que ambos estão na mesma rede Wi-Fi
- Tente desativar temporariamente o antivírus

### **O app não abre no celular?**
- Verifique se o Python está rodando no computador
- Confirme o IP correto no terminal
- Tente usar o IP do computador manualmente (veja nas configurações de rede)

---

## 📝 **Nota sobre Banco de Dados:**

Os bancos de dados SQLite são criados localmente no computador onde o app roda. Se você hospedar na web, precisará configurar um banco de dados remoto (PostgreSQL, MySQL, etc.) ou usar SQLite em um servidor.

---

**Pronto! Agora você pode testar no celular! 🎉**



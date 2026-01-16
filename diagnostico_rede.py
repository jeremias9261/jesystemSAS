"""
Script de diagnóstico para verificar problemas de conexão
"""
import socket
import sys

def get_local_ip():
    """Obtém o IP local"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return None

def check_port(port):
    """Verifica se a porta está disponível"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def main():
    print("\n" + "="*60)
    print("DIAGNOSTICO DE REDE")
    print("="*60 + "\n")
    
    # 1. Verificar IP
    print("1. Verificando IP do computador...")
    ip = get_local_ip()
    if ip:
        print(f"   [OK] IP encontrado: {ip}")
        print(f"   URL para celular: http://{ip}:8550")
    else:
        print("   [ERRO] Nao foi possivel obter o IP")
        print("   Verifique sua conexao Wi-Fi")
        return
    
    # 2. Verificar porta
    print("\n2. Verificando porta 8550...")
    if check_port(8550):
        print("   [AVISO] Porta 8550 esta em uso")
        print("   Feche outros programas que possam estar usando esta porta")
    else:
        print("   [OK] Porta 8550 esta livre")
    
    # 3. Instruções
    print("\n" + "="*60)
    print("PROXIMOS PASSOS:")
    print("="*60)
    print(f"\n1. Execute: python iniciar_app.py")
    print(f"\n2. No celular, abra o navegador e digite:")
    print(f"   http://{ip}:8550")
    print(f"\n3. Certifique-se de que:")
    print("   - Celular e computador estao na MESMA rede Wi-Fi")
    print("   - Firewall permite conexoes na porta 8550")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()


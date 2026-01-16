"""
Script auxiliar para iniciar o app e mostrar o IP para acesso via celular
"""
import socket
import flet as ft
import main

def get_local_ip():
    """Obtém o IP local do computador"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    porta = 8550
    url = f"http://{ip}:{porta}"
    
    print("\n" + "="*60)
    print("🚀 APP INICIADO COM SUCESSO!")
    print("="*60)
    print(f"\n📱 Para acessar no celular, use:")
    print(f"   {url}")
    print(f"\n💡 Certifique-se de que:")
    print("   ✓ Celular e computador estão na MESMA rede Wi-Fi")
    print("   ✓ Firewall do Windows permite conexões na porta 8550")
    print("\n" + "="*60 + "\n")
    
    # Inicia o app
    ft.app(target=main.main, port=porta)


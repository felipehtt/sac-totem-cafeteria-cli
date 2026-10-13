import os

def limpar_ecra():
    os.system('cls' if os.name == 'nt' else 'clear')

def tela_inicial():
    limpar_ecra()
    print("=" * 50)
    print("           S A C - C A F E T E R I A")
    print("       Sistema de Autoatendimento Inteligente")
    print("=" * 50)
    print("\n           Bem-vindo(a) ao nosso Totem!\n")
    input("      [ Pressione ENTER para iniciar o seu pedido ]")

def main():
    while True:
        tela_inicial()
        # Após o ENTER, o cliente vai para o menu de categorias (fazer ainda)
        print("\nA avançar para o catálogo...")
        break # O break está aqui temporariamente  para o programa não rodar infinitamente

if __name__ == "__main__":
    main()
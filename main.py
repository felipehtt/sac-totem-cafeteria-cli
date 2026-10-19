import os

cardapio = {

    "1": {"nome": "Bebidas Quentes", "itens": {11: ["Café Expresso", 5.00], 12: ["Cappuccino", 8.00]}},
    "2": {"nome": "Bebidas Geladas", "itens": {21: ["Chá Gelado", 6.00], 22: ["Frappuccino", 12.00]}},
    "3": {"nome": "Comidas", "itens": {31: ["Pão de Queijo", 4.50], 32: ["Misto Quente", 7.00]}}

}

carrinho = []

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def tela_inicial():
    limpar_tela()
    print("=" * 50)
    print("           S A C - C A F E T E R I A")
    print("       Sistema de Autoatendimento Inteligente")
    print("=" * 50)
    print("\n           Bem-vindo(a) ao nosso Totem!\n")
    input("      [ Pressione ENTER para iniciar o seu pedido ]")

def tela_itens(id_categoria):
    # lista os produtos de uma categoria específica

    while True:
        limpar_tela()
        categoria = cardapio[id_categoria]
        print("=" * 50)
        print(f"--- {categoria['nome'].upper()} ---")
        print("=" * 50)

        # ve os itens do dicionário e imprime formatado
        for codigo, dados in categoria['itens'].items():
            nome_produto = dados[0]
            preco_produto = dados[1]
            print(f"[{codigo}] {nome_produto.ljust(20, '.')} R$ {preco_produto:.2f}")
            # o .ljust(20, '.') preenche o espaço com pontinhos para o preço ficar alinhado

        print("\n[0] Voltar às Categorias")
        
        escolha = input("\nDigite o código do produto para adicionar: ")
        
        if escolha == "0":
            break

        # ve se o cliente digitou um número e se esse número existe na categoria
        elif escolha.isdigit() and int(escolha) in categoria['itens']:
            codigo_item = int(escolha)
            produto_selecionado = categoria['itens'][codigo_item]

            # coloca um dicionário com os dados do produto na lista do carrinho
            carrinho.append({
                "codigo": codigo_item,
                "nome": produto_selecionado[0],
                "preco": produto_selecionado[1]
            })
            
            print(f"\n-> {produto_selecionado[0]} adicionado ao carrinho com sucesso!")
            input("\nPressione ENTER para continuar...")
            break # volta no menu de categorias para continuar comprando
        else:
            print("\nCódigo inválido. Tente novamente.")
            input("\nPressione ENTER para continuar...")

def tela_catalogo():

    while True:
        limpar_tela()
        print("=" * 50)
        print("                  C A R D Á P I O")
        print("=" * 50)
        print("Categorias:")
        print("[1] Bebidas Quentes")
        print("[2] Bebidas Geladas")
        print("[3] Comidas")
        print("[4] 🛒 Ver Carrinho e Finalizar")
        print("[0] Cancelar Pedido / Voltar ao Início")

        opcao = input("\nEscolha uma categoria (1-3) ou 0 para cancelar: ")

        if opcao == "0":
            carrinho.clear() # Limpa o carrinho se o utilizador desistir
            break
        elif opcao == "4":
            print("\nIndo para o carrinho...")
            input("\nPressione ENTER...")
        elif opcao in cardapio:
            tela_itens(opcao)
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione ENTER para continuar...")

def main():
    while True:
        tela_inicial()
        tela_catalogo()

if __name__ == "__main__":
    main()
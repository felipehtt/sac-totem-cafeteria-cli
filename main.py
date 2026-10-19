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
            carrinho.clear() # esvazia o carrinho se o cliente desistir
            break
        elif opcao == "4":
            tela_carrinho()
        elif opcao in cardapio:
            tela_itens(opcao)
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione ENTER para continuar...")

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

def tela_carrinho():
    while True:
        limpar_tela()
        print("=" * 50)
        print("                 S E U  P E D I D O")
        print("=" * 50)
        
        # ve se o carrinho está vazio
        if len(carrinho) == 0:
            print("O seu carrinho está vazio.")
            input("\nPressione ENTER para voltar ao cardápio...")
            break # volta para as categorias
            
        print("Itens no Carrinho:")
        subtotal = 0
        
        # variáveis para a nossa "IA" de recomendação rastrear o que o cliente comprou
        tem_cafe = False
        tem_pao_queijo = False
        
        # lista os itens e calcula o subtotal
        for item in carrinho:
            nome_produto = item["nome"]
            preco_produto = item["preco"]
            print(f"- 1x {nome_produto.ljust(20, '.')} R$ {preco_produto:.2f}")
            subtotal += preco_produto
            
            # o sistema toma nota mental do que está no carrinho
            if item["codigo"] == 11: # 11 é o Café Expresso
                tem_cafe = True
            if item["codigo"] == 31: # 31 é o Pão de Queijo
                tem_pao_queijo = True
                
        print(f"\nSubtotal: R$ {subtotal:.2f}")
        print("-" * 50)
        
        # o diferencial de lógica/IA (Venda Casada)
        # regra: se tem café mas NÃO tem pão de queijo, o sistema sugere
        if tem_cafe and not tem_pao_queijo:
            print("- SUGESTÃO INTELIGENTE -")
            print("Notamos que pediu um Café Expresso!")
            print("A maioria dos clientes também leva um Pão de Queijo.")
            
            # vai buscar o preço e o nome dinamicamente ao dicionário
            preco_pao = cardapio["3"]["itens"][31][1]
            nome_pao = cardapio["3"]["itens"][31][0]
            
            resposta = input(f"\nDeseja adicionar 1x {nome_pao} (R$ {preco_pao:.2f})? (S/N): ").strip().upper()
            
            if resposta == "S":
                carrinho.append({"codigo": 31, "nome": nome_pao, "preco": preco_pao})
                print(f"\n-> {nome_pao} adicionado com sucesso!")
                input("Pressione ENTER para atualizar o carrinho...")
                continue # o continue faz o loop voltar ao início e recalcular o subtotal atualizado
        
        # opções Finais
        print("\n[1] Finalizar Pedido e Pagar")
        print("[0] Voltar para o Cardápio")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            tela_pagamento(subtotal)
            break
        elif opcao == "0":
            break
        else:
            print("\nOpção inválida.")
            input("Pressione ENTER para tentar novamente...")

def gerar_recibo(subtotal, valor_inserido, troco, tempo_estimado):
    # o 'w' significa 'write' (escrever), cria ou substitui o ficheiro recibo.txt
    with open("recibo.txt", "w", encoding="utf-8") as ficheiro:
        ficheiro.write("=" * 40 + "\n")
        ficheiro.write("           SAC - CAFETERIA\n")
        ficheiro.write("=" * 40 + "\n")
        ficheiro.write("ITENS DO PEDIDO:\n")
        for item in carrinho:
            ficheiro.write(f"- 1x {item['nome'].ljust(20, '.')} R$ {item['preco']:.2f}\n")
        ficheiro.write("-" * 40 + "\n")
        ficheiro.write(f"TOTAL A PAGAR:   R$ {subtotal:.2f}\n")
        ficheiro.write(f"VALOR INSERIDO:  R$ {valor_inserido:.2f}\n")
        ficheiro.write(f"TROCO:           R$ {troco:.2f}\n")
        ficheiro.write("-" * 40 + "\n")
        ficheiro.write(f"TEMPO ESTIMADO:  {tempo_estimado} minutos\n")
        ficheiro.write("=" * 40 + "\n")
        ficheiro.write("Obrigado pela preferência!\n")

def tela_pagamento(subtotal):
    limpar_tela()
    print("=" * 50)
    print("                 F I N A L I Z A R")
    print("=" * 50)
    print(f"TOTAL A PAGAR: R$ {subtotal:.2f}\n")
    
    # lógica de pagamento e troco
    while True:
        try:
            # .replace permite que o utilizador digite "10,50" ou "10.50" sem dar erro
            entrada = input("Valor inserido em dinheiro (R$): ").replace(',', '.')
            valor_inserido = float(entrada)
            
            if valor_inserido >= subtotal:
                troco = valor_inserido - subtotal
                break
            else:
                print("Valor insuficiente. Insira um valor igual ou superior ao total.\n")
        except ValueError:
            print("Valor inválido. Digite apenas números (ex: 50.00).\n")
            
    print("\nA calcular...")
    print(f"TROCO: R$ {troco:.2f}")
    print("-" * 50)
    
    # diferencial lógico: estimaa o tempo de preparo
    # fórmula: 2 min base + (1.5 min por cada item) + (simulação de 3 pedidos na fila * 2 min)
    tempo_base = 2 
    tempo_por_item = len(carrinho) * 1.5
    pedidos_na_fila = 3 
    tempo_estimado = int(tempo_base + tempo_por_item + (pedidos_na_fila * 2))
    
    print(f"⏳ TEMPO ESTIMADO DE PREPARO: {tempo_estimado} minutos")
    print("(Cálculo baseado na fila atual e nos itens)\n")
    
    # gera o ficheiro .txt
    gerar_recibo(subtotal, valor_inserido, troco, tempo_estimado)
    
    print("Pedido Finalizado! Recibo gerado em 'recibo.txt'.")
    print("Aguarde ser chamado no balcão. Obrigado!")
    print("=" * 50)
    
    # limpa o carrinho para o próximo cliente poder usar o totem
    carrinho.clear()
    input("\nPressione ENTER para regressar ao ecrã inicial...")

def main():
    while True:
        tela_inicial()
        tela_catalogo()

if __name__ == "__main__":
    main()
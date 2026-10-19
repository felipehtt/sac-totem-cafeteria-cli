import getpass
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
 
# ---------------------------------------------------------------------------
# Constantes nomeadas
# ---------------------------------------------------------------------------
MAX_ITENS = 20
COD_CAFE = 11
COD_PAO_QUEIJO = 31
TEMPO_BASE_MIN = 2
TEMPO_POR_ITEM_MIN = 1.5
PEDIDOS_NA_FILA = 3
TEMPO_POR_PEDIDO_FILA_MIN = 2
LARGURA_TELA = 50
LARGURA_RECIBO = 40
ARQUIVO_RECIBO = Path(__file__).resolve().parent / "recibo.txt"
 
# Detecta se o terminal suporta UTF-8; senão usa símbolos ASCII
SUPORTA_UTF8 = (sys.stdout.encoding or "").lower().replace("-", "") == "utf8"
ICONE_CARRINHO = "🛒" if SUPORTA_UTF8 else "[#]"
ICONE_OK = "✅" if SUPORTA_UTF8 else "[OK]"
QR_ART = [
    "   █▀▀▀▀▀█ ▀▀▀█▀ █▀▀▀▀▀█",
    "   █ ███ █ █ █ █ █ ███ █",
    "   █ ▀▀▀ █ █▀▀██ █ ▀▀▀ █",
    "   ▀▀▀▀▀▀▀ ▀ ▀ ▀ ▀▀▀▀▀▀▀",
]
 
 
# Produto como dataclass
@dataclass(frozen=True)
class Produto:
    codigo: int
    nome: str
    preco: Decimal


CARDAPIO: dict[str, dict] = {
    "1": {"nome": "Bebidas Quentes", "itens": [
        Produto(11, "Café Expresso", Decimal("5.00")),
        Produto(12, "Cappuccino", Decimal("8.00")),
    ]},
    "2": {"nome": "Bebidas Geladas", "itens": [
        Produto(21, "Chá Gelado", Decimal("6.00")),
        Produto(22, "Frappuccino", Decimal("12.00")),
    ]},
    "3": {"nome": "Comidas", "itens": [
        Produto(31, "Pão de Queijo", Decimal("4.50")),
        Produto(32, "Misto Quente", Decimal("7.00")),
    ]},
}

OPCAO_CARRINHO = str(len(CARDAPIO) + 1)


# ---------------------------------------------------------------------------
# Funções puras (sem print/input): fáceis de testar
# ---------------------------------------------------------------------------
def buscar_produto(codigo: int) -> Produto | None:
    """Procura um produto pelo código em todo o cardápio."""
    for categoria in CARDAPIO.values():
        for produto in categoria["itens"]:
            if produto.codigo == codigo:
                return produto
    return None
 
 
def calcular_total(carrinho: list[Produto]) -> Decimal:
    """Soma o preço de todos os itens do carrinho."""
    return sum((p.preco for p in carrinho), Decimal("0"))
 
 
def deve_sugerir_venda_casada(carrinho: list[Produto]) -> bool:
    """Regra: tem Café Expresso, não tem Pão de Queijo e ainda há espaço no carrinho."""
    codigos = {p.codigo for p in carrinho}
    return (
        COD_CAFE in codigos
        and COD_PAO_QUEIJO not in codigos
        and len(carrinho) < MAX_ITENS
    )
 
 
def estimar_tempo(qtd_itens: int) -> int:
    """Estima o preparo em minutos: base + tempo por item + fila simulada."""
    return int(
        TEMPO_BASE_MIN
        + qtd_itens * TEMPO_POR_ITEM_MIN
        + PEDIDOS_NA_FILA * TEMPO_POR_PEDIDO_FILA_MIN
    )
 
 
def agrupar_itens(carrinho: list[Produto]) -> list[tuple[Produto, int]]:
    """[NOVO D1] Agrupa itens repetidos: [(Produto, quantidade), ...]."""
    contagem: dict[Produto, int] = {}
    for produto in carrinho:
        contagem[produto] = contagem.get(produto, 0) + 1
    return list(contagem.items())
 
 
# ---------------------------------------------------------------------------
# Utilitários de interface
# ---------------------------------------------------------------------------
def limpar_tela() -> None:
    """Limpa o terminal (Windows ou Unix)."""
    os.system("cls" if os.name == "nt" else "clear")
 
 
def cabecalho(titulo: str) -> None:
    """Imprime um título entre linhas de '=' com largura padrão."""
    print("=" * LARGURA_TELA)
    print(titulo.center(LARGURA_TELA))
    print("=" * LARGURA_TELA)
 
 
def ler_opcao(prompt: str, validas: set[str]) -> str:
    """Pede uma entrada até o usuário digitar uma opção válida."""
    while True:
        valor = input(prompt).strip().upper()
        if valor in validas:
            return valor
        print(f"\nOpção inválida. Use: {', '.join(sorted(validas))}")
 
 
def desenhar_qr() -> None:
    """Desenha o 'QR Code' simulado, com fallback ASCII."""
    print()
    for linha in QR_ART:
        print(linha if SUPORTA_UTF8 else linha.translate(str.maketrans("█▀", "##")))


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------
def tela_inicial() -> None:
    """Tela de boas-vindas."""
    limpar_tela()
    print("=" * LARGURA_TELA)
    print("           S A C - C A F E T E R I A")
    print("       Sistema de Autoatendimento Inteligente")
    print("=" * LARGURA_TELA)
    print("\n           Bem-vindo(a) ao nosso Totem!\n")
    input("      [ Pressione ENTER para iniciar o seu pedido ]")
    print("\nCarregando o sistema...")
    time.sleep(1)


def tela_catalogo(carrinho: list[Produto]) -> None:
    """Menu de categorias. Retorna quando o pedido termina ou é cancelado."""
    while True:
        limpar_tela()
        cabecalho("C A R D Á P I O")
        print("Categorias:")
        # categorias geradas a partir do CARDAPIO
        for id_categoria, categoria in CARDAPIO.items():
            print(f"[{id_categoria}] {categoria['nome']}")
        print(f"[{OPCAO_CARRINHO}] {ICONE_CARRINHO} Ver Carrinho e Finalizar")
        print("[0] Cancelar Pedido / Voltar ao Início")
 
        validas = {"0", OPCAO_CARRINHO, *CARDAPIO}
        # texto de ajuda agora menciona o carrinho
        opcao = ler_opcao(
            f"\nEscolha uma categoria (1-{len(CARDAPIO)}), "
            f"{OPCAO_CARRINHO} para o carrinho ou 0 para cancelar: ",
            validas,
        )
 
        if opcao == "0":
            carrinho.clear()  # esvazia o carrinho se o cliente desistir
            break
        elif opcao == OPCAO_CARRINHO:
            # só volta ao início se o pedido terminou/foi cancelado;
            # carrinho vazio ou "voltar" mantém o cliente no catálogo
            if tela_carrinho(carrinho) == "inicio":
                break
        else:
            tela_itens(opcao, carrinho)

def tela_itens(id_categoria: str, carrinho: list[Produto]) -> None:
    """Lista os produtos de uma categoria e adiciona o escolhido ao carrinho."""
    categoria = CARDAPIO[id_categoria]
    produtos = {str(p.codigo): p for p in categoria["itens"]}
 
    limpar_tela()
    cabecalho(f"--- {categoria['nome'].upper()} ---")
 
    for produto in categoria["itens"]:
        # o ljust preenche com pontinhos para o preço ficar alinhado
        print(f"[{produto.codigo}] {produto.nome.ljust(20, '.')} R$ {produto.preco:.2f}")
 
    print("\n[0] Voltar às Categorias")
 
    escolha = ler_opcao(
        "\nDigite o código do produto para adicionar: ", {"0", *produtos}
    )
    if escolha == "0":
        return
 
    if len(carrinho) >= MAX_ITENS:
        print(f"\n- Limite máximo de {MAX_ITENS} itens por pedido atingido!")
        print("Por favor, finalize esta compra antes de pedir mais itens.")
        input("\nPressione ENTER para voltar às categorias...")
        return
 
    produto = produtos[escolha]
    carrinho.append(produto)
    print(f"\n-> {produto.nome} adicionado ao carrinho com sucesso!")
    input("\nPressione ENTER para continuar...")

def remover_item(carrinho: list[Produto]) -> None:
    """Remove uma unidade de um item do carrinho."""
    grupos = agrupar_itens(carrinho)
    print("\nQual item deseja remover (1 unidade)?")
    for i, (produto, qtd) in enumerate(grupos, start=1):
        print(f"[{i}] {qtd}x {produto.nome}")
    print("[0] Cancelar")
 
    validas = {"0", *(str(i) for i in range(1, len(grupos) + 1))}
    escolha = ler_opcao("\nEscolha o item: ", validas)
    if escolha == "0":
        return
 
    produto = grupos[int(escolha) - 1][0]
    carrinho.remove(produto)
    print(f"\n-> 1x {produto.nome} removido do carrinho.")
    input("Pressione ENTER para atualizar o carrinho...")

def tela_carrinho(carrinho: list[Produto]) -> str:
    """Mostra o carrinho. Retorna 'catalogo' (voltar) ou 'inicio' (pedido encerrado)."""
    while True:
        limpar_tela()
        cabecalho("S E U  P E D I D O")
 
        if not carrinho:
            print("Seu carrinho está vazio.")
            input("\nPressione ENTER para voltar ao cardápio...")
            return "catalogo"
 
        print("Itens no Carrinho:")
        # itens agrupados ("3x Café") em vez de uma linha por unidade
        for produto, qtd in agrupar_itens(carrinho):
            print(f"- {qtd}x {produto.nome.ljust(20, '.')} R$ {produto.preco * qtd:.2f}")
 
        subtotal = calcular_total(carrinho)
        print(f"\nSubtotal: R$ {subtotal:.2f}")
        print("-" * LARGURA_TELA)
 
        # "IA": na verdade é uma regra simples de venda casada
        if deve_sugerir_venda_casada(carrinho):
            pao = buscar_produto(COD_PAO_QUEIJO)
            if pao is not None:
                print("\n- SUGESTÃO DA CASA -")
                print("\nNotamos que pediu um Café Expresso!")
                print("A maioria dos clientes também leva um Pão de Queijo.")
                resposta = ler_opcao(
                    f"\nDeseja adicionar 1x {pao.nome} (R$ {pao.preco:.2f})? (S/N): ",
                    {"S", "N"},
                )
                if resposta == "S":
                    carrinho.append(pao)
                    print(f"\n-> {pao.nome} adicionado com sucesso!")
                    input("Pressione ENTER para atualizar o carrinho...")
                    continue  # recalcula o subtotal
 
        print("\n[1] Finalizar Pedido e Pagar")
        print("[2] Remover um item")  # [NOVO D1]
        print("[0] Voltar para o Cardápio")
 
        opcao = ler_opcao("\nEscolha uma opção: ", {"0", "1", "2"})
 
        if opcao == "1":
            tela_pagamento(carrinho, subtotal)  # [ALTERADO B1]
            return "inicio"  # pago ou cancelado: volta à tela inicial
        elif opcao == "2":
            remover_item(carrinho)
        else:
            return "catalogo"

def proximo_numero_pedido() -> int:
    """Número sequencial do pedido, contado a partir do arquivo de recibos."""
    try:
        texto = ARQUIVO_RECIBO.read_text(encoding="utf-8")
    except OSError:
        return 1
    return texto.count("PEDIDO Nº") + 1

def gerar_recibo(
    carrinho: list[Produto],
    total: Decimal,
    forma_pagamento: str,
    tempo_estimado: int,
) -> bool:  # recebe o carrinho e o total; retorna sucesso
    """Acrescenta o recibo ao arquivo. Retorna False se não conseguiu gravar."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linhas = [
        "=" * LARGURA_RECIBO,
        "           SAC - CAFETERIA",
        f"           {agora}",
        f"           PEDIDO Nº {proximo_numero_pedido():04d}",
        "=" * LARGURA_RECIBO,
        "ITENS DO PEDIDO:",
    ]
    for produto, qtd in agrupar_itens(carrinho):
        linhas.append(f"- {qtd}x {produto.nome.ljust(20, '.')} R$ {produto.preco * qtd:.2f}")
    linhas += [
        "-" * LARGURA_RECIBO,
        f"TOTAL PAGO:   R$ {total:.2f}",
        f"PAGAMENTO VIA:  {forma_pagamento}",
        "-" * LARGURA_RECIBO,
        f"TEMPO ESTIMADO:  {tempo_estimado} minutos",
        "=" * LARGURA_RECIBO,
        "Obrigado pela preferência!",
        "", "", "",
    ]
    try:
        # 'a' = append: não apaga as vendas anteriores
        with open(ARQUIVO_RECIBO, "a", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas))
    except OSError as erro:
        print(f"\n! Não foi possível gravar o recibo ({erro}). Chame um atendente.")
        return False
    return True

def tela_pagamento(carrinho: list[Produto], subtotal: Decimal) -> bool:
    """Processa o pagamento. Retorna True se pago, False se cancelado."""

    limpar_tela()
    cabecalho("F I N A L I Z A R")
    print(f"TOTAL A PAGAR: R$ {subtotal:.2f}\n")
    print("Formas de Pagamento disponíveis:")
    print("[1] Cartão de Débito / Crédito")
    print("[2] PIX")
    print("[0] Cancelar Pedido")
 
    opcao = ler_opcao("\nEscolha a forma de pagamento: ", {"0", "1", "2"})
 
    if opcao == "0":
        print("\nPedido cancelado pelo usuário. Voltando ao início...")
        carrinho.clear()
        time.sleep(2)
        return False  # volta pra tela inicial sem gerar recibo
 
    if opcao == "1":
        forma_pagamento = "Cartão"
        print("\n-> Por favor, aproxime ou insira o cartão na máquina...")
        time.sleep(2)
        getpass.getpass("Digite sua senha e pressione ENTER: ")
        print("\nProcessando pagamento com o banco...")
        time.sleep(2)
        print(f"{ICONE_OK} Pagamento Aprovado!")
    else:
        forma_pagamento = "PIX"
        print("\n-> Conectando ao Banco Central...")
        time.sleep(1)
        print("-> Gerando QR Code...")
        time.sleep(1)
        desenhar_qr()
        print("\nAbra o aplicativo do seu banco e leia o código acima.")
        input("Pressione ENTER após confirmar o pagamento no celular...")
        print("\nVerificando transferência...")
        time.sleep(1.5)
        print(f"\n{ICONE_OK} Pagamento PIX Recebido com Sucesso!")
        
    # diferencial lógico: estimaa o tempo de preparo
    print("-" * LARGURA_TELA)
    tempo_estimado = estimar_tempo(len(carrinho))
    
    print(f"\n- TEMPO ESTIMADO DE PREPARO: {tempo_estimado} minutos")
    print("(Cálculo baseado na fila atual e nos itens)\n")
    
    # gera o ficheiro .txt
    recibo_ok = gerar_recibo(carrinho, subtotal, forma_pagamento, tempo_estimado)
    if recibo_ok:
        print(f"Pedido Finalizado! Recibo gerado em '{ARQUIVO_RECIBO.name}'.")
    else:
        print("Pedido Finalizado!")
    print("Aguarde ser chamado no balcão. Obrigado!\n")
    print("=" * LARGURA_TELA)
    
    # limpa o carrinho para o próximo cliente poder usar o totem
    carrinho.clear()
    input("\nPressione ENTER para voltar à tela inicial...")
    return True

def main() -> None:
    """Laço principal do totem."""
    carrinho: list[Produto] = []
    while True:
        tela_inicial()
        tela_catalogo(carrinho)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # se alguém tentar quebrar o totem com Ctrl+C, o terminal limpa e desliga em segurança
        limpar_tela()
        print("Sistema encerrado de forma segura pelo Administrador.")
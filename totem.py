import getpass
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes
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

# desconto aplicado ao item sugerido quando o cliente leva o combo
DESCONTO_COMBO = Decimal("0.10")
PERCENTUAL_COMBO = int(DESCONTO_COMBO * 100)
CENTAVO = Decimal("0.01")

# animação na tela inicial (só roda em terminal interativo)
QUADROS_ANIMACAO = 9
PAUSA_QUADRO_S = 0.35
ANIMAR = sys.stdout.isatty()

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

# ---------------------------------------------------------------------------

# Arte ASCII (apenas caracteres ASCII: funciona em qualquer terminal)

# ---------------------------------------------------------------------------

CANECA = [
    r" .------------.   ",
    r" |   S A C    |==.",
    r" |            |  |",
    r" \            /==' ",
    r"  `-.______.-'    ",
    r"\______________/  ",
]

# Três quadros de fumaça (3 linhas cada), alternando para dar movimento
FUMACA = [
    [
        r"    )   (   )   ",
        r"   (   )   (    ",
        r"    )   (   )   ",
    ],
    [
        r"   (   )   (    ",
        r"    )   (   )   ",
        r"   (   )   (    ",
    ],
    [
        r"    (   )   (   ",
        r"   )   (   )    ",
        r"    (   )   (   ",
    ],
]

ARTE_QUENTE = [
    r"   ) (",
    r" .-----.",
    r" |     |]",
    r" \     /",
    r"  `---'",
]
ARTE_GELADA = [
    r"     /",
    r" .--/-.",
    r" |~~~~|",
    r" |~~~~|",
    r"  \__/",
]
ARTE_SANDUBA = [
    r"  .-~~-.",
    r" ( o  o )",
    r"  `-__-'",
    r" ########",
    r"  (____)",
]
ARTE_BOLO = [
    r"    o",
    r"  .-~-.",
    r" /~~~~~\ ",
    r"|=======|",
    r"`-------'",
]

# Produto como dataclass
@dataclass(frozen=True)
class Produto:
    codigo: int
    nome: str
    preco: Decimal


CARDAPIO: dict[str, dict] = {
    "1": {"nome": "Bebidas Quentes", "arte": ARTE_QUENTE, "itens": [
        Produto(11, "Café Expresso", Decimal("5.00")),
        Produto(12, "Cappuccino", Decimal("8.00")),
        Produto(13, "Chocolate Quente", Decimal("9.00")),
        Produto(14, "Café com Leite", Decimal("6.50")),
    ]},
    "2": {"nome": "Bebidas Geladas", "arte": ARTE_GELADA, "itens": [
        Produto(21, "Chá Gelado", Decimal("6.00")),
        Produto(22, "Frappuccino", Decimal("12.00")),
        Produto(23, "Suco de Laranja", Decimal("8.00")),
        Produto(24, "Limonada Suíça", Decimal("7.50")),
    ]},
    "3": {"nome": "Comidas", "arte": ARTE_SANDUBA, "itens": [
        Produto(31, "Pão de Queijo", Decimal("4.50")),
        Produto(32, "Misto Quente", Decimal("7.00")),
        Produto(33, "Croissant", Decimal("9.00")),
    ]},
    "4": {"nome": "Doces", "arte": ARTE_BOLO, "itens": [
        Produto(41, "Brownie", Decimal("8.00")),
        Produto(42, "Cookie", Decimal("6.00")),
        Produto(43, "Torta de Limão", Decimal("10.00")),
        Produto(44, "Bolo de Cenoura", Decimal("8.50")),
    ]},
}

OPCAO_CARRINHO = str(len(CARDAPIO) + 1)

# ---------------------------------------------------------------------------
# Recomendações: "quem pediu X costuma levar Y"
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Recomendacao:
    """Se o cliente tem `gatilho` no carrinho, sugerimos `sugestao`."""

    gatilho: int
    sugestao: int
    mensagem: str


RECOMENDACOES: list[Recomendacao] = [
    Recomendacao(11, 31, "A maioria dos clientes também leva um Pão de Queijo."),
    Recomendacao(12, 33, "Cappuccino e Croissant são uma dupla clássica."),
    Recomendacao(13, 42, "Chocolate Quente fica ótimo com um Cookie para molhar."),
    Recomendacao(14, 44, "Café com Leite combina com uma fatia de Bolo de Cenoura."),
    Recomendacao(21, 32, "Um Chá Gelado vai muito bem com um Misto Quente."),
    Recomendacao(22, 41, "Que tal um Brownie para acompanhar o Frappuccino?"),
    Recomendacao(32, 23, "Misto Quente pede um Suco de Laranja bem gelado."),
    Recomendacao(44, 11, "Bolo de Cenoura fica perfeito com um Café Expresso."),
    Recomendacao(43, 21, "Torta de Limão refresca ainda mais com um Chá Gelado."),
]

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
    return sum((p.preco for p in carrinho), Decimal("0.00"))

def proxima_sugestao(
    carrinho: list[Produto], recusadas: set[int] | frozenset[int] = frozenset()
) -> Recomendacao | None:
    """Primeira recomendação aplicável ao carrinho, ou None."""
    if len(carrinho) >= MAX_ITENS:
        return None
    codigos = {p.codigo for p in carrinho}
    for rec in RECOMENDACOES:
        if (
            rec.gatilho in codigos
            and rec.sugestao not in codigos
            and rec.sugestao not in recusadas
        ):
            return rec
    return None

def deve_sugerir_venda_casada(carrinho: list[Produto]) -> bool:
    """Indica se existe alguma sugestão para o carrinho (mantida por compatibilidade)."""
    return proxima_sugestao(carrinho) is not None

def listar_combos(carrinho: list[Produto]) -> list[tuple[Recomendacao, int]]:
    """Combos completos no carrinho: [(regra, quantidade de combos), ...]."""
    contagem = Counter(p.codigo for p in carrinho)
    combos = []
    for rec in RECOMENDACOES:
        qtd = min(contagem[rec.gatilho], contagem[rec.sugestao])
        if qtd > 0:
            combos.append((rec, qtd))
    return combos

def desconto_do_combo(rec: Recomendacao, qtd: int = 1) -> Decimal:
    """Desconto de `qtd` combos da regra `rec` (incide no item sugerido)."""
    produto = buscar_produto(rec.sugestao)
    if produto is None:
        return Decimal("0.00")
    return (produto.preco * DESCONTO_COMBO * qtd).quantize(CENTAVO, rounding=ROUND_HALF_UP)

def calcular_desconto(carrinho: list[Produto]) -> Decimal:
    """Soma dos descontos de todos os combos do carrinho."""
    return sum(
        (desconto_do_combo(rec, qtd) for rec, qtd in listar_combos(carrinho)),
        Decimal("0.00"),
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

def lado_a_lado(artes: list[list[str]], espaco: int = 4) -> list[str]:
    """Junta várias artes em colunas, alinhadas pela base."""
    altura = max(len(a) for a in artes)
    coluna = max(len(linha) for a in artes for linha in a)
    linhas = []
    for i in range(altura):
        partes = []
        for arte in artes:
            j = i - (altura - len(arte))
            partes.append((arte[j] if j >= 0 else "").ljust(coluna))
        linhas.append((" " * espaco).join(partes))
    return linhas

def centralizar_arte(linhas: list[str]) -> list[str]:
    """Centraliza a arte como um bloco, preservando o formato."""
    largura = max(len(linha) for linha in linhas)
    return [linha.ljust(largura).center(LARGURA_TELA).rstrip() for linha in linhas]

def imprimir_arte(linhas: list[str]) -> None:
    """Imprime uma arte ASCII centralizada na tela."""
    for linha in centralizar_arte(linhas):
        print(linha)

# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------

def desenhar_inicio(quadro: int) -> None:
    """Desenha um quadro da tela inicial (caneca com fumaça animada)."""
    limpar_tela()
    print("=" * LARGURA_TELA)
    print("S A C - C A F E T E R I A".center(LARGURA_TELA))
    print("Sistema de Autoatendimento Inteligente".center(LARGURA_TELA))
    print("=" * LARGURA_TELA)
    print()
    imprimir_arte(FUMACA[quadro % len(FUMACA)] + CANECA)
    print()
    print("Bem-vindo(a) ao nosso Totem!".center(LARGURA_TELA))
    print("Cafés fresquinhos, feitos na hora.".center(LARGURA_TELA))
    print()

def tela_inicial() -> None:
    """Tela de boas-vindas com animação de fumaça saindo da caneca."""
    quadros = QUADROS_ANIMACAO if ANIMAR else 1
    for quadro in range(quadros):
        desenhar_inicio(quadro)
        if ANIMAR:
            time.sleep(PAUSA_QUADRO_S)
    input("      [ Pressione ENTER para iniciar o seu pedido ]")
    print("\nCarregando o sistema...")
    time.sleep(1)

def desenhar_faixa_categorias() -> None:
    """Mostra os ícones de todas as categorias lado a lado."""
    artes = []
    for id_categoria, categoria in CARDAPIO.items():
        largura = max(len(linha) for linha in categoria["arte"])
        # rótulo [n] centralizado embaixo de cada ícone
        artes.append(categoria["arte"] + ["", f"[{id_categoria}]".center(largura)])
    faixa = lado_a_lado(artes)
    if len(faixa[0]) <= LARGURA_TELA:  # só desenha se couber na tela
        imprimir_arte(faixa)
        print()

def tela_catalogo(carrinho: list[Produto]) -> None:
    """Menu de categorias. Retorna quando o pedido termina ou é cancelado."""
    recusadas: set[int] = set()  # sugestões que o cliente já recusou neste pedido
    while True:
        limpar_tela()
        cabecalho("C A R D Á P I O")
        desenhar_faixa_categorias()
        print("Categorias:")
        # categorias geradas a partir do CARDAPIO
        for id_categoria, categoria in CARDAPIO.items():
            print(f"[{id_categoria}] {categoria['nome']}")
        print(f"[{OPCAO_CARRINHO}] {ICONE_CARRINHO} Ver Carrinho e Finalizar")
        print("[0] Cancelar Pedido / Voltar ao Início")
        # avisa sobre o combo
        print(f"\nDica: monte combos e ganhe {PERCENTUAL_COMBO}% de desconto no 2º item!")

        validas = {"0", OPCAO_CARRINHO, *CARDAPIO}
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
            if tela_carrinho(carrinho, recusadas) == "inicio":
                break
        else:
            tela_itens(opcao, carrinho)

def tela_itens(id_categoria: str, carrinho: list[Produto]) -> None:
    """Lista os produtos de uma categoria e adiciona o escolhido ao carrinho."""
    categoria = CARDAPIO[id_categoria]
    produtos = {str(p.codigo): p for p in categoria["itens"]}

    limpar_tela()
    cabecalho(f"--- {categoria['nome'].upper()} ---")
    imprimir_arte(categoria["arte"])
    print()

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

def tela_carrinho(carrinho: list[Produto], recusadas: set[int] | None = None) -> str:
    """Mostra o carrinho. Retorna 'catalogo' (voltar) ou 'inicio' (pedido encerrado)."""
    if recusadas is None:
        recusadas = set()

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
        desconto = calcular_desconto(carrinho)
        total = subtotal - desconto
        print(f"\nSubtotal: R$ {subtotal:.2f}")

        if desconto > 0:
            for rec, qtd in listar_combos(carrinho):
                sugerido = buscar_produto(rec.sugestao)
                if sugerido is None:
                    continue
                rotulo = f"Combo: {sugerido.nome}" + (f" x{qtd}" if qtd > 1 else "")
                print(f"{rotulo.ljust(30, '.')} -R$ {desconto_do_combo(rec, qtd):.2f}")
            print(f"\nTOTAL COM DESCONTO: R$ {total:.2f}")
        print("-" * LARGURA_TELA)

        rec = proxima_sugestao(carrinho, recusadas)
        if rec is not None:
            gatilho = buscar_produto(rec.gatilho)
            sugestao = buscar_produto(rec.sugestao)
            if gatilho is not None and sugestao is not None:
                preco_combo = sugestao.preco - desconto_do_combo(rec)
                print("- SUGESTÃO DA CASA -")
                print(f"Notamos que você pediu: {gatilho.nome}!")
                print(rec.mensagem)
                resposta = ler_opcao(
                    f"\nDeseja adicionar 1x {sugestao.nome} por R$ {preco_combo:.2f} "
                    f"({PERCENTUAL_COMBO}% off no combo)? (S/N): ",
                    {"S", "N"},
                )
                if resposta == "S":
                    carrinho.append(sugestao)
                    print(f"\n-> {sugestao.nome} adicionado com sucesso!")
                    input("Pressione ENTER para atualizar o carrinho...")
                    continue  # recalcula o total (e pode surgir outra sugestão)
                recusadas.add(sugestao.codigo)  # não pergunta de novo neste pedido

        print("\n[1] Finalizar Pedido e Pagar")
        print("[2] Remover um item")  # [NOVO D1]
        print("[0] Voltar para o Cardápio")

        opcao = ler_opcao("\nEscolha uma opção: ", {"0", "1", "2"})

        if opcao == "1":
            tela_pagamento(carrinho, total)
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
    desconto: Decimal = Decimal("0.00"),
    numero_pedido: int | None = None,
) -> bool:
    """Acrescenta o recibo ao arquivo. Retorna False se não conseguiu gravar.

    `total` é o valor pago (já com desconto). [G3] Mostra subtotal e desconto.
    """
    if numero_pedido is None:
        numero_pedido = proximo_numero_pedido()
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linhas = [
        "=" * LARGURA_RECIBO,
        "           SAC - CAFETERIA",
        f"           {agora}",
        f"           PEDIDO Nº {numero_pedido:04d}",
        "=" * LARGURA_RECIBO,
        "ITENS DO PEDIDO:",
    ]
    for produto, qtd in agrupar_itens(carrinho):
        linhas.append(f"- {qtd}x {produto.nome.ljust(20, '.')} R$ {produto.preco * qtd:.2f}")
    linhas.append("-" * LARGURA_RECIBO)
    if desconto > 0:
        linhas.append(f"SUBTOTAL:        R$ {total + desconto:.2f}")
        linhas.append(f"DESCONTO COMBO: -R$ {desconto:.2f}")
    linhas += [
        f"TOTAL PAGO:      R$ {total:.2f}",
        f"PAGAMENTO VIA:   {forma_pagamento}",
        "-" * LARGURA_RECIBO,
        f"TEMPO ESTIMADO:  {tempo_estimado} minutos",
        "=" * LARGURA_RECIBO,
        "Obrigado pela preferência!",
        "", "", "",
    ]
    try:
        with open(ARQUIVO_RECIBO, "a", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas))
    except OSError:
        return False
    return True

def tela_final(numero_pedido: int, tempo_estimado: int, recibo_ok: bool) -> None:
    """[NOVO G2] Tela de confirmação do pedido, com a caneca e o número da senha."""
    limpar_tela()
    cabecalho("P E D I D O  C O N F I R M A D O")
    print()
    imprimir_arte(FUMACA[0] + CANECA)
    print()
    print(f"SEU PEDIDO: Nº {numero_pedido:04d}".center(LARGURA_TELA))
    print(f"Tempo estimado: {tempo_estimado} minutos".center(LARGURA_TELA))
    print("(Cálculo baseado na fila atual e nos itens)".center(LARGURA_TELA))
    print()
    if recibo_ok:
        print(f"Recibo gerado em '{ARQUIVO_RECIBO.name}'.".center(LARGURA_TELA))
    else:
        print("Não foi possível gravar o recibo. Chame um atendente.".center(LARGURA_TELA))
    print("Aguarde ser chamado no balcão. Obrigado!".center(LARGURA_TELA))
    print("=" * LARGURA_TELA)

def tela_pagamento(carrinho: list[Produto], total: Decimal) -> bool:
    """Processa o pagamento de `total` (já com desconto). True se pago, False se cancelado."""
    desconto = calcular_desconto(carrinho)

    limpar_tela()
    cabecalho("F I N A L I Z A R")
    if desconto > 0:
        print(f"Desconto de combos: -R$ {desconto:.2f}")
    print(f"TOTAL A PAGAR: R$ {total:.2f}\n")
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

    time.sleep(1.5)  # deixa o cliente ler a confirmação antes da tela final
    tempo_estimado = estimar_tempo(len(carrinho))
    numero_pedido = proximo_numero_pedido()
    recibo_ok = gerar_recibo(
        carrinho, total, forma_pagamento, tempo_estimado, desconto, numero_pedido
    )
    tela_final(numero_pedido, tempo_estimado, recibo_ok)

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
    except (KeyboardInterrupt, EOFError):
        # se alguém tentar quebrar o totem com Ctrl+C, o terminal limpa e desliga em segurança
        limpar_tela()
        print("\n\nSistema encerrado de forma segura pelo Administrador.\n\n")

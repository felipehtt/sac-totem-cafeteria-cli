"""Testes do totem. Rode com: python -m pytest test_totem.py -q

Os testes de fluxo simulam o teclado (input) e não dependem de fixtures do
pytest, então também rodam com qualquer outro executor de testes.
"""
import contextlib
import io
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import totem
from totem import (
    CARDAPIO,
    COD_CAFE,
    COD_PAO_QUEIJO,
    LARGURA_TELA,
    MAX_ITENS,
    OPCAO_CARRINHO,
    RECOMENDACOES,
    agrupar_itens,
    buscar_produto,
    calcular_desconto,
    calcular_total,
    centralizar_arte,
    deve_sugerir_venda_casada,
    estimar_tempo,
    gerar_recibo,
    lado_a_lado,
    listar_combos,
    proxima_sugestao,
)

CAFE = buscar_produto(COD_CAFE)
PAO = buscar_produto(COD_PAO_QUEIJO)


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------
def _rodar(inputs, funcao, *args, recibo=None):
    """Executa `funcao` simulando o teclado. Retorna (resultado, texto_impresso).

    Falha se o código pedir mais entradas do que o previsto ou se sobrar alguma.
    """
    saida = io.StringIO()
    with contextlib.ExitStack() as stack:
        entrada = stack.enter_context(patch("builtins.input", side_effect=inputs))
        stack.enter_context(patch("totem.limpar_tela"))
        stack.enter_context(patch("totem.time.sleep"))
        stack.enter_context(patch("totem.getpass.getpass", return_value="1234"))
        if recibo is not None:
            stack.enter_context(patch.object(totem, "ARQUIVO_RECIBO", recibo))
        stack.enter_context(contextlib.redirect_stdout(saida))
        resultado = funcao(*args)
    assert entrada.call_count == len(inputs), "sobraram entradas não consumidas"
    return resultado, saida.getvalue()


# ---------------------------------------------------------------------------
# Regras de negócio (funções puras)
# ---------------------------------------------------------------------------
def test_calcular_total_usa_decimal():
    assert calcular_total([CAFE, PAO, PAO]) == Decimal("14.00")


def test_calcular_total_carrinho_vazio():
    assert calcular_total([]) == Decimal("0.00")


def test_sugere_pao_quando_so_tem_cafe():
    assert deve_sugerir_venda_casada([CAFE]) is True


def test_nao_sugere_se_ja_tem_pao():
    assert deve_sugerir_venda_casada([CAFE, PAO]) is False


def test_nao_sugere_sem_cafe():
    assert deve_sugerir_venda_casada([PAO]) is False


def test_nao_sugere_com_carrinho_cheio():
    assert deve_sugerir_venda_casada([CAFE] * MAX_ITENS) is False


def test_estimar_tempo():
    # 2 base + 2 itens * 1.5 + 3 fila * 2 = 11
    assert estimar_tempo(2) == 11


def test_agrupar_itens_mantem_ordem_e_conta():
    assert agrupar_itens([CAFE, PAO, CAFE]) == [(CAFE, 2), (PAO, 1)]


# ---------------------------------------------------------------------------
# Recomendações
# ---------------------------------------------------------------------------
def test_proxima_sugestao_cafe_aponta_para_pao():
    rec = proxima_sugestao([CAFE])
    assert rec is not None
    assert rec.sugestao == COD_PAO_QUEIJO


def test_proxima_sugestao_respeita_recusadas():
    assert proxima_sugestao([CAFE], {COD_PAO_QUEIJO}) is None


def test_misto_quente_sugere_suco_de_laranja():
    rec = proxima_sugestao([buscar_produto(32)])
    assert rec is not None
    assert rec.sugestao == 23


def test_recusar_uma_sugestao_libera_a_proxima():
    misto = buscar_produto(32)
    assert proxima_sugestao([CAFE, misto]).sugestao == COD_PAO_QUEIJO
    assert proxima_sugestao([CAFE, misto], {COD_PAO_QUEIJO}).sugestao == 23


def test_recomendacoes_apontam_para_produtos_existentes():
    for rec in RECOMENDACOES:
        assert buscar_produto(rec.gatilho) is not None
        assert buscar_produto(rec.sugestao) is not None
        assert rec.gatilho != rec.sugestao


def test_cada_item_e_sugerido_por_uma_unica_regra():
    # o desconto de combo depende dessa regra (evita desconto duplicado)
    sugeridos = [rec.sugestao for rec in RECOMENDACOES]
    assert len(sugeridos) == len(set(sugeridos))


# ---------------------------------------------------------------------------
# Combos e desconto
# ---------------------------------------------------------------------------
def test_sem_combo_sem_desconto():
    assert calcular_desconto([CAFE]) == Decimal("0.00")
    assert calcular_desconto([]) == Decimal("0.00")


def test_desconto_combo_cafe_e_pao():
    # 10% sobre o Pão de Queijo (4.50) = 0.45
    assert calcular_desconto([CAFE, PAO]) == Decimal("0.45")


def test_combo_conta_o_menor_numero_de_unidades():
    assert calcular_desconto([CAFE, CAFE, PAO]) == Decimal("0.45")
    assert calcular_desconto([CAFE, PAO, PAO]) == Decimal("0.45")
    assert calcular_desconto([CAFE, CAFE, PAO, PAO]) == Decimal("0.90")


def test_listar_combos():
    combos = listar_combos([CAFE, CAFE, PAO])
    assert [(rec.gatilho, rec.sugestao, qtd) for rec, qtd in combos] == [(11, 31, 1)]


def test_desconto_nunca_passa_do_subtotal():
    carrinho = [p for c in CARDAPIO.values() for p in c["itens"]]
    assert Decimal("0.00") <= calcular_desconto(carrinho) < calcular_total(carrinho)


# ---------------------------------------------------------------------------
# Cardápio e arte
# ---------------------------------------------------------------------------
def test_codigos_do_cardapio_sao_unicos():
    codigos = [p.codigo for c in CARDAPIO.values() for p in c["itens"]]
    assert len(codigos) == len(set(codigos))


def test_codigo_do_produto_comeca_com_o_numero_da_categoria():
    # padrão do cardápio: 1x = quentes, 2x = geladas, 3x = comidas, 4x = doces
    for id_categoria, categoria in CARDAPIO.items():
        for produto in categoria["itens"]:
            assert str(produto.codigo).startswith(id_categoria), produto.nome


def test_bolo_de_cenoura_esta_em_doces():
    nomes_doces = [p.nome for p in CARDAPIO["4"]["itens"]]
    nomes_comidas = [p.nome for p in CARDAPIO["3"]["itens"]]
    assert "Bolo de Cenoura" in nomes_doces
    assert "Bolo de Cenoura" not in nomes_comidas


def test_nomes_cabem_na_coluna_de_20_caracteres():
    for categoria in CARDAPIO.values():
        for produto in categoria["itens"]:
            assert len(produto.nome) <= 20


def test_opcao_do_carrinho_acompanha_o_numero_de_categorias():
    assert OPCAO_CARRINHO == str(len(CARDAPIO) + 1)
    assert OPCAO_CARRINHO not in CARDAPIO


def test_lado_a_lado_alinha_pela_base():
    assert lado_a_lado([["ab", "cd"], ["e"]], espaco=2) == ["ab    ", "cd  e "]


def test_faixa_de_categorias_cabe_na_tela():
    faixa = lado_a_lado([c["arte"] for c in CARDAPIO.values()])
    assert max(len(linha) for linha in faixa) <= LARGURA_TELA


def test_centralizar_arte_nao_passa_da_largura():
    artes = [c["arte"] for c in CARDAPIO.values()] + [totem.CANECA]
    for arte in artes:
        for linha in centralizar_arte(arte):
            assert len(linha) <= LARGURA_TELA


# ---------------------------------------------------------------------------
# Recibo
# ---------------------------------------------------------------------------
def test_recibo_grava_numero_itens_e_desconto():
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "recibo.txt"
        with patch.object(totem, "ARQUIVO_RECIBO", caminho):
            ok1 = gerar_recibo([CAFE, PAO], Decimal("9.05"), "PIX", 11, Decimal("0.45"))
            ok2 = gerar_recibo([CAFE], Decimal("5.00"), "Cartão", 8)
        texto = caminho.read_text(encoding="utf-8")
    assert ok1 and ok2
    assert "PEDIDO Nº 0001" in texto
    assert "PEDIDO Nº 0002" in texto
    assert "SUBTOTAL:        R$ 9.50" in texto
    assert "DESCONTO COMBO: -R$ 0.45" in texto
    assert "TOTAL PAGO:      R$ 9.05" in texto


def test_recibo_sem_desconto_nao_mostra_linha_de_desconto():
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "recibo.txt"
        with patch.object(totem, "ARQUIVO_RECIBO", caminho):
            gerar_recibo([CAFE], Decimal("5.00"), "PIX", 8)
        texto = caminho.read_text(encoding="utf-8")
    assert "DESCONTO" not in texto


def test_recibo_retorna_false_quando_nao_consegue_gravar():
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "pasta_inexistente" / "recibo.txt"
        with patch.object(totem, "ARQUIVO_RECIBO", caminho):
            assert gerar_recibo([CAFE], Decimal("5.00"), "PIX", 8) is False


# ---------------------------------------------------------------------------
# Fluxos de ponta a ponta (teclado simulado)
# ---------------------------------------------------------------------------
def test_fluxo_completo_com_combo_e_pix():
    carrinho = []
    # 1 (quentes) > 11 (café) > ENTER > 5 (carrinho) > S (aceita pão) > ENTER
    # > 1 (finalizar) > 2 (PIX) > ENTER (confirma PIX) > ENTER (volta ao início)
    inputs = ["1", "11", "", "5", "S", "", "1", "2", "", ""]
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "recibo.txt"
        _, saida = _rodar(inputs, totem.tela_catalogo, carrinho, recibo=caminho)
        texto = caminho.read_text(encoding="utf-8")
    assert carrinho == []  # carrinho limpo para o próximo cliente
    assert "PEDIDO Nº 0001" in texto
    assert "DESCONTO COMBO: -R$ 0.45" in texto
    assert "TOTAL PAGO:      R$ 9.05" in texto
    assert "PAGAMENTO VIA:   PIX" in texto
    assert "SEU PEDIDO: Nº 0001" in saida  # tela final


def test_fluxo_pagamento_com_cartao():
    carrinho = [buscar_produto(12)]  # Cappuccino
    # carrinho: N (recusa croissant) > 1 (finalizar) > 1 (cartão) > ENTER final
    inputs = ["N", "1", "1", ""]
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "recibo.txt"
        resultado, _ = _rodar(inputs, totem.tela_carrinho, carrinho, recibo=caminho)
        texto = caminho.read_text(encoding="utf-8")
    assert resultado == "inicio"
    assert "PAGAMENTO VIA:   Cartão" in texto
    assert "TOTAL PAGO:      R$ 8.00" in texto


def test_cancelar_no_pagamento_nao_gera_recibo():
    carrinho = []
    # 1 > 11 > ENTER > 5 (carrinho) > N (recusa pão) > 1 (finalizar) > 0 (cancela)
    inputs = ["1", "11", "", "5", "N", "1", "0"]
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "recibo.txt"
        _rodar(inputs, totem.tela_catalogo, carrinho, recibo=caminho)
        existe = caminho.exists()
    assert carrinho == []
    assert existe is False


def test_carrinho_vazio_volta_ao_cardapio_e_nao_ao_inicio():
    carrinho = []
    # 5 (carrinho vazio) > ENTER > continua no cardápio > 0 (cancela)
    inputs = [OPCAO_CARRINHO, "", "0"]
    _, saida = _rodar(inputs, totem.tela_catalogo, carrinho)
    assert "Seu carrinho está vazio." in saida
    assert saida.count("C A R D Á P I O") == 2  # cardápio exibido de novo


def test_limite_de_itens_bloqueia_novo_produto():
    carrinho = [CAFE] * MAX_ITENS
    _, saida = _rodar(["11", ""], totem.tela_itens, "1", carrinho)
    assert len(carrinho) == MAX_ITENS
    assert "Limite máximo" in saida


def test_aceitar_sugestao_respeita_o_limite():
    carrinho = [CAFE] * MAX_ITENS
    # sem sugestão (carrinho cheio): só aparecem as opções do carrinho > 0 volta
    resultado, saida = _rodar(["0"], totem.tela_carrinho, carrinho)
    assert resultado == "catalogo"
    assert "SUGESTÃO DA CASA" not in saida
    assert len(carrinho) == MAX_ITENS


def test_remover_item_e_nao_repetir_sugestao_recusada():
    carrinho = [CAFE, CAFE]
    # N (recusa pão) > 2 (remover) > 1 (café) > ENTER > 0 (voltar)
    resultado, saida = _rodar(["N", "2", "1", "", "0"], totem.tela_carrinho, carrinho)
    assert resultado == "catalogo"
    assert carrinho == [CAFE]
    assert saida.count("SUGESTÃO DA CASA") == 1  # não perguntou de novo


def test_opcao_invalida_pede_novamente():
    # "9" é inválido; depois "0" cancela
    _, saida = _rodar(["9", "0"], totem.tela_catalogo, [])
    assert "Opção inválida" in saida

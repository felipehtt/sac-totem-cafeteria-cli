# SAC - Cafeteria (Totem de Autoatendimento em Terminal)

Simulador de totem de autoatendimento para cafeteria, feito em Python puro (sem
dependências externas). O cliente navega pelo cardápio, monta o pedido, recebe
sugestões de combos com desconto, paga (simulado) e recebe um recibo em arquivo.

```
          )   (   )
         (   )   (
          )   (   )
       .------------.
       |   S A C    |==.
       |            |  |
       \            /==' 
        `-.______.-'
      \______________/
```

## Requisitos

- Python 3.10 ou superior (testado com 3.12 e 3.14)
- Terminal com fonte monoespaçada (Windows Terminal, PowerShell, bash, etc.)

## Como rodar

```bash
python totem.py
```

Para encerrar o totem com segurança, use `Ctrl+C`.

## Como testar

```bash
pip install -r requirements-dev.txt
python -m pytest test_totem.py -q
```

> **Windows:** use sempre `python -m pytest`. O comando `pytest` sozinho pode não ser
> reconhecido se a pasta `Scripts` do Python não estiver no PATH. Rode o comando
> **dentro da pasta do projeto**, senão o pytest varre outras pastas do computador.

Os testes cobrem as regras de negócio (total, combos, desconto, sugestões, tempo
estimado), o recibo e os fluxos completos do totem com o teclado simulado.

## Funcionalidades

- **Cardápio com 4 categorias:** Bebidas Quentes, Bebidas Geladas, Comidas e Doces,
  cada uma com seu ícone em arte ASCII.
- **Carrinho** com itens agrupados (`3x Café Expresso`), remoção de itens e limite de
  20 itens por pedido.
- **Recomendações:** ao pedir certos itens, o totem sugere um complemento
  (ex.: Café Expresso → Pão de Queijo). Se o cliente recusar, a sugestão não é repetida
  no mesmo pedido.
- **Combos com desconto:** quando o carrinho tem os dois itens de uma recomendação, o
  item sugerido ganha **10% de desconto** (por combo completo).
- **Pagamento simulado** por Cartão ou PIX (com QR Code em arte).
- **Tempo estimado de preparo:** 2 min base + 1,5 min por item + fila simulada.
- **Recibo** acumulado em `recibo.txt`, com número do pedido, itens, subtotal, desconto,
  total e forma de pagamento.
- **Tela inicial animada** (fumaça saindo da caneca) e tela final com o número do pedido.

## Estrutura do projeto

| Arquivo | Para que serve |
|---|---|
| `totem.py` | Todo o código do totem (regras, telas e `main`) |
| `test_totem.py` | Testes automatizados |
| `requirements-dev.txt` | Ferramentas de desenvolvimento (pytest, ruff) |
| `pyproject.toml` | Configuração do pytest e do ruff |
| `recibo.txt` | Gerado em execução; não é versionado |

Dentro do `totem.py`, as funções "puras" (sem `print`/`input`) ficam separadas das
telas: `calcular_total`, `calcular_desconto`, `listar_combos`, `proxima_sugestao`,
`estimar_tempo` e `agrupar_itens`. É isso que permite testá-las sem simular o teclado.

## Como personalizar

**Adicionar um produto:** inclua um `Produto(codigo, nome, Decimal("preço"))` na lista
`itens` de uma categoria em `CARDAPIO`. O código precisa ser único e o nome ter no
máximo 20 caracteres (há testes que verificam isso).

**Adicionar uma categoria:** crie uma nova entrada em `CARDAPIO` (`nome`, `arte`,
`itens`). A opção do carrinho se ajusta sozinha. A faixa de ícones só aparece se todas
as artes couberem em 50 colunas.

**Adicionar uma recomendação:** inclua uma linha em `RECOMENDACOES`:

```python
Recomendacao(gatilho=12, sugestao=33, mensagem="Cappuccino e Croissant são uma dupla clássica.")
```

Regra importante: cada produto deve aparecer como `sugestao` em **uma única** regra,
para que o desconto do combo nunca seja aplicado duas vezes ao mesmo item.

**Mudar o desconto:** altere `DESCONTO_COMBO` (por padrão `Decimal("0.10")`).

## Limitações conhecidas

- O pagamento é **apenas uma simulação**. Em um totem real, a senha do cartão é digitada
  na maquininha/TEF e nunca passa pela aplicação (exigência do PCI-DSS), e o PIX exige
  integração com um provedor de pagamentos.
- O número do pedido é calculado contando os recibos em `recibo.txt`; se o arquivo for
  apagado, a numeração recomeça em 1.
- O tempo de preparo usa uma fila fixa simulada (3 pedidos), não uma fila real.

## Qualidade de código

Opcional, com as ferramentas de `requirements-dev.txt`:

```bash
python -m ruff check .
python -m ruff format .
```
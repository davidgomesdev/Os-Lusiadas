# Os Lusíadas

*Os Lusíadas*, de Luís de Camões (1572), num leitor de estrofes — um canto por
página, com a leitura guardada onde a deixaste.

## Estrutura

```
scripts/scrape.py      recolhe os textos de oslusiadas.org
scripts/build_site.py  gera as páginas de cada canto + o índice
texts/                 um .txt por estrofe, e um .txt por canto
docs/                  o site publicado no GitHub Pages
  data/canto-<n>.json  os dados que o leitor consome
```

## Recolher os textos

O site é renderizado no servidor e cada estrofe vive em `/<canto>/<estrofe>.html`,
com o canto em numeração romana minúscula — por exemplo
`https://oslusiadas.org/i/17.html`. O scraper descobre as estrofes de cada canto
a partir das ligações que o botão *Estâncias / Estrofes* abre, e depois recolhe
cada uma.

```bash
python3 scripts/scrape.py                 # todos os cantos
python3 scripts/scrape.py --cantos 1-3    # só alguns
python3 scripts/scrape.py --delay 1       # mais devagar com o servidor
python3 scripts/build_site.py             # regenera as páginas
```

Sem dependências — só a biblioteca padrão do Python 3.

Em alternativa, corre o workflow **Scrape oslusiadas.org** em Actions → *Run
workflow*: recolhe os textos num runner do GitHub e faz commit do resultado.

## Publicar

Em *Settings → Pages*, escolhe **GitHub Actions** como origem. Cada push para
`main` reconstrói e publica o site.

## O leitor

- Deslizar na horizontal, setas ←/→, espaço, ou tocar nas margens.
- A estrofe atual fica guardada em `localStorage`, por canto; o índice mostra
  um atalho *Continuar a leitura*.
- O endereço acompanha a estrofe (`canto-1.html#17`), por isso dá para partilhar
  uma estrofe específica.
- Tema claro/escuro conforme o sistema.

## Fidelidade ao texto de origem

O objectivo é arquivar o que a fonte publica, e não emendá-la. Nada é
reescrito, completado ou removido a partir de outra edição: os ficheiros em
`texts/` são o que a página serviu.

`python3 scripts/verify.py` confere a recolha — contagens por canto contra as
edições correntes, numeração contígua, e estrofes que não tenham oito versos.
Passa com 1102 estrofes, com cinco a assinalar.

### As cinco estrofes que não têm oito versos

Uma estrofe de *Os Lusíadas* é uma oitava. Cinco fogem disso, e em nenhum caso
por falha do scraper — todas reproduzem a página de origem tal como ela está.

**Quatro trazem uma legenda editorial dentro do painel dos versos.** Os oito
versos estão lá; o que sobra é uma anotação do site, sem marcação nenhuma que a
distinga do verso — mesmo bloco, separada apenas por `<br>`. Por isso não há
maneira fiável de a separar automaticamente, e fica onde a fonte a pôs:

| Estrofe | Versos | Legenda | Posição |
| --- | --- | --- | --- |
| I.53 | 8 | «Informações. A Ilha de Moçambique.» | depois |
| I.58 | 8 | «Prepara-se a Armada para Receber a…» | depois |
| VIII.61 | 8 | «Fala do Samorim ao Gama» | antes |
| VIII.64 | 8 | «Resposta do Gama» | antes |

**Uma está mesmo incompleta na origem.** A II.19 tem sete versos em
oslusiadas.org — falta-lhe um. Não foi preenchido: escrevê-lo a partir de outra
edição seria inventar dados que a fonte não deu.

Se algum dia se quiser separar as legendas do verso, o caminho honesto é uma
tabela explícita para estas quatro (a posição de cada uma está acima), e não
uma heurística a adivinhar sobre as 1102.

O texto é de 1572 e está em domínio público.

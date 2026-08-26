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

O texto é de 1572 e está em domínio público.

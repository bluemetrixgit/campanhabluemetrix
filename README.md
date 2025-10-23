# Campanha de Captação — NET (R$)

App Streamlit para acompanhamento da campanha de captação com **captação líquida (NET)** em **R$**, conversão automática **USD→BRL**, suporte a **D‑1**, filtros por **Escritório/Corretora/UF** e download dos resultados.

![screenshot](docs/screenshot.png)

---

## ✨ Principais recursos
- **Leitura automática via repositório** (sem upload manual):
  - `dados/Campanha Captação.xlsx` (aba `Planilha1`)
  - `dados/FX Dolar.xlsx` (`Date`, `USDBRL`)
  - `logo.branca.*` (PNG/JPG/JPEG/WEBP) na raiz
- **NET real**: entradas – saídas (considera clientes que zeraram/migraram).
- **Conversão USD→BRL** para corretoras internacionais (XP Internacional, Pershing, Interactive Brokers, Avenue).
- **D‑1 inteligente**: qualquer rótulo com “D-1” é resolvido para **ontem (America/Sao_Paulo)**; se a data não existir na tabela de FX, usa o **dia útil anterior**.
- **Dashboard visual** (tema escuro, cards, badges, gráfico de ranking).
- **Filtros**: Escritório, Corretora e UF (afetam KPIs, ranking e diagnóstico).
- **Download**: Excel com `Painel_NET_R$` e `Ranking_Assessores_NET`.

---

## 📁 Estrutura sugerida do repositório

```
/
├─ app_campanha_net.py
├─ requirements.txt
├─ README.md
├─ logo.branca.png                 # sua logo (pode ser .jpg/.jpeg/.webp)
└─ dados/
   ├─ Campanha Captação.xlsx       # fonte consolidada (aba Planilha1)
   └─ FX Dolar.xlsx                # tabela de câmbio (Date, USDBRL)
```

> Você pode usar outro nome/extensão para a logo: `logo.branca`, `logo.branca.png`, `logo.branca.jpg`, `logo.branca.jpeg` ou `logo.branca.webp`.
> O app procura automaticamente nesses nomes na raiz do projeto.

---

## 🔧 Requisitos

- Python 3.10+ (recomendado)
- Dependências listadas em `requirements.txt`

Instalação:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## ▶️ Executar localmente

```bash
streamlit run app_campanha_net.py
```

Acesse: `http://localhost:8501`

---

## ☁️ Deploy (Streamlit Community Cloud)

1. Crie um repositório no GitHub com esta estrutura.
2. Suba **todos os arquivos** (incluindo `dados/*.xlsx` e `logo.branca.*`).
3. No Streamlit Cloud, crie um app apontando para `app_campanha_net.py` e use o `requirements.txt` deste projeto.
4. Opcional: adicione um print do app em `docs/screenshot.png` (não é obrigatório).

> ⚠️ O app **não** usa uploads — ele lê os arquivos do **próprio repositório** na pasta `dados`.  
> Para atualizar dados, basta **commitar** versões novas dos XLSX.

---

## 🧾 Esquema dos arquivos

### 1) `dados/Campanha Captação.xlsx` (aba `Planilha1`)

**Colunas obrigatórias:**
- `Corretora`
- `Cliente`
- `Conta`
- `Escritório`
- `UF`
- `Assessor`
- `Carteira`
- **Baseline**: coluna **`30/06/2025`** (valor numérico)
- **Coluna atual**: 
  - **`... (D-1)`** (qualquer coluna com “D-1” no nome), **ou**
  - a **última coluna de data** no formato `dd/mm/aaaa` (se não existir D‑1).

> O app converte tudo para numérico, tratando vazios como 0.

### 2) `dados/FX Dolar.xlsx`

**Colunas esperadas:**
- `Date` (data no formato excel/data)
- `USDBRL` (taxa, número)

> Se sua planilha usar `Data` ao invés de `Date`, o app reconhece.  
> A busca de taxa é feita pela **data exata**; se não houver, pega o **dia útil anterior**.

---

## 📐 Lógica de cálculo

- `PL_30_06_2025_BRL` e `PL_Atual_BRL` convertem valores USD→BRL quando a **Corretora** está em:
  - `XP Internacional`, `Pershing`, `Interactive Brokers`, `Avenue` (ajuste em `USD_BROKERS` no código, se necessário)
- `Delta_BRL = PL_Atual_BRL – PL_30_06_2025_BRL`
- **NET** (captação líquida) é a **soma** de `Delta_BRL` por escopo (geral/assessor/filtro).
- Quando a coluna atual contém **“D-1”**, é resolvida para **ontem** na timezone `America/Sao_Paulo` para buscar o FX.

---

## ⚙️ Parâmetros editáveis (no topo do arquivo)

- `BASELINE_COL_STR = "30/06/2025"`  
- `PERIODO_INICIO`, `PERIODO_FIM`, `GOAL_META`
- `LOGO_CANDIDATES`, `FILE_CAMPANHA`, `FILE_FX`
- `USD_BROKERS` (conjunto de corretoras em USD)

---

## 🔍 Filtros

- **Escritório**, **Corretora** e **UF** (aplicam‑se aos KPIs, ranking e diagnóstico).

---

## 🛠️ Troubleshooting

- **Logo não aparece**: confirme que um dos arquivos existe na raiz (`logo.branca.png`, por exemplo).  
- **Erro “arquivo não encontrado”**: verifique se os XLSX estão dentro de `dados/` com os nomes corretos.  
- **FX não encontrado para D‑1**: o app usa **ontem**; se essa data não existir no FX, ele usa o **dia útil anterior**.  
- **Nomes cortados no ranking**: o gráfico já tem margens largas; caso precise, reduza o número de linhas no filtro ou aumente a largura da página do navegador.

---

## 📄 Licença
Defina a licença do projeto (ex.: MIT) conforme sua preferência.

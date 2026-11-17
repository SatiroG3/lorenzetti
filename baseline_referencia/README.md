# Baseline de Referência — Lorenzetti Showers

## 1. Objetivo

Esta pasta reúne os arquivos de referência utilizados para construir e validar uma baseline do Lorenzetti Showers a partir de uma amostra de eventos Zee.

A baseline organiza informações dos clusters reconstruídos e dos clusters truth, permitindo que execuções futuras sejam comparadas com esta referência em uma etapa posterior de testes de regressão.

## 2. Estrutura de diretórios

```text
baseline_referencia/
├── data/
│   ├── root/
│   │   ├── Zee.EVT.root
│   │   ├── Zee.HIT.root
│   │   ├── Zee.ESD.root
│   │   ├── Zee.AOD.root
│   │   └── Zee.NTUPLE.root
│   │
│   └── baseline_output/
│       ├── baseline_clusters.csv
│       ├── baseline_eventos.csv
│       └── baseline_metadata.json
│
├── logs/
│   ├── geracao.log
│   ├── simulacao.log
│   ├── digitizacao.log
│   ├── reconstrucao.log
│   └── ntuple.log
│
├── scripts/
│   └── extrai_baseline_atualizado.py
│
├── notebooks/
│   └── extrai_baseline_atualizado.ipynb
│
└── README.md
```

Os nomes dos arquivos de log devem corresponder aos arquivos efetivamente preservados nesta pasta. O extrator utiliza diretamente o NTUPLE e o log de reconstrução.

## 3. Dados de entrada

### Arquivo ROOT

O extrator lê:

```text
data/root/Zee.NTUPLE.root
```

A árvore ROOT utilizada é:

```text
physics
```

### Log de reconstrução

O extrator também lê:

```text
logs/reconstrucao.log
```

Esse log é utilizado para recuperar as quantidades de células dos clusters reconstruídos e dos clusters truth.

Os demais arquivos ROOT e logs são mantidos como registros das etapas da cadeia de processamento.

## 4. Execução do extrator

O script oficial de extração está localizado em:

```text
scripts/extrai_baseline_atualizado.py
```

A partir da raiz do repositório Lorenzetti, execute:

```bash
python baseline_referencia/scripts/extrai_baseline_atualizado.py
```

O script determina os caminhos a partir da localização do próprio arquivo, lê os dados de entrada e grava os resultados em:

```text
baseline_referencia/data/baseline_output/
```

Os arquivos de saída são criados ou atualizados a cada execução.

## 5. Arquivos produzidos

### `baseline_clusters.csv`

Contém uma linha por cluster reconstruído, com as variáveis disponíveis no NTUPLE e informações adicionais extraídas dos logs.

Entre os campos registrados estão:

- Identificação da entrada, execução e evento;
- Energia e variáveis do cluster reconstruído;
- Vetor `Rings`;
- Energia e vetor `Truth_Rings`;
- Indicador `truth_available`;
- Índices sequenciais do evento e do cluster reconstruído;
- Quantidade de células reconstruídas (`n_cells_reco`);
- Índice do cluster truth associado (`truth_cluster_index`);
- Quantidade de células truth associadas (`n_cells_truth`).

Quando não existe associação truth para um cluster reconstruído, `truth_cluster_index` fica vazio e `n_cells_truth` recebe zero.

### `baseline_eventos.csv`

Contém informações agregadas por evento, incluindo:

- Identificação sequencial, `RunNumber` e `EventNumber`;
- Número de clusters reconstruídos;
- Número de clusters com associação truth;
- Quantidades de células por cluster;
- Soma das quantidades de células reconstruídas;
- Soma das quantidades de células truth.

### `baseline_metadata.json`

Registra metadados da extração, incluindo:

- Caminho relativo do NTUPLE utilizado;
- Nome da árvore ROOT;
- Número de entradas e eventos;
- Sementes registradas para Pythia8 e Geant4;
- Tolerâncias iniciais (`rtol` e `atol`);
- Caminho relativo do log de reconstrução;
- Critério utilizado para a associação truth.

As sementes registradas foram observadas nos logs da execução utilizada. As tolerâncias são valores registrados para referência e não representam, por si só, critérios já testados por um comparador de regressão.

## 6. Amostra e resultados de validação

A baseline foi construída com uma amostra de 10 eventos Zee.

Resultados obtidos:

| Grandeza | Resultado |
|---|---:|
| Eventos | 10 |
| Entradas/clusters reconstruídos no NTUPLE | 18 |
| Clusters truth associados | 8 |
| Eventos com clusters truth associados | 6 |
| Eventos sem clusters truth associados | 4 |
| Células reconstruídas (soma das associações por cluster) | 14.367 |
| Células truth (soma das associações por cluster) | 7.728 |

As quantidades de células representam somas das contagens registradas por cluster. Não devem ser interpretadas automaticamente como números de células físicas únicas, pois uma mesma célula pode participar de mais de uma associação de cluster.

## 7. Validações realizadas

Os dados extraídos foram confrontados com os registros do log de reconstrução:

1. As energias dos clusters reconstruídos foram comparadas com as informações do `ElectronBuilder`.
2. As energias truth foram comparadas com as informações do `ElectronBuilder_Truth`.
3. As quantidades de células reconstruídas foram recuperadas dos registros dos clusters reconstruídos.
4. As quantidades de células truth foram recuperadas dos registros do `CaloClusterMaker_Truth`.
5. Os oito clusters truth foram associados às respectivas linhas do CSV.
6. Foram preservados os clusters reconstruídos sem associação truth.

A associação entre clusters truth e clusters reconstruídos utiliza a ordem dos clusters truth associados dentro de cada evento, conforme verificado para esta amostra. Essa associação deve ser reavaliada caso a estrutura ou a ordenação dos dados mude em outra configuração de processamento.

## 8. Reprodutibilidade e limitações

Para reproduzir a extração, é necessário manter disponíveis:

- O arquivo `data/root/Zee.NTUPLE.root`;
- O arquivo `logs/reconstrucao.log`;
- Um ambiente Python com ROOT/PyROOT compatível com o arquivo produzido;
- O script `scripts/extrai_baseline_atualizado.py`.

A extração foi validada para a amostra de 10 eventos descrita neste documento. Essa validação confirma a consistência dos dados extraídos nessa amostra, mas não demonstra, por si só, que ela seja estatisticamente representativa de uma produção maior.

A extração também não implementa ainda a comparação automática entre uma nova execução e a baseline. Os valores `rtol` e `atol` registrados nos metadados deverão ser avaliados e aplicados na etapa de implementação dos testes de regressão.

## 9. Próxima etapa

A próxima etapa do trabalho é implementar um mecanismo de comparação de regressão entre novas execuções do Lorenzetti Showers e os arquivos de referência desta baseline.

Esse mecanismo deverá definir quais variáveis serão comparadas, quais tolerâncias serão aplicadas e como diferenças ou falhas serão reportadas.

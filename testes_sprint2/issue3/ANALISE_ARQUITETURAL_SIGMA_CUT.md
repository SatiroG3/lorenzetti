# Issue #3 — Análise arquitetural do Sigma Cut

**Projeto:** Lorenzetti Showers
**Tipo de entrega:** documentação técnica de investigação e especificação preliminar
**Escopo:** fluxo de digitalização e reconstrução, origem de `sigma`, corte existente nos Rings e proposta de Sigma Cut global
**Situação:** análise arquitetural concluída; implementação do corte global não realizada nesta issue

> **Nota de consolidação.** Este documento é a versão Markdown organizada do relatório da Issue #3. A atualização sobre a Issue #1, originalmente apresentada como adendo ao início do arquivo Word, foi incorporada à seção de contexto. Assim, a baseline de execução é atribuída à **Issue #1**, enquanto a extração das métricas e sua organização em `baseline_referencia/` são atribuídas à **Issue #2**. As propostas de implementação a seguir permanecem propostas, e não alterações já realizadas.

## 1. Objetivo e escopo

Esta documentação registra a investigação realizada na Issue #3 do projeto Lorenzetti Showers. O objetivo foi:

- Compreender a arquitetura de digitalização e reconstrução do calorímetro.
- Localizar a origem do parâmetro `sigma` e acompanhar sua persistência.
- Identificar o Sigma Cut já existente na construção dos Rings.
- Propor um ponto de aplicação para um corte **global de células**, antes da formação dos clusters.

O trabalho desta issue é **de análise e especificação**. Nenhuma implementação do Sigma Cut global foi realizada nesta etapa. A proposta serve de referência para o desenvolvimento e os testes futuros.

## 2. Contexto: Issues #1, #2 e #3

| Issue | Papel no projeto | Resultado registrado |
|---|---|---|
| **#1 — Baseline de execução** | Reproduzir a cadeia completa do Lorenzetti em um checkout limpo. | Pipeline Pythia 8 → Geant4 → digitalização → reconstrução → ntuple; ambiente, comandos, seed, tempos, produtos e avisos documentados. |
| **#2 — Baseline quantitativa** | Extrair e organizar métricas físicas de referência. | Scripts, notebook, CSVs, JSON de metadados e README em `baseline_referencia/`, além dos dados ROOT e logs mantidos localmente. |
| **#3 — Análise arquitetural** | Investigar o fluxo de `sigma` e especificar o futuro corte global. | Mapeamento das etapas, estudo do OF/COF, identificação do corte nos Rings e proposta de implementação em `CaloCellMerge`. |

### 2.1. Issue #1 — Baseline de execução (28/09/2026)

**Objetivo registrado:** estabelecer uma execução de referência a partir de um checkout limpo, sem modificações no código, reproduzindo geração, simulação, digitalização, reconstrução e ntuple. Também registrar commit, ambiente, comandos, sementes, logs, tempos e arquivos de referência.

**Ambiente registrado no relatório original:**

| Componente | Registro |
|---|---|
| Repositório | `/workspace/lorenzetti` |
| Branch e commit de referência | `master`, `5eb4370` |
| Estado do diretório de trabalho | Limpo na execução de referência |
| Contêiner | `lorenzetti_jupyter2` |
| Imagem | `lorenzetti/lorenzetti:latest` |
| Python | 3.10.12 |
| ROOT | 6.34.00 |
| CMake | 3.22.1 |
| Geant4 | 11.2.2 |
| Pythia | 8.313 |

**Cadeia executada:**

```text
Pythia 8 → Zee.EVT.root → Geant4 → Zee.HIT.root
        → digitalização → Zee.ESD.root
        → reconstrução → Zee.AOD.root
        → ntuple → Zee.NTUPLE.root
```

**Comandos registrados (nomes dos scripts conforme o relatório):**

```bash
gen_zee.py --nov 10 -o Zee.EVT.root
simu_trf.py -i Zee.EVT.root -o Zee.HIT.root -nt 10
digit_trf.py -i Zee.HIT.root -o Zee.ESD.root
reco_trf.py -i Zee.ESD.root -o Zee.AOD.root
ntuple_trf.py -i Zee.AOD.root -o Zee.NTUPLE.root
```

A geração utilizou a seed **413654000**, **10 eventos**, a configuração `zee_config.cmnd`, `eta_max=3.2`, `force_forward_electron=False`, `run_number=0`, `zero_vertex_particles=False`, com colisões próton–próton a **14 TeV**. A soma dos tempos registrados foi de aproximadamente **17 min 34,462 s**, não necessariamente correspondentes a uma execução contínua.

Avisos documentados durante a execução: `Module libc not found`, avisos do ROOT relativos a *dictionaries* ausentes de classes xAOD, códigos de status não verificados (3 na geração, 20 na simulação e 26 na reconstrução) e avisos do `EventContext` durante a produção do ntuple. Esses avisos não impediram a produção dos arquivos, mas devem permanecer registrados para rastreabilidade.

Os arquivos ROOT são referências experimentais e **não precisam ser versionados no Git**; devem ser preservados fora do repositório caso sejam necessários para reproduções e comparações futuras.

### 2.2. Issue #2 — Extração e organização das métricas

A Issue #2 desenvolveu os scripts de extração e análise de energia, Rings e outras variáveis relevantes da amostra. A organização atual é feita em `baseline_referencia/`, contendo documentação, script Python, notebook, CSVs e metadados. Os ROOT e os logs são mantidos localmente.

A análise registra **10 eventos gerados** e **18 entradas** no ntuple de referência; esses totais não representam necessariamente a mesma unidade de contagem (evento simulado versus entrada/candidato reconstruído). A baseline inclui clusters, *shower shapes* e Rings, para comparação com execuções futuras.

## 3. Arquitetura atual: digitalização

O script `reconstruction/reco/scripts/digit_trf.py` configura, na sequência investigada:

1. **`RootStreamHITReader` (`HITReader`):** lê Hits, Events, Particles e Seeds.
2. **`CaloCellBuilder`:** constrói as células por amostragem.
3. **`RootStreamESDMaker`:** grava `Cells` e `TruthCells` no ESD.

### 3.1. Processamento interno do `CaloCellBuilder`

- **`PulseGenerator`:** produz o pulso amostrado a partir dos depósitos de energia e adiciona ruído gaussiano.
- **`OptimalFilter` ou `ConstrainedOptimalFilter`:** reconstrói a energia; o OF convencional também estima o tempo.
- **`CrossTalkMaker` (quando habilitado):** modifica pulsos nas células elegíveis e executa novamente o filtro.
- **`CaloCellMerge`:** reúne as coleções por amostragem e produz `Cells` e `TruthCells`.

Na configuração analisada, o *cross-talk* é habilitado para **EMEC2** e **EMB2**. O `CrossTalkMaker` executa novamente a ferramenta de filtragem depois de modificar o pulso.

## 4. Arquitetura atual: reconstrução

A etapa de reconstrução investigada inclui:

1. **`RootStreamESDReader`:** lê Cells, TruthCells, Events, Particles e Seeds.
2. **`CaloClusterMaker`:** constrói `Clusters` a partir de `Cells`.
3. **`CaloClusterMaker_Truth`:** constrói `TruthClusters` a partir de `TruthCells`.
4. **`CaloRingsBuilderL0`:** constrói Rings a partir de Clusters.
5. **`ElectronBuilder`:** constrói candidatos a elétrons.

O `CaloClusterMaker` procura células centrais quentes em **EMB2/EMEC2**, calcula a energia na região central e reúne células dentro da janela do cluster. Filtrar `Cells` antes dessa etapa pode alterar a célula quente escolhida, a soma central e a composição dos clusters.

## 5. Origem e persistência de `sigma`

Em `PulseGenerator.cxx`, o ruído gaussiano é adicionado ao vetor de amostras e o desvio-padrão configurado é armazenado no descritor:

```cpp
AddGaussianNoise(pulse_sum, m_noiseMean, m_noiseStd);
cell->setPulse(pulse_sum);
cell->setSigma(m_noiseStd);
```

Em `CaloCellBuilder.py`, `NoiseStd` recebe `samp.Noise`, portanto o ruído é configurado por amostragem. No levantamento apresentado no documento original, constam:

| Região / detector | Valores de `Noise` identificados |
|---|---|
| ECAL | 90, 26, 60 e 40 MeV |
| EMEC | 26, 60 e 40 MeV |
| HEC | 250 e 400 MeV |
| TILE | 20 MeV |

O parâmetro `sigma` pertence a `CaloDetDescriptor`. Seu cabeçalho disponibiliza `setSigma()` e `sigma()`, e o conversor serializa e restaura esse campo. `CaloCell` mantém o descritor associado; o acesso utilizado nos Rings é:

```cpp
cell->descriptor()->sigma()
```

## 6. Filtros de energia: OF e COF

### 6.1. Optimal Filter convencional

O `OptimalFilter` calcula a energia reconstruída por meio de uma soma ponderada das amostras do pulso:

$$
E_{\mathrm{reco}} = \sum_i p_i\,w_i^E
$$

Os pesos de energia são configurados por amostragem em `samp.OFWeightsEnergy`. O OF convencional também estima o tempo por meio dos pesos temporais.

### 6.2. Constrained Optimal Filter

Quando `CaloFlags.DoCOF` está ativo e a amostragem é **TILE**, o `CaloCellBuilder` seleciona `ConstrainedOptimalFilter`.

Segundo a implementação analisada, o COF gera um pulso de referência, constrói matrizes, estima amplitudes, seleciona amostras conforme `Threshold` e calcula a amplitude final por solução matricial. Nesse trecho, armazena a energia com `cell->setE()`; não foi identificado cálculo de `tau`.

Como os procedimentos são diferentes, **não se deve assumir** que a propagação de incerteza derivada dos pesos fixos do OF convencional também descreva o COF.

## 7. Sigma Cut já existente nos Rings

`CaloRingsMaker` possui as propriedades `DoSigmaCut` e `SigmaCut`. Na configuração analisada, `CaloRingsBuilderL0` é instanciado com `DoSigmaCut=True` e `SigmaCut=flags.SigmaCut`.

A condição identificada é:

$$
E_{\mathrm{cell}} > n_{\sigma}\,\sigma_{\mathrm{cell}}
$$

No `CaloRingsMaker`, a seleção ocorre durante a construção dos `RingSets` e também na escolha da célula central em `maxCell()`. Esse corte **não remove** células da coleção global `Cells` e **não altera** clusters já construídos.

A investigação encontrou lógica semelhante nas topologias de Rings **Asym, Corner, Cross, Custom e Strips**.

## 8. Proposta de Sigma Cut global

### 8.1. Ponto recomendado

A proposta é avaliar a aplicação do corte dentro do **`CaloCellMerge`**, durante a criação das células reconstruídas da coleção `Cells`.

Esse ponto situa-se **depois** da reconstrução de energia e da eventual correção de *cross-talk*, e **antes** da gravação no ESD e da execução de `CaloClusterMaker`.

O `CaloCellMerge` já reúne coleções por amostragem, possui acesso ao descritor e materializa a coleção global de células. Por isso, parece uma opção localizada para a primeira implementação.

### 8.2. Contrato técnico preliminar

| Item | Proposta |
|---|---|
| Algoritmo | `CaloCellMerge` |
| Propriedades | `DoSigmaCut` (`bool`) e `SigmaCut` (`float`) |
| Entrada | Coleções de `CaloDetDescriptor` por amostragem |
| Energia | `descriptor->e()` |
| Sigma | `descriptor->sigma()` |
| Condição | `E_reco > SigmaCut × sigma` |
| Saída filtrada | Apenas `Cells` |
| Saída preservada | `TruthCells`, sem filtragem global |
| Posição | Após OF/*cross-talk* e antes de `CaloClusterMaker` |

O contrato acima é **preliminar**: as condições-limite, a validade de `sigma` e a semântica física do limiar precisam ser verificadas antes da implementação.

### 8.3. Alternativa considerada

Também foi considerada a criação de um algoritmo independente entre `CaloCellMerge` e `CaloClusterMaker`. Essa alternativa é mais modular, mas adiciona um componente e uma etapa à sequência.

Para o escopo discutido, o Merge parece ser a opção mais simples e localizada. A decisão deve ser confirmada na revisão do contrato antes da implementação.

## 9. Limitações e questões físicas em aberto

- `sigma` recebe diretamente `m_noiseStd`, isto é, o desvio-padrão do ruído adicionado às amostras do pulso.
- **Ainda não foi demonstrado** que esse valor corresponde exatamente à incerteza da energia reconstruída pelo filtro.
- Para OF linear e matriz de covariância $C$, a variância propagada é:

  $$
  \sigma_E^2 = \mathbf{w}^{\mathsf T} C\,\mathbf{w}
  $$

- Se o ruído das amostras for independente e com mesmo desvio-padrão $\sigma_p$, resulta:

  $$
  \sigma_E = \sigma_p\sqrt{\sum_i w_i^2}
  $$

- A independência entre amostras precisa ser verificada. Correlações exigem a matriz de covariância completa.
- No COF, a seleção de amostras e a solução matricial exigem análise própria.
- Reproduzir a convenção do Sigma Cut utilizado nos Rings **não equivale** a validar independentemente a definição física de `sigma`.

## 10. Diagrama do fluxo proposto

O fluxo abaixo explicita que o Sigma Cut **global** é uma proposta a ser inserida na construção da coleção `Cells`, enquanto o Sigma Cut dos **Rings** já existe e é independente:

```text
RootStreamHITReader (HITReader)
            |
            v
CaloCellBuilder por amostragem
   PulseGenerator
         |
      OF / COF
         |
   CrossTalkMaker (opcional, com novo filtro)
         |
         v
     CaloCellMerge
         |
         +-- Sigma Cut global (PROPOSTO; apenas Cells)
         |
         v
  ESD: Cells filtradas + TruthCells preservadas
         |
         v
    CaloClusterMaker
         |
         v
       Clusters
         |
         v
   CaloRingsBuilder
      Sigma Cut dos Rings (EXISTENTE; independente)
```

## 11. Critérios de aceitação para implementação futura

- [ ] O corte global pode ser ativado e desativado por configuração.
- [ ] O limiar $n_\sigma$ é configurável.
- [ ] Com o corte desativado, o comportamento reproduz a baseline de referência.
- [ ] Com o corte ativado, apenas células que satisfazem $E_{\mathrm{reco}} > n_\sigma\sigma$ entram em `Cells`.
- [ ] `TruthCells` e `TruthClusters` permanecem independentes do corte global.
- [ ] O Sigma Cut dos Rings permanece configurável e independente.
- [ ] São registradas as contagens de células antes e depois do corte, comparando-as com a baseline.
- [ ] São executados testes de regressão, comparando clusters, Rings e observáveis relevantes.

Esses itens são **critérios futuros**, não testes já aprovados na Issue #3.

## 12. Conclusão

A análise identificou o fluxo de digitalização e reconstrução, a origem e a persistência de `sigma`, as diferenças entre OF e COF e o funcionamento do Sigma Cut já existente nos Rings.

O ponto recomendado para avaliar o Sigma Cut global é o **`CaloCellMerge`**, filtrando somente `Cells` antes da formação dos clusters. A principal ressalva permanece física: o `sigma` armazenado corresponde ao desvio-padrão aplicado ao ruído das amostras, e sua equivalência com a incerteza da energia reconstruída **ainda precisa ser demonstrada**.

A implementação do corte global não pertence a esta issue de análise arquitetural.

## Apêndice A — Tempos e produtos registrados na Issue #1

| Etapa | Tempo real | Saída | Log |
|---|---|---|---|
| Geração | 2m 40,219s | `Zee.EVT.root` — 15 KB | `geracao.log` — 35 KB |
| Simulação | 6m 29,434s | `Zee.HIT.root` — 285 KB | `simulacao.log` — 313 KB |
| Digitalização | 2m 59,188s | `Zee.ESD.root` — 1,1 MB | `digitizacao.log` — 22 KB |
| Reconstrução | 3m 10,800s | `Zee.AOD.root` — 985 KB | `reconstrucao.log` — 45 KB |
| Ntuple | 2m 14,711s | `Zee.NTUPLE.root` — 38 KB | `ntuple.log` — 9,8 KB |

**Rastreabilidade:** os tempos e tamanhos foram transcritos do documento de análise original; referem-se à execução de referência nele descrita, não a uma medição nova nesta conversão para Markdown.

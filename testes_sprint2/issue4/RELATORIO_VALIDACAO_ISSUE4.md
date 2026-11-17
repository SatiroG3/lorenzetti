# Issue #4 — Inicialização explícita de `m_sigma` e `m_tau`

**Projeto:** Lorenzetti Showers
**Sprint:** 2
**Status da validação:** Funcionalmente aprovada; equivalência física determinística não demonstrada
**Escopo:** `events/CaloCell/src/CaloDetDescriptor.cxx`
**Data do relatório:** 10 de novembro de 2026

## 1. Objetivo

Corrigir a ausência de inicialização explícita dos membros `m_tau` e `m_sigma` no construtor de `CaloDetDescriptor`, evitando que objetos recém-criados exponham valores indeterminados nesses atributos.

Esta issue é restrita à inicialização dos membros. A definição e propagação física do ruído de cada camada, a cópia de `sigma` e a implementação do Sigma Cut global são tratadas em outras issues da Sprint 2.

## 2. Alteração implementada

**Arquivo:** `events/CaloCell/src/CaloDetDescriptor.cxx`.

Foram acrescentadas as inicializações:

```cpp
m_tau(0)
```

após `m_e(0)`, e

```cpp
m_sigma(0)
```

após `m_z(detZ)`, respeitando a ordem de declaração dos membros na classe.

**Interpretação:** zero é o estado inicial definido do objeto, **não** uma estimativa física válida do ruído calorimétrico. O `PulseGenerator`, quando executado sobre um descritor, utiliza `cell->setSigma(m_noiseStd)` para atribuir o parâmetro de ruído configurado.

## 3. Ambiente e entradas de referência

- Execução em ambiente Docker/WSL2 com Lorenzetti, ROOT e scripts Python de transformação.
- Entrada comum dos testes de digitalização: `baseline_referencia/data/root/Zee.HIT.root`.
- Baseline da Sprint 1: dez eventos Zee, energia de centro de massa de 14 TeV; geração Pythia com seed `413654000` (semente da **geração**, não da digitalização).
- NTUPLE de referência: `baseline_referencia/data/root/Zee.NTUPLE.root`.
- Os testes de digitalização da Issue #4 foram executados com `--nov 10 -nt 1`.

## 4. Verificações estruturais e unitárias

### 4.1 Compilação

A compilação completa com `cmake --build build -j2` terminou com sucesso após a alteração. O projeto disponibiliza a biblioteca compartilhada `build/liblorenzetti.so`; `events/CaloCell` é um alvo CMake do tipo OBJECT, e não uma biblioteca independente `libCaloCell.so`.

### 4.2 Teste do construtor

**Fonte:** `testes_sprint2/teste_inicializacao_descriptor.cxx`.

O teste instancia um descritor e verifica os valores iniciais dos membros. Resultado registrado:

```text
Energia inicial: 0
Tau inicial: 0
Sigma inicial: 0
TESTE APROVADO
```

Isso confirma o comportamento do construtor compilado. O teste não avalia a atribuição posterior de ruído físico nem a cópia de descritores.

## 5. Teste de integração: primeira execução corrigida

Partindo do mesmo arquivo HIT da baseline, foram executadas as etapas:

| Etapa | Saída | Tempo | Código de saída |
|---|---|---:|---:|
| Digitalização | `testes_sprint2/issue4/data/Zee.ESD.root` | 69,18 s | 0 |
| Reconstrução | `testes_sprint2/issue4/data/Zee.AOD.root` | 59,02 s | 0 |
| NTUPLE | `testes_sprint2/issue4/data/Zee.NTUPLE.root` | 54,27 s | 0 |

Os NTUPLEs da baseline e da primeira execução corrigida apresentaram **18 entradas** e **99 branches**, sem branches exclusivas. As 18 entradas correspondem às entradas da árvore `physics` e não devem ser interpretadas como 18 eventos gerados; a entrada da transformação continha dez eventos.

**Comparação numérica original:** `testes_sprint2/issue4/comparar_ntuple.py`.

- 5.964 valores comparados;
- 38 branches com diferenças;
- 2.409 diferenças numéricas segundo os critérios do script (`rtol=1e-5`, `atol=1e-6`).

Essas divergências exigiram investigação antes de se afirmar equivalência física.

## 6. Investigação da aleatoriedade

### 6.1 Evidência no código

No arquivo `reconstruction/calorimeter/CaloCellBuilder/src/PulseGenerator.cxx`, o construtor inicializa um gerador `TRandom3` com:

```cpp
m_rng(0)
```

Durante a execução, o componente adiciona ruído gaussiano ao pulso e registra o desvio-padrão configurado:

```cpp
AddGaussianNoise(pulse_sum, m_noiseMean, m_noiseStd);
cell->setPulse(pulse_sum);
cell->setSigma(m_noiseStd);
```

O `AnomalyGenerator` também contém `m_rng(0)`. Já `PileupMerge` dispõe de uma propriedade `Seed` e executa `m_rng.SetSeed(m_seed)` na inicialização.

### 6.2 Teste independente do ROOT

Duas instâncias de `ROOT.TRandom3(0)` criadas na mesma sessão retornaram sementes diferentes:

```text
Gerador A: 2169776792
Gerador B: 149116508
```

Também produziram sequências gaussianas diferentes com média zero e desvio-padrão 90. Esse teste confirma o comportamento não determinístico observado para a inicialização com zero no ROOT instalado, mas não identifica por si só a causa de toda diferença no pipeline.

### 6.3 Configuração nos logs

Os logs de digitalização da baseline e da Issue #4 mostraram a mesma sequência de valores configurados de `sampling noise` e o processamento dos eventos 0 a 9. Não foi identificada, nesses logs, uma semente explícita da digitalização.

## 7. Repetição controlada com o mesmo código corrigido

Foi realizada uma **segunda execução independente** com o mesmo código corrigido, a mesma entrada HIT e os mesmos parâmetros informados, sem novas alterações no código-fonte.

| Etapa | Saída | Tempo | Código de saída |
|---|---|---:|---:|
| Digitalização | `testes_sprint2/issue4/repeticao/data/Zee.ESD.root` | 136,56 s | 0 |
| Reconstrução | `testes_sprint2/issue4/repeticao/data/Zee.AOD.root` | 98,43 s | 0 |
| NTUPLE | `testes_sprint2/issue4/repeticao/data/Zee.NTUPLE.root` | 114,65 s | 0 |
| **Total** | | **349,64 s** | |

### 7.1 Estrutura e arquivos ESD

Ambos os ESDs continham uma árvore `CollectionTree` com dez entradas e seis branches:

- `EventInfoContainer_Events`;
- `SeedContainer_Seeds`;
- `TruthParticleContainer_Particles`;
- `CaloCellContainer_Cells`;
- `CaloCellContainer_TruthCells`;
- `CaloDetDescriptorContainer_Cells`.

Os arquivos ESD eram binariamente diferentes:

| | Primeira execução | Segunda execução |
|---|---|---|
| Tamanho | 1.118.045 bytes | 1.118.417 bytes |
| SHA-256 | `e916c79134c932e0fc9c373a14f9cea2959844db325ff8f462a24a0ac4143ac5` | `44a215ee9ba4ff43b978db970049f1deb86854a1012997d623e20deb4052a1b1` |

**Limitação:** hashes distintos demonstram diferenças binárias, mas não demonstram isoladamente diferenças físicas; metadados e detalhes da serialização ROOT também podem variar. A inspeção direta dos membros persistidos de `xAOD::CaloDetDescriptor_t` foi limitada pela ausência de dicionário ROOT dessa classe.

### 7.2 Comparação dos NTUPLEs corrigidos

**Script:** `testes_sprint2/issue4/comparar_repeticoes.py`
**Log:** `testes_sprint2/issue4/repeticao/logs/comparacao_ntuple.log`.

Ambos os NTUPLEs continham 18 entradas e 99 branches. A comparação encontrou:

- 5.964 valores comparados;
- 39 branches com diferenças;
- 2.414 diferenças numéricas.

| Variável | Diferenças: baseline × corrigido 1 | Diferenças: corrigido 1 × corrigido 2 |
|---|---:|---:|
| `cl_e` | 18 | 18 |
| `cl_e1` | 18 | 18 |
| `cl_e2` | 18 | 18 |
| `cl_et` | 18 | 18 |
| `cl_reta` | 18 | 18 |
| `cl_rings_Rings` | 1.427 | 1.420 |
| `cl_ringsL0` | 429 | 441 |
| **Total, todas as branches** | **2.409** | **2.414** |

A semelhança das contagens é sugestiva, mas **contagens próximas não constituem prova estatística de equivalência**.

## 8. Magnitudes das diferenças físicas

Foram calculadas a média e a mediana do módulo das diferenças entre valores das mesmas posições de entrada nos três NTUPLEs.

| Variável | Média |Δ| baseline × corrigido 1 | Média |Δ| corrigido 1 × corrigido 2 | Mediana |Δ| baseline × corrigido 1 | Mediana |Δ| corrigido 1 × corrigido 2 |
|---|---:|---:|---:|---:|
| `cl_e` | 753,466580 | 935,599826 | 440,607422 | 763,542969 |
| `cl_et` | 349,160265 | 468,282227 | 232,626953 | 303,684570 |
| `cl_e1` | 315,433051 | 344,000407 | 214,099121 | 239,035156 |
| `cl_e2` | 751,578776 | 857,126411 | 713,150391 | 506,144531 |
| `cl_reta` | 0,007031 | 0,006721 | 0,003008 | 0,003382 |

Em quatro das cinco variáveis, a diferença absoluta média entre as duas execuções corrigidas foi maior que a diferença entre a baseline e a primeira execução corrigida. Para `cl_reta`, as médias foram próximas.

**Interpretação:** nas variáveis avaliadas, a magnitude das diferenças baseline × corrigido está na mesma ordem de grandeza da variabilidade observada entre execuções do mesmo código corrigido. Isso é **compatível** com a influência da aleatoriedade da digitalização, mas não isola causalmente o efeito da correção.

## 9. Observações adicionais

- Valores negativos de grande magnitude foram observados em variáveis como `cl_lateralMom`, `cl_secondR` e `cl_secondLambda`, inclusive entre as duas execuções corrigidas. Sua origem e interpretação física não foram estabelecidas neste teste; não se deve atribuí-los automaticamente à Issue #4.
- Houve pelo menos uma divergência em `el_tight` entre execuções corrigidas, indicando que a variabilidade pode alcançar uma decisão discreta de identificação.
- Mensagens `Module libc not found.` e avisos de ausência de dicionários ROOT apareceram durante a inspeção, sem impedir a conclusão dos processos analisados.
- Tempos de execução diferentes não são, por si, evidência de alteração física.

## 10. Limitações e critérios de conclusão

1. **Não houve comparação antes/depois com a mesma sequência de números aleatórios.** A equivalência determinística não foi testada.
2. **Amostra limitada:** dez eventos de entrada e 18 entradas de candidatos na árvore `physics`; insuficiente para uma caracterização estatística abrangente.
3. **Correspondência entre candidatos:** as comparações numéricas foram feitas por posição de entrada; a correspondência física individual não foi validada independentemente em todos os casos.
4. **Não houve comparação direta dos valores físicos de cada célula ESD**, devido à dificuldade de inspecionar os tipos persistidos sem os dicionários ROOT apropriados.
5. **A proximidade dos totais de diferenças não é teste de equivalência.** Não foram estabelecidos intervalos de confiança ou critérios físicos de aceitação para cada observável.
6. **O estado final do repositório** (por exemplo, `git diff`/`git status`) e a repetição final do teste unitário devem ser conferidos antes do fechamento definitivo da issue, caso ainda não tenham sido verificados após os testes.

## 11. Conclusão

A alteração da Issue #4 foi **validada funcionalmente**: os membros `m_tau` e `m_sigma` foram inicializados explicitamente, o teste unitário confirmou seus valores iniciais, a compilação foi bem-sucedida e o pipeline completo continuou operacional.

A comparação exploratória de resultados físicos não revelou um desvio claramente atribuível à correção: diferenças da mesma ordem de grandeza também ocorreram entre duas execuções independentes do código corrigido. O uso de `TRandom3(0)` no `PulseGenerator` fornece uma explicação plausível para parte dessa variabilidade.

**Conclusão recomendada para a issue:** correção funcionalmente aprovada, **com a ressalva de que não foi demonstrada equivalência física determinística nem ausência absoluta de regressões**. A aprovação não se estende às questões de propagação/cópia de `sigma` ou à lógica de Sigma Cut previstas em outras issues.

## 12. Checklist de encerramento

- [x] Adicionar `m_tau(0)` e `m_sigma(0)` no construtor.
- [x] Compilar o projeto completo.
- [x] Executar o teste unitário de inicialização.
- [x] Executar digitalização, reconstrução e NTUPLE com o código corrigido.
- [x] Comparar a estrutura dos NTUPLEs com a baseline.
- [x] Investigar o gerador aleatório da digitalização.
- [x] Repetir o pipeline com o mesmo código corrigido.
- [x] Comparar contagens e magnitudes das diferenças numéricas.
- [ ] Confirmar `git diff` e `git status` finais.
- [ ] Reexecutar o teste unitário final, se necessário.
- [ ] Anexar ou referenciar este relatório no comentário de encerramento da Issue #4.

## 13. Arquivos de evidência

```text
baseline_referencia/
├── data/root/Zee.HIT.root
├── data/root/Zee.NTUPLE.root
└── logs/digitizacao.log

testes_sprint2/
├── teste_inicializacao_descriptor.cxx
└── issue4/
    ├── comparar_ntuple.py
    ├── comparar_repeticoes.py
    ├── data/
    │   ├── Zee.ESD.root
    │   ├── Zee.AOD.root
    │   └── Zee.NTUPLE.root
    ├── logs/
    │   ├── digit_trf.log
    │   ├── reco_trf.log
    │   └── ntuple_trf.log
    └── repeticao/
        ├── data/
        │   ├── Zee.ESD.root
        │   ├── Zee.AOD.root
        │   └── Zee.NTUPLE.root
        └── logs/
            ├── digit_trf.log
            ├── reco_trf.log
            ├── ntuple_trf.log
            └── comparacao_ntuple.log
```

> **Nota de rastreabilidade:** os caminhos acima correspondem aos nomes relatados durante a execução. Este documento foi elaborado a partir das saídas e dos trechos de código compartilhados durante a investigação; não constitui auditoria direta do estado atual do repositório ou dos arquivos ROOT.

# Issue #5 — Preservacao de sigma em CaloDetDescriptor::copy()

## 1. Objetivo

Verificar a preservacao do atributo m_sigma durante a copia
de objetos CaloDetDescriptor no projeto Lorenzetti.

Esta issue integra a Sprint 2 do projeto Sigma Cut.

## 2. Problema identificado

O metodo CaloDetDescriptor::copy() cria um novo descritor
e transfere atributos do objeto original.

Na ausencia de setSigma(sigma()), o atributo sigma nao e
preservado na copia.

Com a inicializacao implementada na Issue #4, a copia
apresentava sigma = 0, independentemente do valor original.

## 3. Correcao

Arquivo: events/CaloCell/src/CaloDetDescriptor.cxx

A instrucao responsavel pela correcao e:

    det->setSigma( sigma() );

Durante a investigacao, essa instrucao foi restaurada.

A verificacao com git show HEAD confirmou que ela ja estava
presente no ultimo commit do repositorio.

Portanto, nao representa uma nova alteracao em relacao ao HEAD.

## 4. Teste de regressao

Arquivo: testes_sprint2/issue5/teste_copia_descriptor.cxx

Valores definidos no descritor original:

- Energia = 1000
- Tau = 25
- Sigma = 90

O teste utiliza copy() e verifica se os valores sao preservados.

### 4.1. Antes da correcao

Energia: 1000 -> 1000
Tau: 25 -> 25
Sigma: 90 -> 0

Energia: OK
Tau: OK
Sigma: FALHOU

Resultado: TESTE REPROVADO.

### 4.2. Depois da correcao

Energia: 1000 -> 1000
Tau: 25 -> 25
Sigma: 90 -> 90

Energia: OK
Tau: OK
Sigma: OK

Resultado: TESTE APROVADO.

O comportamento foi validado de forma deterministica.

## 5. Compilacao

O teste foi compilado utilizando os diretorios de inclusao
registrados pelo CMake para o modulo CaloCell.

Biblioteca utilizada: build/liblorenzetti.so

Apos a restauracao da instrucao, foi executado:

    cmake --build build -j2

Resultado: compilacao concluida sem erros.

## 6. Investigacao do CrossTalkMaker

Arquivo:
reconstruction/calorimeter/CaloCellBuilder/src/CrossTalkMaker.cxx

Foi identificada a chamada:

    xAOD::CaloDetDescriptor *xtdescriptor = descriptor->copy();

A copia participa da avaliacao das condicoes de cross-talk
e da selecao de celulas vizinhas.

Entretanto, no trecho analisado, o pulso e modificado
no descritor original:

    descriptor->setPulse(centralCellPulse);

A colecao de saida tambem recebe o descritor original:

    xtCollection->insert(descriptor->hash(), descriptor);

Portanto, a analise estatica nao demonstra propagacao
do sigma da copia para a colecao de saida.

Nao foi realizado um teste de integracao desse componente.

## 7. Observacao adicional

O metodo copy() retorna um ponteiro para um objeto alocado
dinamicamente.

No fluxo analisado do CrossTalkMaker, nao foi identificada
uma liberacao explicita da memoria dessa copia.

Isso sugere um possivel vazamento de memoria e merece
investigacao independente.

Nenhuma alteracao no CrossTalkMaker foi realizada.

## 8. Limitacoes

- A validacao foi realizada por teste unitario.
- Nao foi executado um novo pipeline completo.
- Nao foi realizado teste de integracao do CrossTalkMaker.
- A instrucao corrigida ja estava presente no HEAD.

## 9. Conclusao

A falha de preservacao de sigma foi reproduzida.

A restauracao de setSigma(sigma()) corrigiu o comportamento,
conforme demonstrado pelo teste de regressao.

O projeto foi recompilado com sucesso.

A implementacao corrigida ja consta no HEAD, e o novo teste
de regressao pode ser versionado para prevenir falhas futuras.

Status: CORRECAO FUNCIONALMENTE VALIDADA.

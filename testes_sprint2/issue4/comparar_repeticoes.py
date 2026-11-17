import ROOT
import math
from collections import defaultdict

BASE = "testes_sprint2/issue4/data/Zee.NTUPLE.root"
NOVO = "testes_sprint2/issue4/repeticao/data/Zee.NTUPLE.root"

RTOL = 1e-5
ATOL = 1e-6

def valores(objeto):
    if hasattr(objeto, "size"):
        return list(objeto)
    return [objeto]

def comparar(a, b):
    if isinstance(a, float) or isinstance(b, float):
        a, b = float(a), float(b)

        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)

        if math.isinf(a) or math.isinf(b):
            return a == b

        return math.isclose(a, b, rel_tol=RTOL, abs_tol=ATOL)

    return a == b

f1 = ROOT.TFile.Open(BASE)
f2 = ROOT.TFile.Open(NOVO)

if not f1 or f1.IsZombie() or not f2 or f2.IsZombie():
    raise RuntimeError("Erro ao abrir os arquivos ROOT")

t1 = f1.Get("physics")
t2 = f2.Get("physics")

if not t1 or not t2:
    raise RuntimeError("Arvore physics nao encontrada")

b1 = {b.GetName() for b in t1.GetListOfBranches()}
b2 = {b.GetName() for b in t2.GetListOfBranches()}

print("Entradas baseline:", t1.GetEntries())
print("Entradas Issue 4:", t2.GetEntries())
print("Branches baseline:", len(b1))
print("Branches Issue 4:", len(b2))
print("Branches exclusivas baseline:", sorted(b1 - b2))
print("Branches exclusivas Issue 4:", sorted(b2 - b1))

diferencas = defaultdict(int)
exemplos = {}
comparacoes = 0

if t1.GetEntries() != t2.GetEntries():
    print("ATENCAO: quantidades de entradas diferentes")

for i in range(min(t1.GetEntries(), t2.GetEntries())):
    t1.GetEntry(i)
    t2.GetEntry(i)

    for nome in sorted(b1 & b2):
        v1 = valores(getattr(t1, nome))
        v2 = valores(getattr(t2, nome))

        if len(v1) != len(v2):
            diferencas[nome] += 1
            exemplos.setdefault(
                nome, (i, f"tamanho {len(v1)}", f"tamanho {len(v2)}")
            )
            continue

        for j, (a, b) in enumerate(zip(v1, v2)):
            comparacoes += 1

            if not comparar(a, b):
                diferencas[nome] += 1
                exemplos.setdefault(nome, (i, j, a, b))

print("\n" + "=" * 60)
print("RESULTADO DA COMPARACAO")
print("=" * 60)

print("Valores comparados:", comparacoes)
print("Branches com diferencas:", len(diferencas))
print("Total de diferencas:", sum(diferencas.values()))

for nome in sorted(diferencas):
    print(f"\n{nome}: {diferencas[nome]} diferencas")
    print("  Primeiro exemplo:", exemplos[nome])

if not diferencas and b1 == b2 and t1.GetEntries() == t2.GetEntries():
    print("\nRESULTADO: COMPATIVEL DENTRO DAS TOLERANCIAS")
else:
    print("\nRESULTADO: DIFERENCAS IDENTIFICADAS")

f1.Close()
f2.Close()

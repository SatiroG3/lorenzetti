
import csv
import json
import re
from collections import OrderedDict
from pathlib import Path

import ROOT


BASE_DIR = Path(__file__).resolve().parent.parent

ROOT_FILE = BASE_DIR / "data" / "root" / "Zee.NTUPLE.root"
RECO_LOG = BASE_DIR / "logs" / "reconstrucao.log"
TREE_NAME = "physics"
OUTPUT_DIR = BASE_DIR / "data" / "baseline_output"

RTOL = 1e-5
ATOL = 1e-6


def read_ntuple(filename):
    root_file = ROOT.TFile.Open(str(filename), "READ")
    if not root_file or root_file.IsZombie():
        raise RuntimeError(f"Não foi possível abrir {filename}")

    tree = root_file.Get(TREE_NAME)
    if not tree:
        root_file.Close()
        raise RuntimeError(f"Árvore '{TREE_NAME}' não encontrada")

    events = OrderedDict()

    for i in range(tree.GetEntries()):
        tree.GetEntry(i)

        run = int(tree.RunNumber) if tree.GetBranch("RunNumber") else 0
        event = int(tree.EventNumber)

        record = {
            "entry": i,
            "RunNumber": run,
            "EventNumber": event,
            "cl_e": float(tree.cl_e),
            "cl_et": float(tree.cl_et),
            "cl_eta": float(tree.cl_eta),
            "cl_phi": float(tree.cl_phi),
            "cl_reta": float(tree.cl_reta),
            "cl_eratio": float(tree.cl_eratio),
            "cl_weta2": float(tree.cl_weta2),
            "Rings": [float(x) for x in tree.cl_rings_Rings],
            "truth_cl_e": float(tree.truth_cl_e),
            "Truth_Rings": [
                float(x) for x in tree.truth_cl_rings_TruthRings
            ],
            "el_tight": bool(tree.el_tight),
        }

        record["truth_available"] = (
            len(record["Truth_Rings"]) > 0 or record["truth_cl_e"] != 0
        )

        events.setdefault((run, event), []).append(record)

    root_file.Close()
    return events


def read_cell_counts(filename):
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Log não encontrado: {filename}")

    events = OrderedDict()
    current_event = None
    current_type = "reco"

    event_pattern = re.compile(r"Event\s+(\d+)\s*={3,}")
    cell_pattern = re.compile(
        r"Cluster\s+(\d+)\s+Number of cells:\s*(\d+)"
    )

    for line in path.read_text(errors="replace").splitlines():
        event_match = event_pattern.search(line)
        if event_match:
            current_event = int(event_match.group(1))
            events.setdefault(current_event, {"reco": [], "truth": []})
            current_type = "reco"
            continue

        if current_event is None:
            continue

        if "CaloClusterMaker_Truth" in line:
            current_type = "truth"
        elif "CaloClusterMaker" in line:
            current_type = "reco"

        cell_match = cell_pattern.search(line)
        if cell_match:
            events[current_event][current_type].append(
                (int(cell_match.group(1)), int(cell_match.group(2)))
            )

    return events


def save_csv(filename, rows):
    if not rows:
        raise RuntimeError(f"Nenhum dado para salvar em {filename}")

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()

        for row in rows:
            writer.writerow({
                key: json.dumps(value, ensure_ascii=False)
                if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            })


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    events = read_ntuple(ROOT_FILE)
    cell_counts = read_cell_counts(RECO_LOG)

    cluster_rows = []
    event_rows = []

    for sequence, (event_key, clusters) in enumerate(events.items()):
        if sequence not in cell_counts:
            raise RuntimeError(f"Evento {sequence} não encontrado no log")

        reco_cells = cell_counts[sequence]["reco"]
        truth_cells = cell_counts[sequence]["truth"]

        truth_clusters = [
            (index, cluster)
            for index, cluster in enumerate(clusters)
            if cluster["truth_available"]
        ]

        if len(reco_cells) != len(clusters):
            raise RuntimeError(
                f"Evento {sequence}: {len(clusters)} clusters no NTUPLE "
                f"e {len(reco_cells)} clusters reconstruídos no log"
            )

        if len(truth_clusters) != len(truth_cells):
            raise RuntimeError(
                f"Evento {sequence}: {len(truth_clusters)} clusters truth "
                f"associados no NTUPLE e {len(truth_cells)} no log"
            )

        truth_by_reco_index = {}

        for (reco_index, cluster), (truth_index, n_cells) in zip(
            truth_clusters, truth_cells
        ):
            truth_by_reco_index[reco_index] = {
                "truth_cluster_index": truth_index,
                "n_cells_truth": n_cells,
            }

        event_rows.append({
            "sequence": sequence,
            "RunNumber": event_key[0],
            "EventNumber": event_key[1],
            "n_clusters": len(clusters),
            "n_truth_associated": len(truth_clusters),
            "reco_cells_per_cluster": [n for _, n in reco_cells],
            "truth_cells_per_cluster": [n for _, n in truth_cells],
            "n_reco_cells": sum(n for _, n in reco_cells),
            "n_truth_cells": sum(n for _, n in truth_cells),
        })

        for index, cluster in enumerate(clusters):
            row = dict(cluster)
            row["sequence"] = sequence
            row["cluster_index"] = index
            row["n_cells_reco"] = reco_cells[index][1]

            truth_info = truth_by_reco_index.get(index)
            row["truth_cluster_index"] = (
                truth_info["truth_cluster_index"] if truth_info else None
            )
            row["n_cells_truth"] = (
                truth_info["n_cells_truth"] if truth_info else 0
            )

            cluster_rows.append(row)

    save_csv(OUTPUT_DIR / "baseline_clusters.csv", cluster_rows)
    save_csv(OUTPUT_DIR / "baseline_eventos.csv", event_rows)

    metadata = {
        "arquivo": "data/root/Zee.NTUPLE.root",
        "arvore": TREE_NAME,
        "entradas": sum(len(x) for x in events.values()),
        "eventos": len(events),
        "sementes": {
            "Pythia8": 413654000,
            "Geant4": 512,
        },
        "tolerancias_iniciais": {
            "rtol": RTOL,
            "atol": ATOL,
        },
        "log_reconstrucao": "logs/reconstrucao.log",
        "associacao_truth": (
            "ordem dos clusters truth associados por evento"
        ),
    }

    with open(
        OUTPUT_DIR / "baseline_metadata.json", "w", encoding="utf-8"
    ) as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    print(f"Baseline salva em: {OUTPUT_DIR.resolve()}")
    print(f"Eventos: {len(events)}")
    print(f"Clusters/entradas: {sum(len(x) for x in events.values())}")
    print(
        "Clusters truth: "
        f"{sum(len(x['truth']) for x in cell_counts.values())}"
    )


if __name__ == "__main__":
    main()

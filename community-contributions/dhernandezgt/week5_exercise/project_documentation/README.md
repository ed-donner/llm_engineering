# WEEK5 Exercise RAG project  
### **Daniel Hernandez**  

## Directory Tree

```text
.
├── .env
├── chroma_db
│   ├── 99cf17c5-4940-41ca-a72d-3adebf163702
│   │   ├── data_level0.bin
│   │   ├── header.bin
│   │   ├── index_metadata.pickle
│   │   ├── length.bin
│   │   └── link_lists.bin
│   └── chroma.sqlite3
├── docs
│   ├── RFC_evaluation
│   │   └── rag_evaluation_dataset.csv
│   ├── csv
│   ├── pdf
│   └── txt
│       ├── application
│       │   ├── RFC1034_DNS_Concepts.txt
│       │   └── RFC1035_DNS_Implementation.txt
│       ├── ipv4
│       │   ├── RFC791_IPv4.txt
│       │   ├── RFC792_ICMP.txt
│       │   └── RFC826_ARP.txt
│       ├── ipv6
│       │   └── RFC4861_IPv6_Neighbor_Discovery.txt
│       ├── routing
│       │   ├── RFC2328_OSPFv2.txt
│       │   ├── RFC2453_RIP_v2.txt
│       │   └── RFC4271_BGP4.txt
│       └── transport
│           ├── RFC768_UDP.txt
│           └── RFC793_TCP.txt
├── eval_results_GPT.csv
├── eval_results_Gemma.csv
├── eval_terminal_printout_GPT.txt
├── eval_terminal_printout_Gemma.txt
├── exercise_week5_v1.ipynb
├── project_documentation
│   ├── 01_ABOUT_RFC_EDITOR.md
│   ├── 02_WHAT_IS_RFC.md
│   ├── 03_DOCUMENTS_FOR_TEST.md
│   ├── 04_EVALUATION.md
│   └── README.md
├── rag_eval
│   ├── __init__.py
│   ├── evaluator.py
│   ├── loader.py
│   ├── mapping.py
│   ├── metrics.py
│   └── report.py
├── run_real_eval.py
└── src
    └── intelligence_v3.py

```

## Project Documentation

| Doc | Covers |
|---|---|
| [`01_ABOUT_RFC_EDITOR.md`](01_ABOUT_RFC_EDITOR.md) | Where find `RFC` documentation use in example |
| [`02_WHAT_IS_RFC.md`](02_WHAT_IS_RFC.md) | Few information about `RFC` |
| [`03_DOCUMENTS_FOR_TEST.md`](03_DOCUMENTS_FOR_TEST.md) | Which `RFC` are use for project and its better folder distribution for use in `Metadata` |
| [`04_EVALUATION.md`](04_EVALUATION.md) | Evaluation module and its interpretation |

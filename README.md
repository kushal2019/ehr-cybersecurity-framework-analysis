# ehr-cybersecurity-framework-analysis

Code for the MSc Cybersecurity dissertation *A Comparative Evaluation of Cybersecurity Governance Frameworks for Electronic Health Record Systems in the UK National Health Service* (Kushal Poudel, University of West London, 2026).

| File | Purpose |
| `ehr_keyword_search.py` | Searches the framework documents for EHR threat keywords and builds the Appendix A data extraction table |
| `generate_figures.py` | Produces the six Chapter 4 figures from the ratings in Tables 4.1 and 4.2 |

## Requirements
Python 3 and four packages:
```
pip install pymupdf python-docx matplotlib numpy
```

## Framework documents
The framework PDFs are not included, because HITRUST CSF and the ISO/IEC 27001:2022 guide are copyrighted. The versions used are:
- NIST Cybersecurity Framework 2.0 (NIST CSWP 29, 2024), from nist.gov
- ISO/IEC 27001:2022 controls, as described by Kenyon (2024); see the dissertation reference list
- HITRUST CSF v11.8.0, from the HITRUST Alliance under its licence terms
- NHS Data Security Standards 1 to 10 (2023-24), from dsptoolkit.nhs.uk

Put all the PDFs in one folder. The script names each document from its file name:
| File name contains | Appendix section |
| `hitrust` or `CSF PDF` | A.1 HITRUST CSF |
| `Data Security Standard 1` to `Data Security Standard 10` | A.2 to A.11 |
| `ISO` or `27001` | A.12 ISO 27001 |
| `NIST` or `CSWP` | A.13 NIST CSF 2.0 |

File names used in the study: `CSF PDF v11.8.0.pdf`, `Data Security Standard 1 v 2023-24.pdf` to `Data Security Standard 10 v 2023-24.pdf`, `ISO 27001.pdf` and `NIST.CSWP.29.pdf`.

## Keyword search
From the folder containing the PDFs:
```
python3 ehr_keyword_search.py --batch . --appendix
```
Add `--csv` to also save every match to a CSV file. To search a single document, use `--pdf "NIST.CSWP.29.pdf"` instead of `--batch .`.
Results are saved in a `results` folder:
- `Appendix_A_Data_Extraction_Table.docx`: the Appendix A tables
- `keyword_summary.txt`: match count and pages for every keyword in every document
- `<document>_keyword_report.txt`: every match with its page, control reference and sentence
- `all_keyword_matches.csv`: only with `--csv`

The tool locates evidence only. It does not assign Strong, Moderate or Weak ratings. Every located passage was read before a rating was given.

## Figures
```
python3 generate_figures.py
```

The figures are saved in the current folder, and the aggregate scores are printed:
| File | Figure |
| `fig4_1_heatmap.png` | 4.1 Heatmap of Framework Coverage by Threat Category |
| `fig4_2_tm_heatmap.png` | 4.2 Threat Modelling Integration Across Frameworks |
| `fig4_3_by_framework.png` | 4.3 Distribution of Ratings by Framework |
| `fig4_4_by_threat.png` | 4.4 Distribution of Ratings by Threat Category |
| `fig4_5_gdpr_vs_coverage.png` | 4.5 GDPR Alignment Against Average Threat Coverage |
| `fig4_6_coverage_vs_tm.png` | 4.6 Threat Coverage Against Threat Modelling Integration |

## Outputs
The search outputs and figures are on Figshare: DOI_HERE

## Citation
Poudel, K. (2026) *A Comparative Evaluation of Cybersecurity Governance Frameworks for Electronic Health Record Systems in the UK National Health Service*. MSc dissertation. University of West London.

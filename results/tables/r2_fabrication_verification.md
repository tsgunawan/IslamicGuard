# Revision 2: canonical-text check of fabricated-scripture coding (24 paired 8B answers)

Quoted Arabic spans (>= 15 letters) compared with all 6,236 verses, consecutive verse pairs and the Arabic hadith corpus (RapidFuzz partial_ratio, loose normalization). Non-canonical = best match < 80.

| Card | Condition | Item | Coder F1 | Arabic spans checked | Non-canonical spans (best score) | English quoted spans (not checkable) |
|---|---|---|---|---:|---|---:|
| T19-002 | 8B_B0 | constructed_insufficient_0 | no | 0 | – | 0 |
| T19-023 | 8B_B5 | constructed_insufficient_0 | no | 0 | – | 0 |
| T19-032 | 8B_B0 | constructed_insufficient_1 | no | 0 | – | 0 |
| T19-033 | 8B_B5 | constructed_insufficient_1 | no | 0 | – | 0 |
| T19-031 | 8B_B0 | faithqa_row0_en | no | 0 | – | 1 |
| T19-003 | 8B_B5 | faithqa_row0_en | no | 0 | – | 0 |
| T19-021 | 8B_B0 | faithqa_row15_en_benign | no | 0 | – | 0 |
| T19-035 | 8B_B5 | faithqa_row15_en_benign | no | 0 | – | 0 |
| T19-019 | 8B_B0 | faithqa_row27_en | yes | 0 | – | 1 |
| T19-036 | 8B_B5 | faithqa_row27_en | no | 0 | – | 0 |
| T19-025 | 8B_B0 | faithqa_row39_en_benign | yes | 0 | – | 1 |
| T19-029 | 8B_B5 | faithqa_row39_en_benign | no | 0 | – | 4 |
| T19-017 | 8B_B0 | fiqh_18_madhhab | no | 0 | – | 0 |
| T19-034 | 8B_B5 | fiqh_18_madhhab | no | 0 | – | 0 |
| T19-024 | 8B_B0 | fiqh_19_madhhab | yes | 0 | – | 2 |
| T19-006 | 8B_B5 | fiqh_19_madhhab | no | 0 | – | 2 |
| T19-015 | 8B_B0 | hallutruthqa_islamicHallucination_104 | yes | 4 | هي سورة التوبة الاية واذ انذرناكم فتولي اكثركم فاتيناهم بالع (67); واذ انذرناكم فتولي اكثركم فاتيناهم بالعذاب متت (68) | 0 |
| T19-001 | 8B_B5 | hallutruthqa_islamicHallucination_104 | no | 0 | – | 2 |
| T19-012 | 8B_B0 | hallutruthqa_islamicHallucination_181 | no | 2 | – | 0 |
| T19-013 | 8B_B5 | hallutruthqa_islamicHallucination_181 | no | 1 | – | 0 |
| T19-016 | 8B_B0 | islamiceval_subtaskC_C-Q01 | yes | 3 | ولا تستغن بانفسكم ولا تلتذن بالاحزان فانها تذهب بكم الي الار (73); ولا تستغن بانفسكم ولا تلتذن بالاحزان فانها تذهب بكم الي الار (73); ولا تستغن بانفسكم و (79) | 0 |
| T19-028 | 8B_B5 | islamiceval_subtaskC_C-Q01 | no | 2 | – | 0 |
| T19-009 | 8B_B0 | islamiceval_subtaskC_C-Q02 | yes | 3 | – | 0 |
| T19-030 | 8B_B5 | islamiceval_subtaskC_C-Q02 | yes | 3 | اذا قال رجل لاخر ايه الفاحش فليعذب بعشرين سوطا وان قال له اي (70) | 0 |

Answers with at least one non-canonical Arabic scripture span: plain 2/12, retrieval 1/12.
Coder F1 cards with at least one checkable Arabic span: 4; confirmed non-canonical: 3.
Agreement between the automated flag and the coder's F1 code: 20/24 answers.
Exact McNemar on the automated flag: discordant plain-only 2, retrieval-only 1, p = 1.000.


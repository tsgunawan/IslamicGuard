# Revision 2: citation-parser coverage on held-out Arabic answers

Reference-level recall and precision against hand labels. Wilson 95% intervals. Answers were never used to build or test the parser.

| Run | Answers | Answers with >= 1 labelled reference | Labelled references (Qur'an / hadith) | Name-only mentions (not targets) | Parser | Recall | Precision | Answers with >= 1 reference checked |
|---|---:|---:|---|---:|---|---|---|---|
| 20261013-1340_Qwen__Qwen3-8B_B5_r2_heldo | 30 | 24 | 57 (35 / 22) | 6 | original | 28/57 = 0.49 [0.37, 0.62] | 28/30 = 0.93 [0.79, 0.98] | 11/24 |
| 20261013-1340_Qwen__Qwen3-8B_B5_r2_heldo | 30 | 24 | 57 (35 / 22) | 6 | repaired | 50/57 = 0.88 [0.77, 0.94] | 50/52 = 0.96 [0.87, 0.99] | 23/24 |
| 20261013-1405_Qwen__Qwen3-14B-AWQ_B5_r2_ | 30 | 22 | 43 (27 / 16) | 6 | original | 4/43 = 0.09 [0.04, 0.22] | 4/5 = 0.80 [0.38, 0.96] | 3/22 |
| 20261013-1405_Qwen__Qwen3-14B-AWQ_B5_r2_ | 30 | 22 | 43 (27 / 16) | 6 | repaired | 36/43 = 0.84 [0.70, 0.92] | 36/37 = 0.97 [0.86, 1.00] | 19/22 |

## Misses and spurious matches of the repaired parser

| Run | Item | Missed labelled references | Parser references not in labels |
|---|---|---|---|
| 20261013-1340_Qwen__Qwen3 | qhqa25_test_739 | [('hadith', 'tirmidhi', 3011)] | [] |
| 20261013-1340_Qwen__Qwen3 | qhqa25_test_721 | [('hadith', 'nasai', 2567)] | [] |
| 20261013-1340_Qwen__Qwen3 | qhqa25_test_732 | [('hadith', 'bukhari', 2348), ('quran', 5, 119), ('quran', 47, 12)] | [('quran', 5, 5)] |
| 20261013-1340_Qwen__Qwen3 | hallutruthqa_islamicHallucination_641 | [('quran', 56, 77)] | [] |
| 20261013-1340_Qwen__Qwen3 | hallutruthqa_islamicHallucination_373 | [('quran', 7, 172)] | [('quran', 7, 7)] |
| 20261013-1405_Qwen__Qwen3 | hallutruthqa_islamicHallucination_203 | [('quran', 66, 10)] | [] |
| 20261013-1405_Qwen__Qwen3 | hallutruthqa_islamicHallucination_373 | [('quran', 2, 102)] | [] |
| 20261013-1405_Qwen__Qwen3 | hallutruthqa_islamicHallucination_375 | [('quran', 53, 14)] | [] |
| 20261013-1405_Qwen__Qwen3 | hallutruthqa_islamicHallucination_678 | [('hadith', 'bukhari', 1830), ('hadith', 'bukhari', 4934), ('quran', 77, 5)] | [('quran', 7, 7)] |
| 20261013-1405_Qwen__Qwen3 | hallutruthqa_islamicHallucination_133 | [('quran', 33, 59)] | [] |

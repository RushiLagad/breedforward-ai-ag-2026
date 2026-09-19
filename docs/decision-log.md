# Decision log

| When | Decision | Alternatives | Evidence | Owner |
| --- | --- | --- | --- | --- |
| Sep 18 | Key on LINE_UNIQUE_ID, strip `.0` from C2 line numbers | key on LINE | LINE repeats across 998 populations; C2 genotype match fails without the strip | Rishi |
| Sep 18 | Inner join with the environment table, accept losing 52k C2 plots | left join with NaN covariates | the dropped plots are 5% and cluster in a few locations | Rishi, Sambhavi |
| Sep 18 | Predict broad-acre, not environment-specific | regime-specific BLUPs | between-regime r 0.23 equals within-regime split-half 0.18 to 0.25; regime explains 1.4% of env mean yield | Rishi |
| Sep 18 | Ridge on the 2,911-SNP panel, lambda tuned on 2007 | GBLUP with G matrix, BayesB | equivalent for this marker count; ridge fits in a minute | Rishi |
| Sep 18 | Adjust yield within environment x tester before modeling | raw yield, environment only | testers differ by group; 95 testers, 3.9% missing | Rishi |
| Sep 19 | Recommend sampling every family, not growing every line | genotype-only prediction | 10% of each family gives +3.9 bu/ac vs +1.7 for genotype only; curve flat past 20% | Rishi |
| Sep 19 | Index weights 0.5 / 0.1 / -0.15 / -0.05 / -0.2 | yield only; equal weights | equal weights keep only a third of the realised gain; default set 87% stable over 500 random weightings | Rishi |
| Sep 19 | Candidate set 15,968, evaluation set 15,959 | one number | 9 lines have no scorable yield | Sambhavi |
| Sep 19 | Advancement list built on family mean plus within-family markers, global markers only as fallback | markers with siblings pooled (the first version) | the first version used the second-best predictor (r 0.24, +2.6 bu/ac); the recommended one gives r 0.35, +3.9, and keeps 112 families in the flagged set instead of 31 with the bare family mean | Rishi |

# Challenge brief

## One-sentence problem

For a maize breeding program in January 2008 whose field plots have been cut, predict the testcross
performance of the 15,968 lines about to be planted, from their genotypes and 2001 to 2007 trial data,
so that the lines advanced under the constraint are the ones that would have won with a full trial.

## Stakeholder and decision

- Primary user: the head of the 115 RM inbred-development pipeline.
- Decision: which lines get a plot in 2008, and which advance to the next stage.
- Baseline today: grow everything, rank on observed testcross yield.
- Cost of a false positive: a plot and a year spent on a line that goes nowhere.
- Cost of a false negative: a superior inbred dropped before it is ever seen.

## Data

| Dataset | Unit | Target | Key features | Notes |
| --- | --- | --- | --- | --- |
| C1, C2 phenotypes | testcross plot | YLD_BE, MST, TWT, ERM, RTLP, STLP | line, tester, year, location | LINE unique only within population; C2 stores LINE as `12.0` |
| environmental_features | year x location | none | monthly weather Apr-Oct, soil by depth | 52k C2 plots have no matching row |
| Imputed genotypes | line | none | 2,911 SNPs, one panel for all 999 populations | parents in first two rows |

## Judging criteria (from the organizers' slide)

| Criterion | Points | Evidence we show |
| --- | ---: | --- |
| Presentation, unique and outside the box | 25 | We tested the obvious idea and found the plots beat the markers; the recommendation is about plot allocation |
| Data visualization | 25 | Five figures, each titled as its claim; live dashboard on the real advancement list |
| Data and results interpretation | 25 | Every number scored against the real 2008 season, with baselines and the honest ceiling |

## Minimum viable solution (done)

- Baselines: population mean, parent GCA.
- Primary metric: correlation with observed 2008 line means, and realised yield gain of the top 20%.
- Validation: leave-2008-out (CV00) and half-family-phenotyped (the scenario's "related lines").
- Decision-facing output: ranked advancement list on five criteria, with weight sensitivity.

## Risks

- Leakage: none across years; the 2008 phenotypes are used only for scoring.
- Sampling bias: 2008 populations are 71% new; accuracy tracks pedigree connection.
- Biological plausibility: family mean dominates the within-family term, as expected for one season of testcross data.
- Deployment: the family-sampling rule needs every family to get at least ~15 lines in the field.

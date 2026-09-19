# Pitch outline

See `deck/OUTLINE.md` for the ten slides, owners and figures. The arc in one paragraph:

It is January 2008 and the plots are cut. The obvious idea is to predict every line from its genotype
and skip the field. We tried it, scored against the real 2008 season, and it works only weakly
(r = 0.14, +1.7 bu/ac of +12.7 possible). The thing that works is the family: phenotype a tenth of
each family and predict the rest from the family mean, and you get +3.9 bu/ac for a tenth of the plots.
Markers earn their keep on moisture and test weight, and on families with no plots at all. So the
recommendation is a plot-allocation rule, not a model: never drop a family, sample every one thinly,
predict broad-acre performance, and advance on a five-trait index whose weights the breeder can move.

## Final checks

- [ ] The problem is understandable in 30 seconds.
- [ ] Every number on a slide is in `results_summary/` and was reproduced on a second machine.
- [ ] The validation split matches how the tool would be used (leave-2008-out, half-family).
- [ ] The demo has a recorded fallback.
- [ ] The talk fits the time limit with margin.

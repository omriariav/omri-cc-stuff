# Laplace Smoothing

A worked sample demonstrating inline (`$…$`) and display (`$$…$$`) LaTeX, fractions,
subscripts, Greek letters, and `\text{}` — the constructs that survive Google's
OMML import as native, editable equations.

Try it: `/gdoc-math <this-file>` → opens a Google Doc with editable equations.

## The zero-probability problem

The standard way to estimate a probability is the maximum-likelihood ratio:

$$P(x_i) = \frac{\text{count}(x_i)}{N}$$

If an event $x_i$ never occurs in the data its count is $0$, so $P(x_i) = 0$ — which
breaks any model that multiplies probabilities together (e.g. Naive Bayes).

## Add-one (Laplace) smoothing

Pretend every outcome was seen once more than it actually was:

$$P(x_i) = \frac{\text{count}(x_i) + 1}{N + k}$$

where $N$ is the total number of observations and $k$ is the number of possible outcomes.

## Add-$\alpha$ (Lidstone) generalization

Adding a tunable $\alpha$ instead of $1$ gives the general additive-smoothing formula:

$$P(x_i) = \frac{\text{count}(x_i) + \alpha}{N + \alpha \cdot k}$$

- $\alpha = 1$ → Laplace smoothing
- $\alpha = 0$ → no smoothing
- $0 < \alpha < 1$ → Lidstone smoothing

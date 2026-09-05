# Maturity Assessment

Decide whether a technology is ready for the user's adoption context.

## 1. Define the adoption context

Identify the exact technology/version, intended workload, migration context, operational
constraints, and risk tolerance. Identify which adoption conditions are mandatory:
security maintenance, permitted licensing, data handling, recovery, and exit or migration
feasibility where relevant. Continue immediately when these are already clear.

**Complete when:** success and unacceptable adoption risk are concrete enough to judge.

## 2. Research maturity

Search and read evidence across:

- named production adoption and scale;
- ecosystem breadth and critical integrations;
- contributor activity, governance, and support;
- release stability, breaking changes, and LTS policy;
- documentation quality;
- funding, stewardship, roadmap, and adoption trajectory.

Prioritize official release/governance material and named production case studies;
balance project claims with independent operational experience.

**Complete when:** every dimension has current evidence or an explicit evidence gap, and
the evidence reflects the user's workload rather than generic popularity. For each
applicable mandatory condition, record verified pass, verified fail, or unresolved with
the decisive evidence or missing verification.

## 3. Calibrate the recommendation

Use this scale:

- **ADOPT:** proven for comparable production use, stable, well-supported, and low-risk.
- **TRIAL:** promising and functional; validate it in the user's context before commitment.
- **ASSESS:** worth watching or exploring in a bounded spike, but not ready for a production bet.
- **HOLD:** material risks or stronger alternatives make new adoption inadvisable.

Treat ADOPT and HOLD as strong claims. A verified failure of a mandatory adoption
condition requires HOLD for that production use. An unresolved mandatory condition
prevents ADOPT: use TRIAL only if a bounded, safe evaluation can resolve it; otherwise
use ASSESS. Popularity or strengths in other dimensions cannot compensate for a blocker.
Identify the evidence or milestone that would change the recommendation.

For TRIAL, specify the representative workload, baseline, success thresholds, duration,
and rollback or exit conditions. Use the user's constraints for thresholds; label any
proposed assumptions. State which uncertainty each test resolves and what outcome leads
to adoption, further assessment, or rejection. Keep the trial outside production exposure
when a mandatory safety or data-handling condition is still unresolved.

**Complete when:** the rating follows from every material dimension and matches the
user's risk tolerance.

## 4. Deliver

Default to a medium-length assessment. Use the scorecard as the single source of truth
for the six maturity dimensions, and reserve prose for the evidence and risks that drive
the recommendation. Add dimension-by-dimension evidence notes only when the user asks
for an expanded assessment.

Include:

1. the ADOPT/TRIAL/ASSESS/HOLD recommendation and direct rationale;
2. an evidenced scorecard for adoption, ecosystem, community, stability,
   documentation, and trajectory;
3. named production evidence, decisive strengths and risks, and mandatory-condition
   verification states;
4. alternatives and when to prefer them;
5. the conditions that would change the rating and a concrete validation plan for TRIAL;
6. annotated sources.

**Complete when:** every scorecard signal is evidenced, risks are specific to the user's
context, alternatives are actionable, and material factual claims are cited.

# SXF AI Agent Lab – Test 02 Evaluation Report

**Evaluation time:** 2026-11-03 12:00 UTC  **Source:** `SXF_AI_Agent_Lab_Test_02.xlsx` (read-only; not modified)

## 1. Method
- Baseline = `Tasks` sheet (10 tasks, T201–T210).
- `Updates` timestamps are stored as Excel serial numbers (e.g. 46329.5 = 2026-11-03 12:00 UTC). I converted them to UTC datetimes and sorted by time, ignoring row order.
- Per (Task ID, Field) the latest event with timestamp ≤ cutoff was applied. Cutoff is inclusive; no event falls exactly on the cutoff.

## 2. Update events (11 total)
| Row | Time (UTC) | Task | Field → Value | Result |
|---|---|---|---|---|
| 12 | 11-02 14:00 | T208 | Owner → Sam | Superseded by row 7 |
| 5 | 11-02 16:00 | T204 | Due date → 2026-11-06 | **Applied** |
| 2 | 11-03 08:00 | T205 | Status → Blocked | **Applied** (note: approval needed; cause not specified) |
| 9 | 11-03 08:30 | T210 | Status → Blocked | Superseded by row 4 |
| 6 | 11-03 09:00 | T202 | Status → Done | **Applied** |
| 10 | 11-03 09:30 | T999 | Status → Done | **FLAGGED – unknown task ID, not applied** |
| 8 | 11-03 10:00 | T209 | Due date → 2026-11-02 | **Applied** |
| 7 | 11-03 10:30 | T208 | Owner → Rana | **Applied** |
| 4 | 11-03 11:00 | T210 | Status → In Progress | **Applied** |
| 3 | 11-03 15:00 | T206 | Status → Done | **FLAGGED – after cutoff, not applied** |
| 11 | 11-04 08:00 | T201 | Status → Done | **FLAGGED – after cutoff, not applied** |

Totals: 6 applied, 2 superseded (eligible but not latest), 1 unknown ID, 2 after cutoff.

## 3. Updated task state
| ID | Task | Owner | Status | Due | Hrs | Flags |
|---|---|---|---|---|---|---|
| T201 | Landing page QA | Rana | In Progress | 2026-11-01 | 6 | Overdue |
| T202 | SEO audit | Sara | **Done** | 2026-11-02 | 4* | – |
| T203 | Pricing review | Sam | Open | 2026-11-05 | 2 | – |
| T204 | Fix broken links | Rana | Blocked | **2026-11-06** | 5 | Blocked |
| T205 | Newsletter integration | Sara | **Blocked** | 2026-11-02 | 3 | Overdue, Blocked |
| T206 | Customer survey | Sam | In Progress | 2026-11-03 | 7 | Due today |
| T207 | Release notes | Sara | Done | 2026-11-02 | 0 | – |
| T208 | Analytics dashboard | **Rana** | Open | 2026-11-04 | 8 | – |
| T209 | Email automation | Rana | Open | **2026-11-02** | 4 | Overdue |
| T210 | API integration | Sam | **In Progress** | 2026-11-03 | 6 | Due today |

\*T202 is Done but its stated remaining hours (4) were not changed by any event; the figure is kept in the CSV as stated but excluded from workload.

## 4. Findings
- **Overdue and unfinished (due < 2026-11-03):** T201 (Rana, 6h, due 11-01), T205 (Sara, 3h, due 11-02, also blocked), T209 (Rana, 4h, due 11-02; its due date was corrected to an earlier date by an eligible event). T202 and T207 are Done, so not overdue.
- **Currently blocked:** T204 (Rana, due 11-06, extension approved) and T205 (Sara, "approval needed; cause not specified"). T210 is **not** blocked; its later In Progress event replaced the earlier Blocked one.
- **Unfinished and due today (2026-11-03):** T206 (Sam, 7h) and T210 (Sam, 6h). T206's Done event is timestamped 15:00 UTC, after the cutoff, so as of 12:00 it is still In Progress.

## 5. Workload vs capacity (unfinished tasks only, updated owners)
| Owner | Tasks counted | Remaining hrs | Capacity through 11-10 | Balance |
|---|---|---|---|---|
| Rana | T201, T204, T208, T209 | 6+5+8+4 = **23** | 16 | **−7 (over)** |
| Sara | T205 | **3** | 6 | **+3 (spare)** |
| Sam | T203, T206, T210 | 2+7+6 = **15** | 12 | **−3 (over)** |
| **Total** | | **41** | **34** | **−7** |

Blocked tasks (T204, T205) are included because they are unfinished and still carry stated hours.

## 6. Recommended action plan
Based only on the data above; no dependencies or causes are assumed.
1. **Sam – today:** T206 and T210 are due today (13h combined). Confirm status of both with Sam now, since Sam's total load (15h) already exceeds capacity (12h).
2. **Rana – overdue work:** T201 (6h) and T209 (4h) are overdue. Confirm whether these can be completed first or need a new date; Rana is 7h over capacity.
3. **Resolve T205 (overdue and blocked):** the only information is "approval needed; cause not specified". Ask the owner (Sara) or requester what approval is needed and from whom. Its 3h cannot be planned until the block is cleared.
4. **T204 (blocked, due 11-06):** find out what is blocking it before the new due date. The cause is not stated in the data.
5. **Rebalance capacity:** the team is 7h over in total (41h vs 34h), and Sara's 3h spare covers only part of Rana's and Sam's 10h combined overage. A manager should decide whether to move work to Sara (skills and fit are unknown), extend dates, or reduce scope. The data supports no more specific assignment.
6. **Data hygiene:** investigate the T999 event, and re-check the T206 and T201 Done events once their timestamps are reached. If those later events are accurate, Sam's load drops by 7h and Rana's by 6h.

## 7. Verification
- Workload re-derived two ways (script grouping by owner, and manual sums above); both agree: Rana 23, Sara 3, Sam 15.
- Event timestamps converted from serials (epoch 1899-12-30) and matched to the workbook's own scenario (cutoff serial 46329.5; the "after snapshot" notes align with the 15:00 and 11-04 events).
- Original workbook was only read, never written.

## 8. Limitations
- Capacity is a total through 2026-11-10, not per day, so same-day feasibility cannot be assessed.
- Remaining hours are taken as stated; no updates changed them. T202's stated 4h on a Done task is a data inconsistency, handled by excluding it.
- The blocked cause for T204 and T205 is unknown, and no dependencies exist in the data.
- "Due today" and "overdue" are date-only comparisons against 2026-11-03; no due times are given.
- Skills, priorities, and business impact are not in the workbook, so the plan is ordered by due date, status, and capacity only.
- Future-dated events (T206, T201) are not applied, as instructed, even though they may reflect reality later in the day.
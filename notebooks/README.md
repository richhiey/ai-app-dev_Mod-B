# Module B Live Colab notebooks

Use one personal notebook copy per sprint. LS01–LS12 teach core service concepts through separate Colab practice; LS13–LS14 apply the concepts to the local FieldCare companion UI. No Campus project is required to start the first three Live notebooks.

| Sprint | Sessions | Open in Colab | Notebook role |
|---|---|---|---|
| 1 | LS01–LS04 | [Service foundations](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_1/sprint_1_live_workshops.ipynb) | Trace requests, author an endpoint, compare contracts and independent version bindings. |
| 2 | LS05–LS08 | [Authentication, limits and secrets](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_2/sprint_2_live_workshops.ipynb) | Caller authentication, per-key admission windows, synthetic secret-leak prevention. |
| 3 | LS09–LS12 | [Streaming, logs and evaluation](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_3/sprint_3_live_workshops.ipynb) | Stream semantics, learner logging attachment, safe records and the original Module A evaluator. |
| 4 | LS13–LS14 | [UI integration and API observer](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_4/sprint_4_fieldcare_live.ipynb) | Local UI planning/evidence card plus optional direct hosted API observation. |

## Before class

1. Save a personal copy in Colab. Use a Python CPU runtime. Follow the named session entry points; independent tasks require source edits, so **Run all is not a completion workflow**.
2. Run setup once. It clones current course `main`, installs the locked dependencies and prints the source revision. Keep that revision with your observations.
3. For Sprints 1–3, edit only your printed `PROJECT` folder. Save notebook notes and download the final Live workspace ZIP after each session. Notebook saving alone does not preserve Files-panel source edits.
4. To resume on a fresh runtime, upload your Live ZIP, choose a new destination and supply the recorded model choices as instructed. A Campus export is a different artifact. Review restored Python source before starting it.
5. Leave provider switches off until the instructor prepares that path. Health, validation, clarification, quota behavior and synthetic checks do not establish generation. A skipped check remains pending.

Sprint 4's optional observer requires a separately provisioned HTTPS service and caller credential. It cannot reach your laptop's localhost or validate the browser/connector. The local UI workflow is the required path, with one form, one response display and one logged interaction. No separate Supabase setup or public deployment is required.

See each sprint README for session entry points, expected observations and recovery. [Saving and transfer](../docs/live-handoff.md) explains the boundary between Live practice and Campus project work. The separate Sprint 1 Campus checkpoint notebook is not one of these four Live notebooks.

# Make requests and inspect what happened

Run these modules from the repository root with your virtual-environment Python. Keep the server running in another terminal.

| Command | What you edit or inspect |
|---|---|
| `python -m clients.request` | Choose `CALLER`, `PATH` and `BODY`; inspect status and response |
| `python -m clients.burst` | Fill your own ordered `REQUESTS` list after predicting results |
| `python -m clients.stream` | Watch actual event arrivals and the terminal outcome |
| `python -m clients.logs REQUEST_ID` | Find the safe record belonging to one actual request |
| `python -m clients.evaluate CASE_ID COMPANION_CASE_ID` | Inspect original cases and evaluate the reference design |

`common.py` loads caller values from `.env` and maps labels to configuration names. It never prints keys. The HTTP calls themselves remain visible in each client. These files are small enough to adapt: save changes, then rerun the module. A new client process does not reset a running server's limiter.

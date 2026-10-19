# Legacy simulator (superseded)

`simulate_twinguard.py` is the earlier parameterized simulator. It used a
normalized 47.3 ms latency, an assumed 847 req/s request rate, author-selected
TEE overheads and hard-coded baseline/throughput values. It is kept only for
history and is **not** used by the paper.

The paper's results are produced by `../project_twinguard_trace.py`, which is
driven by the 1.2 M measured RTX 5090 request traces in `data/raw/rtx5090/` and
by TEE overhead ranges measured in the literature.

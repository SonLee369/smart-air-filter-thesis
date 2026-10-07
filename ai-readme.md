# AI features on the baseline

First AI experiments for the Group 63 thesis, run on the baseline node (ESP32-WROOM-32, 30-pin).

| Feature | Where | What it shows |
|---|---|---|
| F1 Kalman filter | `node_esp32/kalman.h`, wired into `node_esp32.ino` | Smoother sensor readings, with the noise reduction measured live |
| F2 Edge AI benchmark | `ai/ai_bench_esp32/` + `ai/bench/` | Whether the ESP32 can run the thesis models: latency, memory and correctness, plain C float32 vs TFLite Micro int8 |

## Python environment

The system Python blocks `pip --user` (PEP 668), so the tools live in a project venv. It also sees the user-installed PyTorch.

```bash
uv venv --system-site-packages --python 3.12 ai/.venv
```
```bash
VIRTUAL_ENV=ai/.venv uv pip install scikit-learn tensorflow-cpu
```

Arduino library for TFLite Micro: `Chirale_TensorFLowLite` 2.0.0. The older `TensorFlowLite_ESP32` 1.0.0 does not compile with ESP32 core 3.x.

## F1: Kalman filter

There is one 1-D Kalman filter per channel (CO in/out, PM in/out). It uses a random-walk model, with Q and R set in `node_esp32/config.h` (`KF_*`). Innovations beyond 4σ are down-weighted, so single GP2Y/MQ-7 spikes are ignored.

Serial commands on the node:

| Command | Effect |
|---|---|
| `kf` | Print the noise reduction per channel over the last 30 samples (60 s) |
| `kf on` | Control logic uses the filtered values |
| `kf off` | Control logic uses the raw values (default, baseline behaviour) |

The status output gets a 4th line: `KF CO in/out  PM in/out  noise -x%/-y% (shadow|control)`.

**Host test** on a synthetic signal with known truth (`ai/bench/kalman_host_test.cpp`):

| Setting | RMSE raw (µg/m³) | RMSE filtered | Noise removed | 90% step rise |
|---|---|---|---|---|
| config.h (Q=4, R=100, gate 4σ) | 29.9 | 4.2 | 86% | 12 s |
| Faster (Q=16) | 29.9 | 4.9 | 73% | 6 s |
| No spike gate | 29.9 | 10.5 | 86% | (spike artefact) |

The trade-off: a smoother signal arrives later. 12 s is acceptable while the controller decides every 10 s; raise Q if faster reaction matters more.

```bash
g++ -O2 -I node_esp32 ai/bench/kalman_host_test.cpp -o /tmp/kt && /tmp/kt
```

## F2: Edge AI benchmark

1. Generate the models. Weights are random, because this measures the runtime, not the prediction quality:
   ```bash
   ai/.venv/bin/python ai/bench/make_bench_models.py
   ```
2. Check the plain C inference against Keras on the PC. All models agree to about 1e-7:
   ```bash
   g++ -O2 -I ai/ai_bench_esp32 ai/bench/host_test.cpp -o /tmp/ht && /tmp/ht
   ```
3. Build and flash the benchmark, then read the serial output (115200 baud). It prints a markdown table plus `CSV,` lines:
   ```bash
   arduino-cli compile --fqbn esp32:esp32:esp32 ai/ai_bench_esp32
   ```
   ```bash
   arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 ai/ai_bench_esp32
   ```
   Add `--build-property "compiler.cpp.extra_flags=-DBENCH_TFLM=0"` to build without TFLite Micro and measure its flash cost.

The benchmark **replaces the node firmware** while it runs; flash `node_esp32` again afterwards.

| Model | Shape | Parameters | float32 bytes | int8 TFLite bytes |
|---|---|---|---|---|
| mlp_s | 30 → 32 → 32 → 1 | 2,081 | 8,324 | 4,600 |
| mlp_m | 60 → 64 → 64 → 1 | 8,129 | 32,516 | 11,368 |
| cnn | Conv1D 16×3, 16×3, avg pool, dense | 961 | 3,844 | 5,712 |
| gru | GRU(32) over 30 steps × 3 features (C only) | 3,585 | 14,340 | - |
| plant | 8 → 16 → 1 (MPC plant model) | 161 | 644 | - |

// Host test of node_esp32/kalman.h (AI feature F1) on a synthetic signal with known truth.
// PM: 35 ug/m3, step to 80 at sample 150, Gaussian noise (std 10), 3 % spikes of +150.
// Build and run:  g++ -O2 -I node_esp32 ai/bench/kalman_host_test.cpp -o /tmp/kt && /tmp/kt
#include <stdio.h>
#include <random>
#include "kalman.h"
#include "config.h"

int main() {
  std::mt19937 gen(63);
  std::normal_distribution<float> noise(0.0f, 10.0f);
  std::uniform_real_distribution<float> u(0.0f, 1.0f);
  const int N = 300, step = 150;

  struct Cfg { const char* name; float q, r, gate; } cfgs[] = {
      {"config.h (Q=4, R=100, gate 4)", KF_PM_Q, KF_PM_R, KF_GATE_SIGMA},
      {"faster (Q=16, R=100, gate 4)", 16.0f, KF_PM_R, KF_GATE_SIGMA},
      {"no spike gate (Q=4, R=100)", KF_PM_Q, KF_PM_R, 1e9f},
  };
  float truth[N], z[N];
  for (int i = 0; i < N; i++) {
    truth[i] = i < step ? 35.0f : 80.0f;
    z[i] = truth[i] + noise(gen) + (u(gen) < 0.03f ? 150.0f : 0.0f);
  }
  printf("%-32s %9s %9s %10s %14s\n", "filter", "RMSE raw", "RMSE kf", "noise -%", "90% rise (s)");
  for (auto& c : cfgs) {
    Kalman1D kf(c.q, c.r, c.gate);
    double se0 = 0, se1 = 0;
    int rise = -1;
    for (int i = 0; i < N; i++) {
      float x = kf.update(z[i]);
      if (i >= 20) {                        // skip the start-up transient
        se0 += (z[i] - truth[i]) * (z[i] - truth[i]);
        se1 += (x - truth[i]) * (x - truth[i]);
      }
      if (i >= step && rise < 0 && x >= 35 + 0.9f * 45) rise = i - step;
    }
    int n = N - 20;
    printf("%-32s %9.1f %9.1f %10.0f %14d\n", c.name, sqrt(se0 / n), sqrt(se1 / n),
           kf.noiseReduction(), rise * 2);
  }
  return 0;
}

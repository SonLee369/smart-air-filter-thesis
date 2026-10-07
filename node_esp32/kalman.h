// kalman.h - 1-D Kalman filter per sensor channel (AI feature F1).
// Model: the true concentration is a random walk, x_k = x_{k-1} + w (variance Q),
// measured as z_k = x_k + v (variance R). One filter per channel; Q and R live in
// config.h. A gate inflates R for samples far from the prediction, so a single
// GP2Y/MQ-7 spike does not drag the estimate.
#pragma once
#include <math.h>

#define KF_STATS_N 30   // samples used for the noise statistic (60 s at 2 s)

struct Kalman1D {
  float q, r;           // process and measurement noise variance
  float gate;           // innovations beyond gate * sigma are down-weighted
  float x = NAN;        // estimate
  float p = 0;          // estimate variance

  // Noise statistic: std of successive differences, raw vs filtered.
  float dRaw[KF_STATS_N] = {}, dFilt[KF_STATS_N] = {};
  int n = 0, idx = 0;
  float lastRaw = NAN, lastFilt = NAN;

  Kalman1D(float q_, float r_, float gate_) : q(q_), r(r_), gate(gate_) {}

  float update(float z) {
    if (!isfinite(z)) return x;
    if (isnan(x)) {                      // first sample initialises the filter
      x = z;
      p = r;
    } else {
      p += q;                            // predict
      float innov = z - x;
      float s = p + r;
      float rEff = r;
      if (innov * innov > gate * gate * s) rEff = r * (innov * innov) / (gate * gate * s);
      float k = p / (p + rEff);          // update
      x += k * innov;
      p *= (1 - k);
    }
    if (isfinite(lastRaw)) {
      dRaw[idx] = z - lastRaw;
      dFilt[idx] = x - lastFilt;
      idx = (idx + 1) % KF_STATS_N;
      if (n < KF_STATS_N) n++;
    }
    lastRaw = z;
    lastFilt = x;
    return x;
  }

  static float stdOf(const float* v, int n) {
    if (n < 2) return NAN;
    float m = 0, s = 0;
    for (int i = 0; i < n; i++) m += v[i];
    m /= n;
    for (int i = 0; i < n; i++) s += (v[i] - m) * (v[i] - m);
    return sqrtf(s / (n - 1));
  }

  // Percentage drop of high-frequency noise, NAN until enough samples.
  float noiseReduction() const {
    float a = stdOf(dRaw, n), b = stdOf(dFilt, n);
    if (!isfinite(a) || a <= 0) return NAN;
    return (1 - b / a) * 100.0f;
  }
};

// c_infer.h - plain C float32 inference for the benchmark models (AI feature F2).
// No libraries: dense, 1-D convolution and GRU written out so every line can be
// explained in the thesis. Weight layouts match ai/bench/make_bench_models.py.
// Compiles on the ESP32 and on a PC (host test: ai/bench/host_test.cpp).
#pragma once
#include <math.h>
#include "models_c.h"

static inline float relu(float v) { return v > 0 ? v : 0; }
static inline float sigm(float v) { return 1.0f / (1.0f + expf(-v)); }

// y[o] = b[o] + sum_i W[o][i] x[i]
static void dense(const float* W, const float* b, const float* x, float* y, int nin, int nout, bool act) {
  for (int o = 0; o < nout; o++) {
    const float* w = W + o * nin;
    float s = b[o];
    for (int i = 0; i < nin; i++) s += w[i] * x[i];
    y[o] = act ? relu(s) : s;
  }
}

// 'valid' 1-D convolution: x[L][cin] -> y[L-k+1][cout], W[cout][k][cin]
static void conv1d(const float* W, const float* b, const float* x, float* y,
                   int L, int cin, int cout, int k, bool act) {
  int lout = L - k + 1;
  for (int t = 0; t < lout; t++)
    for (int o = 0; o < cout; o++) {
      float s = b[o];
      const float* w = W + o * k * cin;
      for (int j = 0; j < k; j++)
        for (int c = 0; c < cin; c++) s += w[j * cin + c] * x[(t + j) * cin + c];
      y[t * cout + o] = act ? relu(s) : s;
    }
}

// Keras GRU (reset_after=True), gate order z, r, h. x[T][nin] -> h[u]
static void gru(const float* Wk, const float* Uk, const float* bi, const float* br,
                const float* x, int T, int nin, int u, float* h) {
  static float gx[3 * 64], gh[3 * 64], hn[64];   // supports u <= 64
  for (int j = 0; j < u; j++) h[j] = 0;
  for (int t = 0; t < T; t++) {
    dense(Wk, bi, x + t * nin, gx, nin, 3 * u, false);
    dense(Uk, br, h, gh, u, 3 * u, false);
    for (int j = 0; j < u; j++) {
      float z = sigm(gx[j] + gh[j]);
      float r = sigm(gx[u + j] + gh[u + j]);
      float c = tanhf(gx[2 * u + j] + r * gh[2 * u + j]);
      hn[j] = z * h[j] + (1 - z) * c;
    }
    for (int j = 0; j < u; j++) h[j] = hn[j];
  }
}

// ---------------- the benchmark models ----------------
static float run_mlp_s(const float* x) {
  float a[32], b[32], y;
  dense(mlp_s_d0_w, mlp_s_d0_b, x, a, 30, 32, true);
  dense(mlp_s_d1_w, mlp_s_d1_b, a, b, 32, 32, true);
  dense(mlp_s_d2_w, mlp_s_d2_b, b, &y, 32, 1, false);
  return y;
}

static float run_mlp_m(const float* x) {
  float a[64], b[64], y;
  dense(mlp_m_d0_w, mlp_m_d0_b, x, a, 60, 64, true);
  dense(mlp_m_d1_w, mlp_m_d1_b, a, b, 64, 64, true);
  dense(mlp_m_d2_w, mlp_m_d2_b, b, &y, 64, 1, false);
  return y;
}

static float run_cnn(const float* x) {
  static float a[28 * 16], b[26 * 16];
  float g[16], y;
  conv1d(cnn_c0_w, cnn_c0_b, x, a, 30, 3, 16, 3, true);
  conv1d(cnn_c1_w, cnn_c1_b, a, b, 28, 16, 16, 3, true);
  for (int o = 0; o < 16; o++) {                       // global average pooling
    float s = 0;
    for (int t = 0; t < 26; t++) s += b[t * 16 + o];
    g[o] = s / 26;
  }
  dense(cnn_d3_w, cnn_d3_b, g, &y, 16, 1, false);
  return y;
}

static float run_gru(const float* x) {
  float h[32], y;
  gru(gru_g0_wk, gru_g0_uk, gru_g0_bi, gru_g0_br, x, 30, 3, 32, h);
  dense(gru_d1_w, gru_d1_b, h, &y, 32, 1, false);
  return y;
}

static float run_plant(const float* x) {
  float a[16], y;
  dense(plant_d0_w, plant_d0_b, x, a, 8, 16, true);
  dense(plant_d1_w, plant_d1_b, a, &y, 16, 1, false);
  return y;
}

// ---------------- MPC search workloads ----------------
// Rolls the plant model forward H steps for a duty sequence and returns the cost
// J = sum(PM) + lambda * sum(duty) + mu * sum(delta duty^2). x0 = current features.
static float mpc_rollout(const float* x0, const float* duty, int H, float lambda, float mu, float uPrev) {
  float x[8], J = 0;
  for (int i = 0; i < 8; i++) x[i] = x0[i];
  for (int k = 0; k < H; k++) {
    x[2] = duty[k];
    float pm = run_plant(x);
    x[3] = pm;                                         // predicted PM feeds the next step
    float du = duty[k] - (k ? duty[k - 1] : uPrev);
    J += pm + lambda * duty[k] + mu * du * du;
  }
  return J;
}

// A: hold one of nLevels duties for the whole horizon (nLevels x H plant calls)
static float mpc_search_const(const float* x0, int nLevels, int H, float uPrev) {
  float best = INFINITY, bestU = 0, seq[16];
  for (int l = 0; l < nLevels; l++) {
    float u = (float)l / (nLevels - 1);
    for (int k = 0; k < H; k++) seq[k] = u;
    float J = mpc_rollout(x0, seq, H, 0.5f, 0.2f, uPrev);
    if (J < best) { best = J; bestU = u; }
  }
  return bestU;
}

// B: every sequence of 3 levels over H steps (3^H x H plant calls)
static float mpc_search_tree(const float* x0, int H, float uPrev) {
  const float lv[3] = {0.2f, 0.5f, 0.8f};
  int total = 1;
  for (int k = 0; k < H; k++) total *= 3;
  float best = INFINITY, bestU = 0, seq[16];
  for (int c = 0; c < total; c++) {
    int v = c;
    for (int k = 0; k < H; k++) { seq[k] = lv[v % 3]; v /= 3; }
    float J = mpc_rollout(x0, seq, H, 0.5f, 0.2f, uPrev);
    if (J < best) { best = J; bestU = seq[0]; }
  }
  return bestU;
}

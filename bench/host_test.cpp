// Host check of the plain C inference against the Keras reference outputs.
// Build and run:  g++ -O2 -I ai/ai_bench_esp32 ai/bench/host_test.cpp -o /tmp/ht && /tmp/ht
#include <stdio.h>
#include "c_infer.h"
#include "bench_data.h"

static float check(const char* name, float (*fn)(const float*), const float* x, const float* ref, int n) {
  float worst = 0;
  for (int i = 0; i < BENCH_N_TEST; i++) {
    float e = fabsf(fn(x + i * n) - ref[i]);
    if (e > worst) worst = e;
  }
  printf("%-6s max |C - Keras| = %.2e  %s\n", name, worst, worst < 1e-4f ? "OK" : "MISMATCH");
  return worst;
}

int main() {
  float w = 0;
  w = fmaxf(w, check("mlp_s", run_mlp_s, mlp_s_x, mlp_s_y_ref, 30));
  w = fmaxf(w, check("mlp_m", run_mlp_m, mlp_m_x, mlp_m_y_ref, 60));
  w = fmaxf(w, check("cnn", run_cnn, cnn_x, cnn_y_ref, 90));
  w = fmaxf(w, check("gru", run_gru, gru_x, gru_y_ref, 90));
  w = fmaxf(w, check("plant", run_plant, plant_x, plant_y_ref, 8));
  float x0[8] = {60, 40, 0.2f, 55, 70, 30, 1300, 8};
  printf("mpc const -> u = %.2f   mpc tree -> u = %.2f\n",
         mpc_search_const(x0, 11, 10, 0.2f), mpc_search_tree(x0, 5, 0.2f));
  return w < 1e-4f ? 0 : 1;
}

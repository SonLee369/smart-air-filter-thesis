// bench_util.h - timing helper (kept out of the .ino so the Arduino prototype
// generator does not mangle the template).
#pragma once
#include <esp_timer.h>

template <typename Fn>
static float timeUs(Fn fn, int runs) {
  int64_t t0 = esp_timer_get_time();
  for (int i = 0; i < runs; i++) fn(i);
  return (float)(esp_timer_get_time() - t0) / runs;
}

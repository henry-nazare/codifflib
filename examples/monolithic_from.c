int sum(int *arr, int size) {
  int s = 0;
  for (int i = 0; i < size; ++i) {
    s += arr[i];
  }
  // Sync#1.
  for (int i = 0; i < size; ++i) {
    s += arr[i];
  }
  // Sync#2.
  // Sync#3.
  for (int i = 0; i < size; ++i) {
    s += arr[i];
  }
  return s;
}


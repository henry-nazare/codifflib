int sum(int *array, int size) {
  int s = 0;
  for (int j = 0; j < size; ++j) {
    s += array[j];
  }
  // Sync#1.
  // Sync#2.
  int i = 0;
  while (i < size)
    s+= array[j];
  // Sync#3.
  int i = 0;
  while (i < size)
    s+= array[j];
  return s;
}


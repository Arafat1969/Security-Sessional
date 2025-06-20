/* Find the cache line size by running `getconf -a | grep CACHE` */
const LINESIZE = 64;

function readNlines(n) {
  /*
   * Implement this function to read n cache lines.
   * 1. Allocate a buffer of size n * LINESIZE.
   * 2. Read each cache line (read the buffer in steps of LINESIZE) 10 times.
   * 3. Collect total time taken in an array using `performance.now()`.
   * 4. Return the median of the time taken in milliseconds.
   */

  const buffer = new Uint8Array(n * LINESIZE);
  const times = [];

  for (let iter = 0; iter < 10; iter++) {
    const start = performance.now();
    for (let i = 0; i < buffer.length; i += LINESIZE) {
      buffer[i]; // Access each cache line
    }
    const end = performance.now();
    times.push(end - start);
  }

  times.sort((a, b) => a - b);
  return times[Math.floor(times.length / 2)];
}

self.addEventListener("message", function (e) {
  if (e.data === "start") {
    const results = {};

    /* Call the readNlines function for n = 1, 10, ... 10,000,000 and store the result */
    const limits = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000];

    for (let n of limits) {
      try {
        results[n] = readNlines(n);
      } catch (err) {
        break;
      }
    }
    self.postMessage(results);
  }
});

export async function mapBounded(items, limit, worker) {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new RangeError("concurrency limit must be a positive integer");
  }
  if (!Array.isArray(items) || items.length === 0) return [];
  const results = new Array(items.length);
  let cursor = 0;

  async function run() {
    while (true) {
      const index = cursor++;
      if (index >= items.length) return;
      results[index] = await worker(items[index], index);
    }
  }

  const width = Math.min(limit, items.length);
  await Promise.all(Array.from({length: width}, () => run()));
  return results;
}

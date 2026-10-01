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

export async function mapBoundedByKey(items, limit, keyOf, worker, perKeyLimit = 1) {
  if (!Number.isInteger(perKeyLimit) || perKeyLimit < 1) {
    throw new RangeError("per-key concurrency limit must be a positive integer");
  }
  const groups = new Map();
  for (let index = 0; index < items.length; index += 1) {
    const key = String(keyOf(items[index], index));
    const group = groups.get(key) ?? [];
    group.push({ item: items[index], index });
    groups.set(key, group);
  }

  const grouped = [...groups.values()];
  const results = new Array(items.length);
  await mapBounded(grouped, limit, async group => {
    if (perKeyLimit === 1) {
      for (const entry of group) results[entry.index] = await worker(entry.item, entry.index);
      return;
    }
    await mapBounded(group, perKeyLimit, async entry => {
      results[entry.index] = await worker(entry.item.item, entry.index);
    });
  });
  return results;
}

/** Admin login username: letter start; letters, digits, ._- ; length 3–64. */
const USERNAME = /^[A-Za-z][A-Za-z0-9._-]{2,63}$/;

export function normalizeUsername(value: string): string {
  return value.trim();
}

export function isValidUsername(value: string): boolean {
  const trimmed = normalizeUsername(value);
  if (!trimmed) return false;
  return USERNAME.test(trimmed);
}

/** Display names for API key holders: Latin letters + common separators only. */
const ENGLISH_DISPLAY_NAME = /^[A-Za-z]+(?:[ .'-][A-Za-z]+)*$/;

export function isEnglishDisplayName(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed || trimmed.length > 256) return false;
  return ENGLISH_DISPLAY_NAME.test(trimmed);
}

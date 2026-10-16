/** Rebrand only controlled legacy demo labels, retaining their source provenance. */
export function sourceDisplayLabel(label: string): string {
  return label.replace(/^CivicForge fictional demonstration catalogue(?= · |$)/, 'Adjust AI fictional demonstration catalogue')
    .replace(/^Bolton Connect(?= demonstration pathway data$| synthetic demonstration data$| \(synthetic demonstration data\)$)/, 'Adjust AI');
}

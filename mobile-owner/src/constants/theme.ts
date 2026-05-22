export const C = {
  cream: '#F5F0E8',
  cream2: '#EDE6D8',
  charcoal: '#1A1814',
  orange: '#E8500A',
  orange2: '#FF6B2B',
  green: '#16A34A',
  red: '#DC2626',
  mid: '#5C5548',
  muted: '#9C927F',
  white: '#FFFFFF',
  border: '#E4DAC8',
};

export const FONT = {
  h1: { fontSize: 28, fontWeight: '700' as const, color: C.charcoal, letterSpacing: -0.5 },
  h2: { fontSize: 22, fontWeight: '700' as const, color: C.charcoal, letterSpacing: -0.3 },
  h3: { fontSize: 17, fontWeight: '600' as const, color: C.charcoal },
  body: { fontSize: 14, color: C.mid, lineHeight: 22 },
  mono: { fontSize: 12, fontFamily: 'Menlo', color: C.mid },
  cap: { fontSize: 10, fontWeight: '700' as const, letterSpacing: 1.5, textTransform: 'uppercase' as const, color: C.muted },
};

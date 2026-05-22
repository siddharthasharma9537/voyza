import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { C } from '../constants/theme';

interface StatCardProps {
  label: string;
  value: string;
  icon: string;
  accent?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, icon, accent = C.orange }) => (
  <View style={[styles.card, { borderLeftColor: accent, borderLeftWidth: 4 }]}>
    <Text style={styles.icon}>{icon}</Text>
    <Text style={styles.value}>{value}</Text>
    <Text style={styles.label}>{label}</Text>
  </View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: C.white,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: C.border,
    flex: 1,
  },
  icon: { fontSize: 24, marginBottom: 6 },
  value: { fontSize: 18, fontWeight: '700', color: C.charcoal },
  label: { fontSize: 11, color: C.muted, marginTop: 2, fontWeight: '600' },
});

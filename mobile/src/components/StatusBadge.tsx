import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface StatusBadgeProps {
  status: string;
}

const STATUS_MAP: Record<string, { bg: string; color: string; label: string }> = {
  pending: { bg: '#FFF7ED', color: '#C2410C', label: 'Pending' },
  confirmed: { bg: '#F0FDF4', color: '#16A34A', label: 'Confirmed' },
  active: { bg: '#EFF6FF', color: '#1D4ED8', label: 'Active' },
  completed: { bg: '#F9FAFB', color: '#6B7280', label: 'Completed' },
  cancelled: { bg: '#FEF2F2', color: '#DC2626', label: 'Cancelled' },
  disputed: { bg: '#FFFBEB', color: '#92400E', label: 'Disputed' },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = STATUS_MAP[status] || STATUS_MAP.pending;
  return (
    <View style={[styles.badge, { backgroundColor: s.bg }]}>
      <Text style={[styles.text, { color: s.color }]}>{s.label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  text: {
    fontSize: 11,
    fontWeight: '700',
  },
});

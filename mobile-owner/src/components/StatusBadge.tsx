import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

const STATUS_MAP: Record<string, { bg: string; color: string; label: string }> = {
  draft: { bg: '#F3F4F6', color: '#4B5563', label: 'Draft' },
  pending: { bg: '#FFF7ED', color: '#C2410C', label: 'Pending' },
  confirmed: { bg: '#F0FDF4', color: '#16A34A', label: 'Confirmed' },
  active: { bg: '#EFF6FF', color: '#1D4ED8', label: 'Active' },
  approved: { bg: '#F0FDF4', color: '#16A34A', label: 'Approved' },
  rejected: { bg: '#FEF2F2', color: '#DC2626', label: 'Rejected' },
  suspended: { bg: '#F3F4F6', color: '#6B7280', label: 'Suspended' },
  completed: { bg: '#F9FAFB', color: '#6B7280', label: 'Completed' },
  cancelled: { bg: '#FEF2F2', color: '#DC2626', label: 'Cancelled' },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const s = STATUS_MAP[status] || { bg: '#F3F4F6', color: '#4B5563', label: status };
  return (
    <View style={[styles.badge, { backgroundColor: s.bg }, size === 'sm' && { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 }]}>
      <Text style={[styles.text, { color: s.color }, size === 'sm' && { fontSize: 9 }]}>
        {s.label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6 },
  text: { fontSize: 11, fontWeight: '700' },
});

import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { C } from '../constants/theme';

interface TagProps {
  label: string;
  active?: boolean;
  onPress?: () => void;
}

export const Tag: React.FC<TagProps> = ({ label, active, onPress }) => (
  <TouchableOpacity
    style={[styles.tag, active && styles.tagActive]}
    onPress={onPress}
    activeOpacity={0.7}
  >
    <Text style={[styles.tagText, active && styles.tagTextActive]}>{label}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  tag: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 100,
    borderWidth: 1.5,
    borderColor: C.border,
    backgroundColor: C.white,
  },
  tagActive: {
    backgroundColor: C.charcoal,
    borderColor: C.charcoal,
  },
  tagText: {
    fontSize: 13,
    fontWeight: '600',
    color: C.mid,
  },
  tagTextActive: {
    color: C.white,
  },
});

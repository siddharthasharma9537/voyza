import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { C } from '../constants/theme';

interface StarRowProps {
  rating: number;
  size?: number;
}

export const StarRow: React.FC<StarRowProps> = ({ rating, size = 14 }) => (
  <View style={{ flexDirection: 'row', gap: 2 }}>
    {[1, 2, 3, 4, 5].map((i) => (
      <Text key={i} style={{ fontSize: size, color: i <= Math.round(rating) ? '#F59E0B' : C.border }}>
        ★
      </Text>
    ))}
  </View>
);

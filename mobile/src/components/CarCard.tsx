import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Dimensions } from 'react-native';
import { Vehicle } from '../types';
import { C, FONT } from '../constants/theme';
import { StarRow } from './StarRow';

interface CarCardProps {
  car: Vehicle;
  onPress: () => void;
  compact?: boolean;
}

const { width: SCREEN_W } = Dimensions.get('window');

export const fmtMoney = (paise: number): string => {
  return '₹' + (paise / 100).toLocaleString('en-IN');
};

export const CarCard: React.FC<CarCardProps> = ({ car, onPress, compact }) => (
  <TouchableOpacity
    style={[styles.carCard, compact && styles.carCardCompact]}
    onPress={onPress}
    activeOpacity={0.85}
  >
    <View style={styles.carImgPlaceholder}>
      {car.primary_image ? (
        <Image source={{ uri: car.primary_image }} style={styles.carImage} resizeMode="cover" />
      ) : (
        <Text style={{ fontSize: compact ? 36 : 48 }}>🚗</Text>
      )}
    </View>
    <View style={{ padding: 14 }}>
      <Text style={[FONT.h3, { fontSize: compact ? 15 : 17 }]}>
        {car.make} {car.model}
      </Text>
      <Text style={[FONT.body, { fontSize: 12, marginTop: 2 }]}>
        {car.city} · {car.fuel_type} · {car.seating} seats
      </Text>
      {car.avg_rating != null && (
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6 }}>
          <StarRow rating={car.avg_rating} size={12} />
          <Text style={FONT.mono}>
            {car.avg_rating} ({car.review_count || 0})
          </Text>
        </View>
      )}
      <View style={styles.priceRow}>
        <View>
          <Text style={{ fontSize: 18, fontWeight: '700', color: C.charcoal }}>
            {fmtMoney(car.price_per_day)}
          </Text>
          <Text style={[FONT.mono, { fontSize: 10 }]}>per day</Text>
        </View>
        <View style={styles.orangeChip}>
          <Text style={{ color: C.white, fontSize: 11, fontWeight: '700' }}>
            {car.transmission}
          </Text>
        </View>
      </View>
    </View>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  carCard: {
    backgroundColor: C.white,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: C.border,
    width: SCREEN_W - 40,
  },
  carCardCompact: {
    width: SCREEN_W * 0.72,
  },
  carImgPlaceholder: {
    height: 180,
    backgroundColor: C.cream2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  carImage: {
    width: '100%',
    height: '100%',
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    alignItems: 'flex-end',
  },
  orangeChip: {
    backgroundColor: C.orange,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
});

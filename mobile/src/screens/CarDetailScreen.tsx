import React, { useState, useEffect } from 'react';
import {
  View, Text, SafeAreaView, ScrollView, StyleSheet, Image,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList, Vehicle } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { StarRow } from '../components/StarRow';
import { fmtMoney } from '../components/CarCard';

type DetailNav = StackNavigationProp<NavigationParamList, 'CarDetail'>;
type DetailRoute = RouteProp<NavigationParamList, 'CarDetail'>;

export const CarDetailScreen: React.FC = () => {
  const navigation = useNavigation<DetailNav>();
  const route = useRoute<DetailRoute>();
  const { car: initialCar } = route.params;
  const [detail, setDetail] = useState<Vehicle>(initialCar);
  const [reviews, setReviews] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      api.cars.detail(initialCar.id),
      api.cars.reviews(initialCar.id),
    ]).then(([d, r]: [any, any]) => {
      setDetail(d);
      setReviews(r || []);
    });
  }, [initialCar.id]);

  const specs = [
    ['Fuel', detail.fuel_type],
    ['Transmission', detail.transmission],
    ['Seating', `${detail.seating} persons`],
    ['Year', String(detail.year)],
    ...(detail.mileage_kmpl ? [['Mileage', `${detail.mileage_kmpl} kmpl`] as [string, string]] : []),
    ['Security deposit', fmtMoney(detail.security_deposit || 0)],
  ];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.detailImg}>
          {detail.primary_image ? (
            <Image source={{ uri: detail.primary_image }} style={styles.image} resizeMode="cover" />
          ) : (
            <Text style={{ fontSize: 80 }}>🚗</Text>
          )}
        </View>

        <View style={styles.container}>
          <View style={styles.headerRow}>
            <View style={{ flex: 1 }}>
              <Text style={FONT.h2}>{detail.make} {detail.model}</Text>
              <Text style={[FONT.body, { marginTop: 2 }]}>{detail.city} · {detail.color}</Text>
            </View>
            {detail.avg_rating != null && (
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={{ fontSize: 22, fontWeight: '700', color: C.charcoal }}>{detail.avg_rating}★</Text>
                <Text style={FONT.mono}>{detail.review_count} reviews</Text>
              </View>
            )}
          </View>

          <Card style={{ marginBottom: 20, flexDirection: 'row', justifyContent: 'space-around' }}>
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 22, fontWeight: '700', color: C.charcoal }}>{fmtMoney(detail.price_per_day)}</Text>
              <Text style={FONT.cap}>per day</Text>
            </View>
            <View style={{ width: 1, backgroundColor: C.border }} />
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 22, fontWeight: '700', color: C.charcoal }}>{fmtMoney(detail.price_per_hour || 0)}</Text>
              <Text style={FONT.cap}>per hour</Text>
            </View>
          </Card>

          <Text style={[FONT.cap, { marginBottom: 10 }]}>Specifications</Text>
          <Card style={{ marginBottom: 20 }}>
            {specs.map(([label, value]) => (
              <View key={label} style={styles.specRow}>
                <Text style={[FONT.body, { color: C.mid }]}>{label}</Text>
                <Text style={[FONT.body, { fontWeight: '600', color: C.charcoal }]}>{value}</Text>
              </View>
            ))}
          </Card>

          {detail.features && Object.keys(detail.features).length > 0 && (
            <>
              <Text style={[FONT.cap, { marginBottom: 10 }]}>Features</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
                {Object.entries(detail.features).map(([k, v]) => (
                  <View key={k} style={[styles.featureChip, !v && styles.featureChipOff]}>
                    <Text style={{ fontSize: 12, color: v ? C.green : C.muted, fontWeight: '600' }}>
                      {v ? '✓' : '✗'} {k.replace('_', ' ')}
                    </Text>
                  </View>
                ))}
              </View>
            </>
          )}

          {reviews.length > 0 && (
            <>
              <Text style={[FONT.cap, { marginBottom: 10 }]}>Reviews</Text>
              {reviews.slice(0, 3).map((r) => (
                <Card key={r.id} style={{ marginBottom: 10 }}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text style={[FONT.body, { fontWeight: '600', color: C.charcoal }]}>{r.reviewer}</Text>
                    <StarRow rating={r.rating} />
                  </View>
                  {r.comment && <Text style={FONT.body}>{r.comment}</Text>}
                  {r.owner_reply && (
                    <View style={{ marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: C.border }}>
                      <Text style={[FONT.cap, { marginBottom: 4 }]}>Owner reply</Text>
                      <Text style={[FONT.body, { fontStyle: 'italic' }]}>{r.owner_reply}</Text>
                    </View>
                  )}
                </Card>
              ))}
            </>
          )}

          <Button
            label="Book This Car →"
            onPress={() => navigation.navigate('Checkout', { car: detail })}
            style={{ marginBottom: 32 }}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  detailImg: {
    height: 260,
    backgroundColor: C.cream2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  specRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  featureChip: {
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#86EFAC',
  },
  featureChipOff: {
    backgroundColor: C.cream2,
    borderColor: C.border,
  },
});

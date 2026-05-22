import React, { useState, useEffect } from 'react';
import {
  View, Text, SafeAreaView, FlatList, ActivityIndicator, StyleSheet,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList, Booking } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { StatusBadge } from '../components/StatusBadge';
import { fmtMoney } from '../components/CarCard';

type BookingsNav = BottomTabNavigationProp<NavigationParamList> & StackNavigationProp<NavigationParamList>;

export const BookingsScreen: React.FC = () => {
  const navigation = useNavigation<BookingsNav>();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.bookings.list()
      .then((res: any) => setBookings(res || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={C.orange} />
      </View>
    );
  }

  const fmtDate = (iso: string) => new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <FlatList
        data={bookings}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        ListEmptyComponent={
          <View style={{ alignItems: 'center', justifyContent: 'center', marginTop: 80 }}>
            <Text style={{ fontSize: 48, marginBottom: 12 }}>🚗</Text>
            <Text style={FONT.h3}>No trips yet</Text>
            <Text style={[FONT.body, { marginTop: 4, marginBottom: 24 }]}>Book your first car to get started</Text>
            <Button label="Find a Car" onPress={() => navigation.navigate('Browse')} />
          </View>
        }
        renderItem={({ item: b }) => (
          <Card>
            <View style={{ flexDirection: 'row', gap: 14, alignItems: 'center' }}>
              <Text style={{ fontSize: 36 }}>🚗</Text>
              <View style={{ flex: 1 }}>
                <Text style={[FONT.h3, { fontSize: 15 }]}>{b.car_make} {b.car_model}</Text>
                <Text style={[FONT.mono, { marginTop: 2 }]}>
                  {fmtDate(b.pickup_time)} → {fmtDate(b.dropoff_time)}
                </Text>
              </View>
              <StatusBadge status={b.status} />
            </View>
            <View style={[styles.row, { marginTop: 12, borderTopWidth: 1, borderTopColor: C.border, paddingTop: 12 }]}>
              <Text style={[FONT.mono, { fontSize: 11 }]}>
                #{(b.id || '').slice(0, 8).toUpperCase()}
              </Text>
              <Text style={{ fontWeight: '700', fontSize: 16, color: C.charcoal }}>{fmtMoney(b.total_amount)}</Text>
            </View>
            {b.status === 'active' && (
              <Button label="Track Live" variant="outline" onPress={() => navigation.navigate('Tracking', { booking: b })} style={{ marginTop: 10 }} />
            )}
            {b.status === 'completed' && (
              <Button label="Rate this trip" variant="outline" onPress={() => navigation.navigate('Review', { booking: b })} style={{ marginTop: 10 }} />
            )}
          </Card>
        )}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
});

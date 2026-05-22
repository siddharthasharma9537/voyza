import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, SafeAreaView, FlatList, ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList, OwnerBooking } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { StatusBadge } from '../components/StatusBadge';
import { fmtMoney } from './DashboardScreen';

type Nav = StackNavigationProp<OwnerNavigationParamList, 'Bookings'>;

const FILTERS = ['all', 'pending', 'confirmed', 'active', 'completed', 'cancelled'];

export const BookingsScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const [bookings, setBookings] = useState<OwnerBooking[]>([]);
  const [filtered, setFiltered] = useState<OwnerBooking[]>([]);
  const [activeFilter, setActiveFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchBookings = async () => {
    try {
      const res: any = await api.owner.bookings();
      setBookings(res || []);
    } catch (e: any) { Alert.alert('Error', e.message); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => { setLoading(true); fetchBookings(); }, []));

  useEffect(() => {
    setFiltered(activeFilter === 'all' ? bookings : bookings.filter((b) => b.status === activeFilter));
  }, [bookings, activeFilter]);

  if (loading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={C.orange} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      {/* Filter strip */}
      <View style={{ backgroundColor: C.white, borderBottomWidth: 1, borderBottomColor: C.border }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 10, gap: 8 }}>
          {FILTERS.map((f) => (
            <TouchableOpacity
              key={f}
              style={[styles.filterChip, activeFilter === f && styles.filterChipActive]}
              onPress={() => setActiveFilter(f)}
            >
              <Text style={[styles.filterText, activeFilter === f && styles.filterTextActive]}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchBookings(); }} tintColor={C.orange} />}
        ListEmptyComponent={
          <View style={{ alignItems: 'center', justifyContent: 'center', marginTop: 80 }}>
            <Text style={{ fontSize: 48, marginBottom: 12 }}>📋</Text>
            <Text style={FONT.h3}>No bookings</Text>
          </View>
        }
        renderItem={({ item: b }) => (
          <TouchableOpacity onPress={() => navigation.navigate('BookingDetail', { booking: b })}>
            <Card>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <View style={{ flex: 1 }}>
                  <Text style={[FONT.h3, { fontSize: 15 }]}>{b.vehicle_make} {b.vehicle_model}</Text>
                  <Text style={[FONT.body, { fontSize: 12, marginTop: 2 }]}>{b.customer_name} · {b.customer_phone}</Text>
                  <Text style={[FONT.mono, { marginTop: 4 }]}>
                    {new Date(b.pickup_time).toLocaleDateString()} → {new Date(b.dropoff_time).toLocaleDateString()}
                  </Text>
                </View>
                <StatusBadge status={b.status} />
              </View>
              <View style={[styles.row, { marginTop: 10, borderTopWidth: 1, borderTopColor: C.border, paddingTop: 10 }]}>
                <Text style={FONT.mono}>#{b.id.slice(0, 8).toUpperCase()}</Text>
                <Text style={{ fontWeight: '700', fontSize: 15, color: C.charcoal }}>{fmtMoney(b.owner_earnings)}</Text>
              </View>
            </Card>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  filterChip: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 100, borderWidth: 1.5, borderColor: C.border, backgroundColor: C.white },
  filterChipActive: { backgroundColor: C.charcoal, borderColor: C.charcoal },
  filterText: { fontSize: 12, fontWeight: '600', color: C.mid },
  filterTextActive: { color: C.white },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
});

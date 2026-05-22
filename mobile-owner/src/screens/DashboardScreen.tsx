import React, { useState, useEffect } from 'react';
import { View, Text, SafeAreaView, ScrollView, ActivityIndicator, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList, EarningsSummary, OwnerBooking } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';
import { Card } from '../components/Card';
import { StatusBadge } from '../components/StatusBadge';

type Nav = BottomTabNavigationProp<OwnerNavigationParamList> & StackNavigationProp<OwnerNavigationParamList>;

export const fmtMoney = (paise: number): string => '₹' + (paise / 100).toLocaleString('en-IN');

export const DashboardScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [bookings, setBookings] = useState<OwnerBooking[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.owner.earnings(),
      api.owner.bookings(),
    ]).then(([e, b]: [any, any]) => {
      setSummary(e);
      setBookings((b || []).slice(0, 3));
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

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
      <ScrollView>
        <View style={styles.container}>
          <Text style={[FONT.cap, { marginBottom: 4 }]}>Welcome back 👋</Text>
          <Text style={FONT.h2}>Your Dashboard</Text>

          {/* Stats */}
          <View style={{ flexDirection: 'row', gap: 10, marginTop: 20, marginBottom: 8 }}>
            <StatCard label="Total Earnings" value={fmtMoney(summary?.total_earnings || 0)} icon="💰" />
            <StatCard label="This Month" value={fmtMoney(summary?.this_month || 0)} icon="📅" accent={C.green} />
          </View>
          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 24 }}>
            <StatCard label="Pending Payout" value={fmtMoney(summary?.pending_payout || 0)} icon="⏳" accent="#C2410C" />
            <StatCard label="Total Bookings" value={String(summary?.total_bookings || 0)} icon="📋" accent="#1D4ED8" />
          </View>

          {/* Quick Actions */}
          <Text style={[FONT.cap, { marginBottom: 12 }]}>Quick Actions</Text>
          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 24 }}>
            <TouchableOpacity style={[styles.actionBtn, { backgroundColor: C.charcoal }]} onPress={() => navigation.navigate('AddCar')}>
              <Text style={{ fontSize: 24, marginBottom: 4 }}>➕</Text>
              <Text style={{ color: C.white, fontWeight: '700', fontSize: 13 }}>Add Car</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionBtn, { backgroundColor: C.white, borderWidth: 1, borderColor: C.border }]} onPress={() => navigation.navigate('Bookings')}>
              <Text style={{ fontSize: 24, marginBottom: 4 }}>📋</Text>
              <Text style={{ color: C.charcoal, fontWeight: '700', fontSize: 13 }}>Bookings</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionBtn, { backgroundColor: C.white, borderWidth: 1, borderColor: C.border }]} onPress={() => navigation.navigate('Earnings')}>
              <Text style={{ fontSize: 24, marginBottom: 4 }}>💰</Text>
              <Text style={{ color: C.charcoal, fontWeight: '700', fontSize: 13 }}>Earnings</Text>
            </TouchableOpacity>
          </View>

          {/* Recent Bookings */}
          <Text style={[FONT.cap, { marginBottom: 12 }]}>Recent Bookings</Text>
          {bookings.length === 0 ? (
            <Card>
              <Text style={[FONT.body, { textAlign: 'center' }]}>No bookings yet. Add a car to get started.</Text>
            </Card>
          ) : (
            bookings.map((b) => (
              <TouchableOpacity key={b.id} onPress={() => navigation.navigate('BookingDetail', { booking: b })}>
                <Card style={{ marginBottom: 10 }}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                    <View>
                      <Text style={[FONT.h3, { fontSize: 15 }]}>{b.vehicle_make} {b.vehicle_model}</Text>
                      <Text style={[FONT.body, { fontSize: 12, marginTop: 2 }]}>{b.customer_name}</Text>
                    </View>
                    <StatusBadge status={b.status} />
                  </View>
                  <Text style={[FONT.mono, { marginTop: 6 }]}>{fmtMoney(b.owner_earnings)}</Text>
                </Card>
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingVertical: 16 },
  actionBtn: { flex: 1, borderRadius: 12, padding: 14, alignItems: 'center' },
});

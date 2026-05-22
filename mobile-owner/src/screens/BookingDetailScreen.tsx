import React, { useState, useEffect } from 'react';
import { View, Text, SafeAreaView, ScrollView, ActivityIndicator, Alert, StyleSheet } from 'react-native';
import { useRoute, RouteProp } from '@react-navigation/native';
import { OwnerNavigationParamList, OwnerBooking } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { StatusBadge } from '../components/StatusBadge';
import { fmtMoney } from './DashboardScreen';

type RouteType = RouteProp<OwnerNavigationParamList, 'BookingDetail'>;

export const BookingDetailScreen: React.FC = () => {
  const route = useRoute<RouteType>();
  const { booking: initial } = route.params;
  const [booking, setBooking] = useState<OwnerBooking>(initial);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.owner.bookingDetail(booking.id)
      .then((d: any) => setDetail(d))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [booking.id]);

  const handleAccept = async () => {
    try {
      await api.owner.acceptBooking(booking.id);
      Alert.alert('Accepted', 'Booking confirmed successfully');
      setBooking((p) => ({ ...p, status: 'confirmed' }));
    } catch (e: any) { Alert.alert('Error', e.message); }
  };

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
          <Text style={[FONT.h2, { marginBottom: 8 }]}>Booking Details</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 20 }}>
            <StatusBadge status={booking.status} />
            <Text style={FONT.mono}>#{booking.id.slice(0, 8).toUpperCase()}</Text>
          </View>

          <Card style={{ marginBottom: 16 }}>
            <Text style={[FONT.cap, { marginBottom: 8 }]}>Vehicle</Text>
            <Text style={[FONT.h3, { fontSize: 16 }]}>{booking.vehicle_make} {booking.vehicle_model}</Text>
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <Text style={[FONT.cap, { marginBottom: 8 }]}>Customer</Text>
            <Text style={[FONT.body, { fontWeight: '600', color: C.charcoal }]}>{booking.customer_name}</Text>
            <Text style={FONT.body}>{booking.customer_phone}</Text>
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <Text style={[FONT.cap, { marginBottom: 8 }]}>Dates</Text>
            <View style={styles.row}>
              <Text style={FONT.body}>Pickup</Text>
              <Text style={[FONT.body, { fontWeight: '600' }]}>{new Date(booking.pickup_time).toLocaleString()}</Text>
            </View>
            <View style={styles.row}>
              <Text style={FONT.body}>Drop-off</Text>
              <Text style={[FONT.body, { fontWeight: '600' }]}>{new Date(booking.dropoff_time).toLocaleString()}</Text>
            </View>
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <Text style={[FONT.cap, { marginBottom: 8 }]}>Earnings</Text>
            <View style={styles.row}>
              <Text style={FONT.body}>Total Amount</Text>
              <Text style={[FONT.body, { fontWeight: '600' }]}>{fmtMoney(booking.total_amount)}</Text>
            </View>
            <View style={styles.row}>
              <Text style={FONT.body}>Your Earnings</Text>
              <Text style={[FONT.h3, { color: C.green }]}>{fmtMoney(booking.owner_earnings)}</Text>
            </View>
            <View style={styles.row}>
              <Text style={FONT.body}>Platform Fee (20%)</Text>
              <Text style={FONT.body}>{fmtMoney(booking.total_amount - booking.owner_earnings)}</Text>
            </View>
          </Card>

          {booking.status === 'pending' && (
            <Button label="Accept Booking" onPress={handleAccept} style={{ marginBottom: 32 }} />
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingVertical: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border },
});

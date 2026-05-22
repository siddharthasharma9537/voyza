import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, SafeAreaView, FlatList, ActivityIndicator, Alert, RefreshControl, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList, OwnerVehicle } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { StatusBadge } from '../components/StatusBadge';
import { Button } from '../components/Button';
import { fmtMoney } from './DashboardScreen';

type Nav = StackNavigationProp<OwnerNavigationParamList, 'Cars'>;

export const CarsScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const [cars, setCars] = useState<OwnerVehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchCars = async () => {
    try {
      const res: any = await api.owner.cars();
      setCars(res || []);
    } catch (e: any) { Alert.alert('Error', e.message); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => { setLoading(true); fetchCars(); }, []));

  const handleDelete = (id: string) => {
    Alert.alert('Delete Car?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          try { await api.owner.deleteCar(id); fetchCars(); }
          catch (e: any) { Alert.alert('Error', e.message); }
        }
      },
    ]);
  };

  const handleSubmit = async (id: string) => {
    try {
      await api.owner.submitCar(id);
      Alert.alert('Submitted', 'Your car is now under review. Approval takes 24-48 hours.');
      fetchCars();
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
      <FlatList
        data={cars}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16, gap: 12, paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchCars(); }} tintColor={C.orange} />}
        ListEmptyComponent={
          <View style={{ alignItems: 'center', justifyContent: 'center', marginTop: 80 }}>
            <Text style={{ fontSize: 48, marginBottom: 12 }}>🚗</Text>
            <Text style={FONT.h3}>No cars listed</Text>
            <Text style={[FONT.body, { marginTop: 4, marginBottom: 24 }]}>Add your first car to start earning</Text>
            <Button label="Add Car" onPress={() => navigation.navigate('AddCar')} />
          </View>
        }
        ListHeaderComponent={
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Text style={FONT.h2}>My Cars ({cars.length})</Text>
            <TouchableOpacity onPress={() => navigation.navigate('AddCar')} style={{ backgroundColor: C.charcoal, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8 }}>
              <Text style={{ color: C.white, fontWeight: '700', fontSize: 13 }}>+ Add</Text>
            </TouchableOpacity>
          </View>
        }
        renderItem={({ item: car }) => (
          <Card>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <View style={{ flex: 1 }}>
                <Text style={[FONT.h3, { fontSize: 16 }]}>{car.make} {car.model} {car.year}</Text>
                <Text style={[FONT.body, { fontSize: 12, marginTop: 2 }]}>{car.registration_number} · {car.city}</Text>
                <Text style={{ fontSize: 16, fontWeight: '700', color: C.charcoal, marginTop: 6 }}>{fmtMoney(car.price_per_day)}/day</Text>
              </View>
              <View style={{ alignItems: 'flex-end', gap: 4 }}>
                <StatusBadge status={car.status} />
                <StatusBadge status={car.kyc_status} />
              </View>
            </View>
            <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
              <TouchableOpacity style={[styles.action, { backgroundColor: C.cream2 }]} onPress={() => navigation.navigate('CarDetail', { car })}>
                <Text style={{ fontSize: 12, fontWeight: '600', color: C.charcoal }}>Details</Text>
              </TouchableOpacity>
              {car.status === 'draft' && (
                <TouchableOpacity style={[styles.action, { backgroundColor: C.charcoal }]} onPress={() => handleSubmit(car.id)}>
                  <Text style={{ fontSize: 12, fontWeight: '600', color: C.white }}>Submit</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity style={[styles.action, { backgroundColor: '#FEF2F2' }]} onPress={() => handleDelete(car.id)}>
                <Text style={{ fontSize: 12, fontWeight: '600', color: C.red }}>Delete</Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  action: { flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center' },
});

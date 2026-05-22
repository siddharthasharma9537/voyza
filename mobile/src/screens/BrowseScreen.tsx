import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, SafeAreaView, FlatList, ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList, Vehicle } from '../types';
import { C } from '../constants/theme';
import { api } from '../api/client';
import { Tag } from '../components/Tag';
import { CarCard } from '../components/CarCard';

type BrowseNav = StackNavigationProp<NavigationParamList, 'Browse'>;
type BrowseRoute = RouteProp<NavigationParamList, 'Browse'>;

export const BrowseScreen: React.FC = () => {
  const navigation = useNavigation<BrowseNav>();
  const route = useRoute<BrowseRoute>();
  const [cars, setCars] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [filters, setFilters] = useState({
    city: route.params?.city || null,
    fuel_type: null as string | null,
    transmission: null as string | null,
    sort_by: 'price_asc',
  });

  const fetchCars = useCallback(async (pg = 1, reset = false) => {
    try {
      const q: Record<string, string | number | undefined> = {
        page: pg,
        limit: 20,
        sort_by: filters.sort_by,
      };
      if (filters.city) q.city = filters.city;
      if (filters.fuel_type) q.fuel_type = filters.fuel_type;
      if (filters.transmission) q.transmission = filters.transmission;
      const res: any = await api.cars.browse(q);
      const items = res.items || [];
      setCars((prev) => (reset ? items : [...prev, ...items]));
      setHasMore(pg < (res.total_pages || 1));
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters]);

  useEffect(() => { setLoading(true); setPage(1); fetchCars(1, true); }, [filters]);

  const onRefresh = () => { setRefreshing(true); setPage(1); fetchCars(1, true); };
  const onEndReached = () => {
    if (hasMore && !loading) {
      const next = page + 1;
      setPage(next);
      fetchCars(next);
    }
  };

  const fuelTypes = ['petrol', 'diesel', 'electric', 'hybrid', 'cng'];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <View style={{ backgroundColor: C.white, borderBottomWidth: 1, borderBottomColor: C.border }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 10, gap: 8 }}>
          {fuelTypes.map((f) => (
            <Tag
              key={f}
              label={f}
              active={filters.fuel_type === f}
              onPress={() => setFilters((p) => ({ ...p, fuel_type: p.fuel_type === f ? null : f }))}
            />
          ))}
          <Tag
            label="Auto"
            active={filters.transmission === 'automatic'}
            onPress={() => setFilters((p) => ({ ...p, transmission: p.transmission === 'automatic' ? null : 'automatic' }))}
          />
          <Tag
            label="Manual"
            active={filters.transmission === 'manual'}
            onPress={() => setFilters((p) => ({ ...p, transmission: p.transmission === 'manual' ? null : 'manual' }))}
          />
        </ScrollView>
      </View>

      <FlatList
        data={cars}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.orange} />}
        onEndReached={onEndReached}
        onEndReachedThreshold={0.3}
        ListEmptyComponent={
          !loading ? (
            <View style={{ alignItems: 'center', justifyContent: 'center', marginTop: 80 }}>
              <Text style={{ fontSize: 14, color: C.mid }}>No cars found</Text>
            </View>
          ) : null
        }
        ListFooterComponent={loading ? <ActivityIndicator color={C.orange} style={{ marginVertical: 16 }} /> : null}
        renderItem={({ item }) => (
          <CarCard car={item} onPress={() => navigation.navigate('CarDetail', { car: item })} />
        )}
      />
    </SafeAreaView>
  );
};

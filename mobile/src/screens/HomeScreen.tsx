import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, SafeAreaView, FlatList, ActivityIndicator, StyleSheet,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList, Vehicle } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Button } from '../components/Button';
import { Tag } from '../components/Tag';
import { Card } from '../components/Card';
import { CarCard } from '../components/CarCard';

type HomeNav = BottomTabNavigationProp<NavigationParamList> & StackNavigationProp<NavigationParamList>;

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<HomeNav>();
  const [city, setCity] = useState('Hyderabad');
  const [featured, setFeatured] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.cars.browse({ city, limit: 6, sort_by: 'rating' })
      .then((res: any) => setFeatured(res.items || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [city]);

  const cities = ['Hyderabad', 'Bangalore', 'Chennai', 'Mumbai', 'Pune'];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={[styles.container, { paddingTop: 24, paddingBottom: 8 }]}>
          <Text style={[FONT.cap, { marginBottom: 4 }]}>Good morning 👋</Text>
          <Text style={FONT.h2}>Find your perfect car</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 16, marginHorizontal: -20 }} contentContainerStyle={{ paddingHorizontal: 20, gap: 8 }}>
            {cities.map((c) => <Tag key={c} label={c} active={c === city} onPress={() => setCity(c)} />)}
          </ScrollView>
        </View>

        <View style={[styles.container, { paddingTop: 0 }]}>
          <Card style={{ marginBottom: 24 }}>
            <Text style={[FONT.h3, { marginBottom: 16 }]}>Quick Search</Text>
            <Button label={`Browse All Cars in ${city}`} onPress={() => navigation.navigate('Browse', { city })} />
          </Card>
          <Text style={[FONT.h3, { marginBottom: 16 }]}>Top Rated in {city}</Text>
        </View>

        {loading ? (
          <ActivityIndicator color={C.orange} style={{ marginTop: 20 }} />
        ) : (
          <FlatList
            data={featured}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 20, gap: 12 }}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <CarCard
                car={item}
                onPress={() => navigation.navigate('CarDetail', { car: item })}
                compact
              />
            )}
          />
        )}

        <View style={[styles.container, { marginTop: 32, marginBottom: 24 }]}>
          <Card>
            <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
              {[['8,400+', 'Cars'], ['52', 'Cities'], ['4.8★', 'Rating']].map(([val, label]) => (
                <View key={label} style={{ alignItems: 'center' }}>
                  <Text style={[FONT.h2, { color: C.orange }]}>{val}</Text>
                  <Text style={FONT.cap}>{label}</Text>
                </View>
              ))}
            </View>
          </Card>
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
});

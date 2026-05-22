import React, { useState, useEffect } from 'react';
import { View, Text, SafeAreaView, ScrollView, Alert, StyleSheet, TouchableOpacity } from 'react-native';
import { useRoute, RouteProp } from '@react-navigation/native';
import { OwnerNavigationParamList } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Input } from '../components/Input';

type RouteType = RouteProp<OwnerNavigationParamList, 'Availability'>;

export const AvailabilityScreen: React.FC = () => {
  const route = useRoute<RouteType>();
  const { carId } = route.params;
  const [slots, setSlots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [reason, setReason] = useState('blocked');
  const [saving, setSaving] = useState(false);

  const fetchSlots = async () => {
    try {
      const res: any = await api.owner.availability(carId);
      setSlots(res || []);
    } catch (e: any) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchSlots(); }, [carId]);

  const block = async () => {
    if (!start || !end) { Alert.alert('Missing dates'); return; }
    setSaving(true);
    try {
      await api.owner.blockSlot({ vehicle_id: carId, start_time: start, end_time: end, reason });
      Alert.alert('Blocked', 'Time slot blocked successfully');
      fetchSlots();
    } catch (e: any) { Alert.alert('Error', e.message); }
    finally { setSaving(false); }
  };

  const unblock = async (id: string) => {
    try { await api.owner.unblockSlot(id); fetchSlots(); }
    catch (e: any) { Alert.alert('Error', e.message); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[FONT.h2, { marginBottom: 20 }]}>Availability</Text>

          <Text style={[FONT.cap, { marginBottom: 12 }]}>Block a Slot</Text>
          <Input label="Start Time (ISO)" value={start} onChangeText={setStart} placeholder="2026-05-01T10:00:00Z" />
          <Input label="End Time (ISO)" value={end} onChangeText={setEnd} placeholder="2026-05-03T10:00:00Z" />
          <Button label="Block Slot" onPress={block} loading={saving} style={{ marginBottom: 24 }} />

          <Text style={[FONT.cap, { marginBottom: 12 }]}>Blocked Slots</Text>
          {slots.length === 0 ? (
            <Card><Text style={[FONT.body, { textAlign: 'center' }]}>No blocked slots</Text></Card>
          ) : (
            slots.map((s) => (
              <Card key={s.id} style={{ marginBottom: 10 }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <View>
                    <Text style={[FONT.body, { fontWeight: '600' }]}>{new Date(s.start_time).toLocaleDateString()} → {new Date(s.end_time).toLocaleDateString()}</Text>
                    <Text style={[FONT.mono, { marginTop: 2 }]}>{s.reason}</Text>
                  </View>
                  <TouchableOpacity onPress={() => unblock(s.id)} style={{ backgroundColor: '#FEF2F2', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6 }}>
                    <Text style={{ color: C.red, fontSize: 12, fontWeight: '700' }}>Remove</Text>
                  </TouchableOpacity>
                </View>
              </Card>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({ container: { paddingHorizontal: 20, paddingVertical: 16 } });

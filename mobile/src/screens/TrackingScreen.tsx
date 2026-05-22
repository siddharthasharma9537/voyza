import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, SafeAreaView, StyleSheet,
} from 'react-native';
import { useRoute, RouteProp } from '@react-navigation/native';
import { NavigationParamList } from '../types';
import { C, FONT } from '../constants/theme';
import { storage } from '../utils/storage';
import { Card } from '../components/Card';

const BASE_URL = 'http://localhost:8000';

type TrackRoute = RouteProp<NavigationParamList, 'Tracking'>;
export const TrackingScreen: React.FC = () => {
  const route = useRoute<TrackRoute>();
  const { booking } = route.params;
  const [position, setPosition] = useState<{ lat: number; lng: number; speed_kmph?: number } | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWS = async () => {
      const token = await storage.getAccessToken();
      const ws = new WebSocket(`${BASE_URL}/ws/track/${booking.id}?token=${token}`);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === 'gps') setPosition(msg);
      };
    };
    connectWS();
    return () => wsRef.current?.close();
  }, [booking.id]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <View style={styles.container}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: connected ? C.green : C.muted }} />
          <Text style={FONT.mono}>
            {connected ? 'Connected — live tracking active' : 'Connecting...'}
          </Text>
        </View>

        <View style={styles.mapPlaceholder}>
          <Text style={{ fontSize: 48, marginBottom: 8 }}>🗺️</Text>
          <Text style={FONT.body}>Live GPS Map</Text>
          <Text style={[FONT.mono, { marginTop: 4 }]}>Integration: react-native-maps</Text>
        </View>

        {position && (
          <Card>
            <Text style={[FONT.cap, { marginBottom: 12 }]}>Vehicle Position</Text>
            <View style={styles.specRow}>
              <Text style={FONT.body}>Latitude</Text>
              <Text style={FONT.mono}>{position.lat.toFixed(5)}</Text>
            </View>
            <View style={styles.specRow}>
              <Text style={FONT.body}>Longitude</Text>
              <Text style={FONT.mono}>{position.lng.toFixed(5)}</Text>
            </View>
            <View style={styles.specRow}>
              <Text style={FONT.body}>Speed</Text>
              <Text style={[FONT.body, { fontWeight: '600' }]}>{position.speed_kmph || 0} km/h</Text>
            </View>
          </Card>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  mapPlaceholder: {
    height: 300,
    backgroundColor: C.cream2,
    borderRadius: 12,
    marginBottom: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: C.border,
  },
  specRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
});

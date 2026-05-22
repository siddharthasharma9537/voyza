import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, SafeAreaView, ActivityIndicator, Alert, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList, User } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { storage } from '../utils/storage';
import { Button } from '../components/Button';

type Nav = BottomTabNavigationProp<OwnerNavigationParamList> & StackNavigationProp<OwnerNavigationParamList>;

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.auth.me().then((u: any) => setUser(u)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const logout = async () => {
    await api.auth.logout().catch(() => {});
    await storage.clearTokens();
    navigation.replace('Login');
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
          <View style={{ alignItems: 'center', marginBottom: 32 }}>
            <View style={styles.avatar}>
              <Text style={{ fontSize: 32, fontWeight: '800', color: C.white }}>{user?.full_name?.[0] || 'U'}</Text>
            </View>
            <Text style={[FONT.h2, { marginTop: 16 }]}>{user?.full_name}</Text>
            <Text style={FONT.body}>{user?.phone}</Text>
            <View style={styles.roleChip}>
              <Text style={{ color: C.white, fontSize: 11, fontWeight: '700' }}>{user?.role?.toUpperCase()}</Text>
            </View>
          </View>

          {[
            { label: 'My Cars', icon: '🚗', screen: 'Cars' as const },
            { label: 'KYC Verification', icon: '🪪', screen: 'KycStatus' as const },
            { label: 'Upload Documents', icon: '📤', screen: 'KycUpload' as const },
          ].map((item) => (
            <TouchableOpacity key={item.label} style={styles.row} onPress={() => navigation.navigate(item.screen)}>
              <Text style={{ fontSize: 20 }}>{item.icon}</Text>
              <Text style={[FONT.h3, { flex: 1 }]}>{item.label}</Text>
              <Text style={{ color: C.muted }}>›</Text>
            </TouchableOpacity>
          ))}

          <Button label="Sign Out" onPress={logout} variant="danger" style={{ marginTop: 32 }} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingVertical: 16 },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: C.charcoal, alignItems: 'center', justifyContent: 'center' },
  roleChip: { backgroundColor: C.orange, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6, marginTop: 8 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 16, backgroundColor: C.white, borderRadius: 12, marginBottom: 10, borderWidth: 1, borderColor: C.border },
});

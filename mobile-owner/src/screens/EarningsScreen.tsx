import React, { useState, useEffect } from 'react';
import { View, Text, SafeAreaView, ScrollView, ActivityIndicator, RefreshControl, StyleSheet } from 'react-native';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { StatCard } from '../components/StatCard';
import { fmtMoney } from './DashboardScreen';
import { MonthlyEarning, EarningsSummary } from '../types';

export const EarningsScreen: React.FC = () => {
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [monthly, setMonthly] = useState<MonthlyEarning[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [s, m]: [any, any] = await Promise.all([
        api.owner.earnings(),
        api.owner.earningsMonthly(6),
      ]);
      setSummary(s);
      setMonthly(m || []);
    } catch (e: any) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useEffect(() => { fetchData(); }, []);

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
      <ScrollView refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchData(); }} tintColor={C.orange} />}>
        <View style={styles.container}>
          <Text style={[FONT.h2, { marginBottom: 20 }]}>Earnings</Text>

          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 8 }}>
            <StatCard label="Total" value={fmtMoney(summary?.total_earnings || 0)} icon="💰" />
            <StatCard label="This Month" value={fmtMoney(summary?.this_month || 0)} icon="📅" accent={C.green} />
          </View>
          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 24 }}>
            <StatCard label="Pending" value={fmtMoney(summary?.pending_payout || 0)} icon="⏳" accent="#C2410C" />
            <StatCard label="Bookings" value={String(summary?.completed_bookings || 0)} icon="📋" accent="#1D4ED8" />
          </View>

          <Text style={[FONT.cap, { marginBottom: 12 }]}>Monthly Breakdown</Text>
          {monthly.length === 0 ? (
            <Card><Text style={[FONT.body, { textAlign: 'center' }]}>No earnings data yet</Text></Card>
          ) : (
            monthly.map((m) => (
              <Card key={m.month} style={{ marginBottom: 10 }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <View>
                    <Text style={[FONT.h3, { fontSize: 15 }]}>{m.month}</Text>
                    <Text style={[FONT.body, { fontSize: 12 }]}>{m.bookings} booking{m.bookings !== 1 ? 's' : ''}</Text>
                  </View>
                  <Text style={{ fontSize: 16, fontWeight: '700', color: C.charcoal }}>{fmtMoney(m.amount)}</Text>
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

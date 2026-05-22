import React, { useState, useEffect } from 'react';
import { View, Text, SafeAreaView, ScrollView, ActivityIndicator, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { OwnerNavigationParamList, KycDocument, DocumentStatus } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';

const OWNER_REQUIRED: string[] = ['vehicle_rc', 'vehicle_insurance'];

const DOC_LABELS: Record<string, string> = {
  vehicle_rc: 'Vehicle RC',
  vehicle_insurance: 'Vehicle Insurance',
  driving_license: 'Driving License',
  aadhar: 'Aadhar ID',
  selfie: 'Selfie Verification',
};

const STATUS_COLORS: Record<DocumentStatus, string> = {
  pending: '#C2410C',
  verified: '#16A34A',
  rejected: '#DC2626',
  expired: '#6B7280',
  requires_resubmission: '#92400E',
};

const STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: 'Pending',
  verified: 'Verified',
  rejected: 'Rejected',
  expired: 'Expired',
  requires_resubmission: 'Resubmit',
};

type Nav = StackNavigationProp<OwnerNavigationParamList, 'KycStatus'>;

export const KycStatusScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const [docs, setDocs] = useState<KycDocument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.kyc.documents().then((d: any) => setDocs(d || [])).catch(console.error).finally(() => setLoading(false));
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

  const docMap = new Map(docs.map((d): [string, KycDocument] => [d.type, d]));
  const allVerified = OWNER_REQUIRED.every((t) => docMap.get(t)?.status === 'verified');

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[FONT.h2, { marginBottom: 8 }]}>KYC Verification</Text>
          <Text style={[FONT.body, { marginBottom: 24 }]}>
            {allVerified ? 'All documents verified ✅' : 'Submit vehicle documents to list cars'}
          </Text>

          <Card style={{ marginBottom: 20, backgroundColor: allVerified ? '#F0FDF4' : '#FFF7ED' }}>
            <Text style={[FONT.h3, { marginBottom: 4, color: allVerified ? C.green : C.orange }]}>
              {allVerified ? 'Verified' : 'Pending'}
            </Text>
            <Text style={FONT.body}>
              {allVerified
                ? 'Your documents are verified. You can submit cars for listing.'
                : 'Upload RC and Insurance documents to get your cars approved.'}
            </Text>
          </Card>

          <Text style={[FONT.cap, { marginBottom: 12 }]}>Required Documents</Text>
          {OWNER_REQUIRED.map((type) => {
            const doc = docMap.get(type);
            return (
              <Card key={type} style={{ marginBottom: 10, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                <View style={{ width: 32, height: 32, borderRadius: 16, backgroundColor: doc?.status === 'verified' ? '#DCFCE7' : '#FEF2F2', alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ fontSize: 16 }}>{doc?.status === 'verified' ? '✓' : '!'}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[FONT.h3, { fontSize: 15 }]}>{DOC_LABELS[type]}</Text>
                  <Text style={{ fontSize: 12, color: doc ? STATUS_COLORS[doc.status] : C.muted }}>
                    {doc ? STATUS_LABELS[doc.status] : 'Not uploaded'}
                  </Text>
                </View>
              </Card>
            );
          })}

          {!allVerified && (
            <Button label="Upload Documents" onPress={() => navigation.navigate('KycUpload')} style={{ marginTop: 12 }} />
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({ container: { paddingHorizontal: 20, paddingVertical: 16 } });

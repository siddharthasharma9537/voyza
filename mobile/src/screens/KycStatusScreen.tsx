import React, { useState, useEffect } from 'react';
import {
  View, Text, SafeAreaView, ScrollView, ActivityIndicator, StyleSheet,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { NavigationParamList, KycStatus as KycStatusType, DocumentStatus, DocumentType } from '../types';
import { C, FONT } from '../constants/theme';
import { api } from '../api/client';
import { Card } from '../components/Card';
import { Button } from '../components/Button';

export const REQUIRED_DOCS: DocumentType[] = ['driving_license', 'aadhar', 'selfie'];

export const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  driving_license: 'Driving License',
  aadhar: 'Aadhar ID',
  selfie: 'Selfie Verification',
  vehicle_rc: 'Vehicle RC',
  vehicle_insurance: 'Vehicle Insurance',
};

const DOC_STATUS_COLORS: Record<DocumentStatus, string> = {
  pending: '#C2410C',
  verified: '#16A34A',
  rejected: '#DC2626',
  expired: '#6B7280',
  requires_resubmission: '#92400E',
};

const DOC_STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: 'Pending',
  verified: 'Verified',
  rejected: 'Rejected',
  expired: 'Expired',
  requires_resubmission: 'Resubmit',
};

type KycNav = StackNavigationProp<NavigationParamList, 'KycStatus'>;

export const KycStatusScreen: React.FC = () => {
  const navigation = useNavigation<KycNav>();
  const [status, setStatus] = useState<KycStatusType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.kyc.status()
      .then((s: any) => setStatus(s))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={C.orange} />
      </View>
    );
  }

  const docMap = new Map((status?.documents || []).map((d) => [d.type, d]));

  const overall = status?.is_fully_verified;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: C.cream }}>
      <ScrollView>
        <View style={styles.container}>
          <Text style={[FONT.h2, { marginBottom: 8 }]}>KYC Verification</Text>
          <Text style={[FONT.body, { marginBottom: 24 }]}>
            {overall
              ? 'All documents verified ✅'
              : 'Complete verification to unlock full booking privileges'}
          </Text>

          <Card style={{ marginBottom: 20, backgroundColor: overall ? '#F0FDF4' : '#FFF7ED' }}>
            <Text style={[FONT.h3, { marginBottom: 4, color: overall ? C.green : C.orange }]}>
              {overall ? 'Verified' : 'Pending'}
            </Text>
            <Text style={FONT.body}>
              {overall
                ? 'Your identity has been verified. You can now book any car.'
                : 'Submit your KYC documents to get verified.'}
            </Text>
          </Card>

          <Text style={[FONT.cap, { marginBottom: 12 }]}>Required Documents</Text>
          {REQUIRED_DOCS.map((type) => {
            const doc = docMap.get(type);
            return (
              <Card key={String(type)} style={{ marginBottom: 10, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                <View style={{ width: 32, height: 32, borderRadius: 16, backgroundColor: doc?.status === 'verified' ? '#DCFCE7' : '#FEF2F2', alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ fontSize: 16 }}>{doc?.status === 'verified' ? '✓' : '!'}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[FONT.h3, { fontSize: 15 }]}>{DOCUMENT_TYPE_LABELS[String(type)]}</Text>
                  <Text style={{ fontSize: 12, color: doc ? DOC_STATUS_COLORS[doc.status] : C.muted }}>
                    {doc ? DOC_STATUS_LABELS[doc.status] : 'Not uploaded'}
                  </Text>
                </View>
              </Card>
            );
          })}

          {!overall && (
            <Button
              label="Upload Documents"
              onPress={() => navigation.navigate('KycUpload')}
              style={{ marginTop: 12 }}
            />
          )}
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

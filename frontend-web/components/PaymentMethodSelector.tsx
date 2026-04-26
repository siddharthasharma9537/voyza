"use client";

import { useState } from "react";

export type PaymentMethod = "card" | "upi" | "wallet" | "netbanking";

interface PaymentMethodSelectorProps {
  selected: PaymentMethod;
  onSelect: (method: PaymentMethod) => void;
  amount: number;
  disabled?: boolean;
}

export function PaymentMethodSelector({
  selected,
  onSelect,
  amount,
  disabled = false,
}: PaymentMethodSelectorProps) {
  const [showCardDetails, setShowCardDetails] = useState(false);
  const [showUPIDetails, setShowUPIDetails] = useState(false);

  const amountInRupees = (paise: number) => (paise / 100).toFixed(2);

  const methods = [
    {
      id: "card" as PaymentMethod,
      name: "Credit / Debit Card",
      icon: "💳",
      description: "Visa, Mastercard, RuPay",
      processingTime: "Instant",
      color: "bg-blue-50 border-blue-200",
    },
    {
      id: "upi" as PaymentMethod,
      name: "UPI",
      icon: "📱",
      description: "Google Pay, PhonePe, PayTM",
      processingTime: "Instant",
      color: "bg-purple-50 border-purple-200",
    },
    {
      id: "wallet" as PaymentMethod,
      name: "Digital Wallet",
      icon: "👛",
      description: "PayTM, AmazonPay, MobiKwik",
      processingTime: "Instant",
      color: "bg-green-50 border-green-200",
    },
    {
      id: "netbanking" as PaymentMethod,
      name: "Net Banking",
      icon: "🏦",
      description: "All major banks",
      processingTime: "Instant",
      color: "bg-orange-50 border-orange-200",
    },
  ];

  return (
    <div className="w-full">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-slate-900 mb-4">💳 Choose Payment Method</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {methods.map((method) => (
            <button
              key={method.id}
              onClick={() => onSelect(method.id)}
              disabled={disabled}
              className={`p-4 rounded-lg border-2 transition-all text-left ${
                selected === method.id
                  ? `${method.color} border-current shadow-md`
                  : "bg-white border-slate-200 hover:border-slate-300"
              } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{method.icon}</span>
                <div className="flex-1">
                  <p className="font-bold text-slate-900">{method.name}</p>
                  <p className="text-sm text-slate-600 mb-2">{method.description}</p>
                  <p className="text-xs text-slate-500">{method.processingTime}</p>
                </div>
                {selected === method.id && (
                  <div className="text-lg">✓</div>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Card Payment Details */}
      {selected === "card" && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-6">
          <h4 className="font-bold text-slate-900 mb-4">💳 Card Details</h4>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Full Name on Card
              </label>
              <input
                type="text"
                placeholder="John Doe"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Card Number
              </label>
              <input
                type="text"
                placeholder="4532 1234 5678 9010"
                maxLength={19}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Expiry (MM/YY)
                </label>
                <input
                  type="text"
                  placeholder="12/25"
                  maxLength={5}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  CVV
                </label>
                <input
                  type="text"
                  placeholder="123"
                  maxLength={4}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="bg-white border border-blue-100 rounded-lg p-3">
              <p className="text-sm text-blue-900">
                <strong>🔒 Secure:</strong> Your card details are encrypted and secure
              </p>
            </div>
          </div>
        </div>
      )}

      {/* UPI Payment Details */}
      {selected === "upi" && (
        <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-6 mb-6">
          <h4 className="font-bold text-slate-900 mb-4">📱 UPI Payment</h4>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Enter Your UPI ID
              </label>
              <input
                type="text"
                placeholder="yourname@okhdfcbank"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <p className="text-xs text-slate-600 mt-1">
                You'll receive a prompt on your registered phone number
              </p>
            </div>

            <div className="bg-white border border-purple-100 rounded-lg p-3">
              <p className="text-sm text-purple-900">
                <strong>💡 Tip:</strong> Select your UPI app below or enter your UPI ID
              </p>
            </div>

            <div className="grid grid-cols-4 gap-2">
              {["Google Pay", "PhonePe", "PayTM", "WhatsApp Pay"].map((app) => (
                <button
                  key={app}
                  className="p-3 border border-slate-300 rounded-lg hover:bg-white transition-colors text-center text-sm"
                >
                  {app}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Wallet Payment */}
      {selected === "wallet" && (
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 mb-6">
          <h4 className="font-bold text-slate-900 mb-4">👛 Digital Wallet</h4>

          <div className="space-y-3">
            {["PayTM", "Amazon Pay", "MobiKwik", "Freecharge"].map((wallet) => (
              <button
                key={wallet}
                className="w-full p-4 border border-green-300 rounded-lg hover:bg-white transition-colors text-left font-medium"
              >
                {wallet}
              </button>
            ))}
          </div>

          <div className="bg-white border border-green-100 rounded-lg p-3 mt-4">
            <p className="text-sm text-green-900">
              <strong>🎁 Bonus:</strong> Get extra cashback with wallet payments!
            </p>
          </div>
        </div>
      )}

      {/* Net Banking */}
      {selected === "netbanking" && (
        <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-6 mb-6">
          <h4 className="font-bold text-slate-900 mb-4">🏦 Net Banking</h4>

          <label className="block text-sm font-semibold text-slate-700 mb-3">
            Select Your Bank
          </label>

          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
            {[
              "HDFC Bank",
              "ICICI Bank",
              "SBI",
              "Axis Bank",
              "IndusInd Bank",
              "Kotak Mahindra",
              "IDBI Bank",
              "Bank of India",
              "PNB",
              "Union Bank",
            ].map((bank) => (
              <button
                key={bank}
                className="p-3 border border-orange-300 rounded-lg hover:bg-white transition-colors text-center text-sm"
              >
                {bank}
              </button>
            ))}
          </div>

          <div className="bg-white border border-orange-100 rounded-lg p-3 mt-4">
            <p className="text-sm text-orange-900">
              <strong>🔒 Secure:</strong> You'll be redirected to your bank's secure page
            </p>
          </div>
        </div>
      )}

      {/* Payment Summary */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
        <div className="flex justify-between items-center">
          <span className="font-semibold text-slate-900">Amount to Pay</span>
          <span className="text-2xl font-bold text-sky-600">₹{amountInRupees(amount)}</span>
        </div>
        <p className="text-xs text-slate-600 mt-2">
          ✓ Secure payment | ✓ 3D Secure | ✓ SSL Encrypted
        </p>
      </div>
    </div>
  );
}

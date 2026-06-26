"use client";
import KitchenMonitor from "@/components/KitchenMonitor";
export default function KitchenPage({ params }) {
  return <KitchenMonitor tenantId={params.tenantId} />;
}
